import struct
from contextlib import closing, contextmanager
from fractions import Fraction

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

MAX_PIXELS = 40_000_000


def configure_codecs():
    register_heif_opener(thumbnails=False, depth_images=False, aux_images=False)


class InvalidImage(ValueError):
    pass


class UnsupportedImage(InvalidImage):
    pass


class ImageTooLarge(InvalidImage):
    pass


def check_pixels(image):
    if image.width * image.height > MAX_PIXELS:
        raise ImageTooLarge("Image exceeds 40,000,000 pixels.")


@contextmanager
def decode_image(source):
    try:
        with closing(Image.open(source)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP", "HEIF"}:
                raise UnsupportedImage("Choose a JPEG, PNG, WebP or HEIC image.")
            check_pixels(image)
            if image.format == "HEIF":
                position = source.tell()
                source.seek(0)
                try:
                    animated = heif_is_animated(source.read(20_000_001))
                finally:
                    source.seek(position)
                if animated:
                    raise InvalidImage("Animated images are not supported.")
            if image.format != "HEIF" and getattr(image, "is_animated", False):
                raise InvalidImage("Animated images are not supported.")
            image.load()
            check_pixels(image)
            ImageOps.exif_transpose(image, in_place=True)
            yield image
    except Image.DecompressionBombError:
        raise ImageTooLarge("Image exceeds 40,000,000 pixels.") from None
    except UnidentifiedImageError, OSError, SyntaxError:
        raise InvalidImage("Image is empty or corrupted.") from None


def boxes(data):
    data = memoryview(data)
    position = 0
    while position < len(data):
        if len(data) - position < 8:
            raise InvalidImage("Truncated HEIF box.")
        size, kind = struct.unpack_from(">I4s", data, position)
        header = 8
        if size == 1:
            if len(data) - position < 16:
                raise InvalidImage("Truncated HEIF box.")
            size = struct.unpack_from(">Q", data, position + 8)[0]
            header = 16
        elif size == 0:
            size = len(data) - position
        if kind == b"uuid":
            header += 16
        if size < header or size > len(data) - position:
            raise InvalidImage("Invalid HEIF box extent.")
        yield kind, data[position + header : position + size]
        position += size


def one_box(data, kind, required=True):
    found = None
    for name, payload in boxes(data):
        if name == kind:
            if found is not None:
                raise InvalidImage("Duplicate HEIF box.")
            found = payload
    if required and found is None:
        raise InvalidImage("Missing HEIF box.")
    return found


def clock_scale(header):
    offset = 20 if header[0] == 1 else 12
    if header[0] not in (0, 1) or len(header) < offset + 4:
        raise InvalidImage("Invalid HEIF clock.")
    value = int.from_bytes(header[offset : offset + 4])
    if not value:
        raise InvalidImage("Invalid HEIF clock.")
    return value


def table_entries(data, formats):
    if len(data) < 8 or data[0] not in formats:
        raise InvalidImage("Invalid HEIF timing table.")
    format = formats[data[0]]
    count = int.from_bytes(data[4:8])
    if len(data) != 8 + count * struct.calcsize(format):
        raise InvalidImage("Invalid HEIF timing entries.")
    return list(struct.iter_unpack(format, data[8:]))


def timing_runs(table):
    durations = table_entries(one_box(table, b"stts"), {0: ">II"})
    composition = one_box(table, b"ctts", False)
    offsets = (
        table_entries(composition, {0: ">II", 1: ">Ii"})
        if composition is not None
        else [(sum(count for count, _ in durations), 0)]
    )
    if sum(count for count, _ in durations) != sum(count for count, _ in offsets):
        raise InvalidImage("Inconsistent HEIF sample counts.")
    runs = []
    index = 0
    remaining, offset = offsets[0] if offsets else (0, 0)
    decode_time = 0
    for count, duration in durations:
        if not count:
            raise InvalidImage("Invalid HEIF timing run.")
        while count:
            while not remaining:
                index += 1
                remaining, offset = offsets[index]
            take = min(count, remaining)
            if offset != -(2**31):
                runs.append((decode_time + offset, duration, take))
            decode_time += duration * take
            count -= take
            remaining -= take
    return runs, decode_time


def presentation_times(runs, start=None, end=None):
    points = set()
    previous = None
    last_end = max(
        (first + step * (count - 1) for first, step, count in runs), default=0
    )
    if runs:
        last_end += runs[-1][1]
    for first, step, count in runs:
        if not count:
            continue
        last = first + step * (count - 1)
        if start is None:
            index = 0
        elif step:
            index = max(0, (start - first) // step + 1)
        else:
            index = 0 if first > start else count
        if start is not None and first <= start:
            candidate = (
                min(last, first + ((start - first) // step) * step) if step else first
            )
            previous = candidate if previous is None else max(previous, candidate)
        for i in (index, index + 1):
            if i < count:
                point = first + step * i
                if end is None or point < end:
                    points.add(point)
        if len(points) > 1:
            return points
    if start is not None and previous is not None and start < last_end:
        points.add(start)
    return points


def track_is_animated(track, runs, movie_scale, media_scale):
    edits = one_box(track, b"edts", False)
    if edits is None:
        return len(presentation_times(runs)) > 1
    edit = one_box(edits, b"elst")
    entries = table_entries(edit, {0: ">Iihh", 1: ">Qqhh"})
    presented = set()
    movie_time = Fraction(0)
    for duration, start, rate_integer, rate_fraction in entries:
        span = Fraction(duration * media_scale, movie_scale)
        rate = Fraction(rate_integer * 65536 + (rate_fraction & 65535), 65536)
        if start < -1:
            raise InvalidImage("Invalid HEIF edit time.")
        if start != -1:
            if rate == 0:
                if presentation_times(runs, start, start + 1):
                    presented.add(movie_time)
            else:
                lower = start if rate > 0 else start - span * abs(rate)
                upper = start + span * rate if rate > 0 else start
                if rate < 0 and not duration:
                    points = presentation_times(runs, None, start + 1)
                else:
                    points = presentation_times(
                        runs, lower, upper if duration else None
                    )
                presented.update(
                    movie_time + abs(point - start) / abs(rate) for point in points
                )
        if len(presented) > 1:
            return True
        movie_time += span
    if int.from_bytes(edit[1:4]) & 1 and presented and movie_time:
        header = one_box(track, b"tkhd")
        offset, width = (28, 8) if header[0] == 1 else (20, 4)
        duration = int.from_bytes(header[offset : offset + width])
        return Fraction(duration * media_scale, movie_scale) > movie_time + min(
            presented
        )
    return False


def heif_is_animated(data):
    try:
        if not data or len(data) > 20_000_000:
            raise InvalidImage("Invalid HEIF input size.")
        ftyp = one_box(data, b"ftyp")
        if len(ftyp) < 8 or len(ftyp) % 4:
            raise InvalidImage("Invalid HEIF brands.")
        movie = one_box(data, b"moov", False)
        if movie is None:
            return False
        movie_scale = clock_scale(one_box(movie, b"mvhd"))
        for kind, track in boxes(movie):
            if kind != b"trak":
                continue
            media = one_box(track, b"mdia")
            handler = one_box(media, b"hdlr")
            if len(handler) < 12:
                raise InvalidImage("Invalid HEIF handler.")
            if bytes(handler[8:12]) not in {b"pict", b"vide", b"auxv"}:
                continue
            media_scale = clock_scale(one_box(media, b"mdhd"))
            table = one_box(one_box(media, b"minf"), b"stbl")
            runs, _ = timing_runs(table)
            if track_is_animated(track, runs, movie_scale, media_scale):
                return True
        return False
    except IndexError, struct.error:
        raise InvalidImage("Corrupted HEIF timeline.") from None
