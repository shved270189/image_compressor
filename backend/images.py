import ctypes
import io
import math
import struct
from contextlib import ExitStack, closing, contextmanager
from fractions import Fraction

from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError, _imagingcms
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


class OutputTooLarge(InvalidImage):
    pass


def check_pixels(image):
    if image.width * image.height > MAX_PIXELS:
        raise ImageTooLarge("Image exceeds 40,000,000 pixels.")


@contextmanager
def decode_image(source):
    with ExitStack() as stack:
        try:
            image = stack.enter_context(closing(Image.open(source)))
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
        except Image.DecompressionBombError:
            raise ImageTooLarge("Image exceeds 40,000,000 pixels.") from None
        except InvalidImage:
            raise
        except UnidentifiedImageError, OSError, SyntaxError, ValueError:
            raise InvalidImage("Image is empty or corrupted.") from None
        yield image


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


def timeline_end(runs):
    last_end = max(
        (first + step * (count - 1) for first, step, count in runs), default=0
    )
    if runs:
        last_end += runs[-1][1]
    return last_end


def presentation_times(runs, start=None, end=None, include_previous=True):
    points = set()
    previous = None
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
    if (
        include_previous
        and start is not None
        and previous is not None
        and start < timeline_end(runs)
    ):
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
                if rate < 0:
                    points = presentation_times(
                        runs, lower if duration else None, start, include_previous=False
                    )
                    first_time = min((first for first, _, _ in runs), default=0)
                    points = {point for point in points if point > first_time}
                    upper = min(start, timeline_end(runs))
                    if upper > first_time and (not duration or upper > lower):
                        points.add(upper)
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
            runs, end = timing_runs(table)
            header = one_box(track, b"tkhd")
            offset = 20 if header[0] == 1 else 12
            track_id = struct.unpack_from(">I", header, offset)[0]
            runs.extend(fragment_runs(data, movie, track_id, end))
            if track_is_animated(track, runs, movie_scale, media_scale):
                return True
        return False
    except IndexError, struct.error:
        raise InvalidImage("Corrupted HEIF timeline.") from None


def fragment_runs(data, movie, track_id, decode_time):
    defaults = {}
    extensions = one_box(movie, b"mvex", False)
    if extensions is not None:
        for kind, value in boxes(extensions):
            if kind == b"trex":
                if len(value) != 24 or value[0] != 0:
                    raise InvalidImage("Invalid HEIF fragment defaults.")
                identifier, _, duration, _, _ = struct.unpack_from(">5I", value, 4)
                if identifier in defaults:
                    raise InvalidImage("Duplicate HEIF fragment defaults.")
                defaults[identifier] = duration
    result = []
    for kind, fragment in boxes(data):
        if kind != b"moof":
            continue
        for name, track in boxes(fragment):
            if name != b"traf":
                continue
            header = one_box(track, b"tfhd")
            if len(header) < 8 or header[0] != 0:
                raise InvalidImage("Invalid HEIF fragment header.")
            flags, identifier = struct.unpack_from(">II", header)
            if identifier != track_id:
                continue
            position = 8 + (8 if flags & 1 else 0) + (4 if flags & 2 else 0)
            duration = defaults.get(identifier)
            if flags & 8:
                duration = struct.unpack_from(">I", header, position)[0]
                position += 4
            position += (4 if flags & 16 else 0) + (4 if flags & 32 else 0)
            if position != len(header):
                raise InvalidImage("Invalid HEIF fragment header extent.")
            base = one_box(track, b"tfdt", False)
            if base is not None:
                if base[0] not in (0, 1) or len(base) != (12 if base[0] else 8):
                    raise InvalidImage("Invalid HEIF fragment time.")
                decode_time = int.from_bytes(base[4:])
            for run_kind, run in boxes(track):
                if run_kind != b"trun":
                    continue
                if len(run) < 8 or run[0] not in (0, 1):
                    raise InvalidImage("Invalid HEIF fragment run.")
                flags = int.from_bytes(run[1:4])
                count = int.from_bytes(run[4:8])
                position = 8 + (4 if flags & 1 else 0) + (4 if flags & 4 else 0)
                fields = [flag for flag in (256, 512, 1024, 2048) if flags & flag]
                if len(run) != position + 4 * len(fields) * count:
                    raise InvalidImage("Invalid HEIF fragment sample extent.")
                if not fields:
                    if duration is None:
                        raise InvalidImage("Missing HEIF sample duration.")
                    if count:
                        result.append((decode_time, duration, count))
                    decode_time += duration * count
                    continue
                for _ in range(count):
                    sample_duration = duration
                    composition = 0
                    for flag in fields:
                        value = int.from_bytes(
                            run[position : position + 4],
                            signed=flag == 2048 and run[0] == 1,
                        )
                        if flag == 256:
                            sample_duration = value
                        elif flag == 2048:
                            composition = value
                        position += 4
                    if sample_duration is None:
                        raise InvalidImage("Missing HEIF sample duration.")
                    if composition != -(2**31):
                        result.append((decode_time + composition, sample_duration, 1))
                    decode_time += sample_duration
    return result


def output_size(size, max_width=None, max_height=None):
    width, height = size
    scale = min(
        Fraction(1),
        Fraction(max_width, width) if max_width else 1,
        Fraction(max_height, height) if max_height else 1,
    )
    return tuple(
        max(
            1,
            (2 * dimension * scale.numerator + scale.denominator)
            // (2 * scale.denominator),
        )
        for dimension in size
    )


def process_image(source, max_width=None, max_height=None, output_format="jpeg"):
    with decode_image(source) as image, ExitStack() as stack:
        size = output_size(image.size, max_width, max_height)
        limit = {"webp": 16_383, "jpeg": 65_500}.get(output_format)
        if limit and max(size) > limit:
            raise OutputTooLarge(
                f"{output_format.upper()} supports sides up to {limit:,} pixels. "
                "Reduce maximum width or height and try again."
            )
        resized = stack.enter_context(
            closing(
                image.resize(
                    size,
                    Image.Resampling.LANCZOS,
                )
            )
        )
        result, profile = stack.enter_context(normalize_color(resized))
        has_alpha = "A" in result.getbands()
        if output_format == "jpeg" and has_alpha:
            white = stack.enter_context(
                closing(Image.new("RGBA", result.size, "white"))
            )
            composite = stack.enter_context(
                closing(Image.alpha_composite(white, result))
            )
            result = stack.enter_context(closing(composite.convert("RGB")))
        result.info.clear()
        options = {"icc_profile": profile} if profile else {}
        if output_format == "webp":
            options["lossless"] = True
        with io.BytesIO() as output:
            result.save(output, format=output_format.upper(), **options)
            return output.getvalue()


class Chromaticity(ctypes.Structure):
    _fields_ = [(name, ctypes.c_double) for name in ("x", "y", "Y")]


class Primaries(ctypes.Structure):
    _fields_ = [(name, Chromaticity) for name in ("red", "green", "blue")]


def rgb_profile(chromaticities, decode=None, gamma=None):
    library = ctypes.CDLL(_imagingcms.__file__)
    pointer = ctypes.c_void_p
    library.cmsBuildGamma.argtypes = [pointer, ctypes.c_double]
    library.cmsBuildGamma.restype = pointer
    library.cmsBuildTabulatedToneCurve16.argtypes = [
        pointer,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint16),
    ]
    library.cmsBuildTabulatedToneCurve16.restype = pointer
    library.cmsCreateRGBProfile.argtypes = [
        ctypes.POINTER(Chromaticity),
        ctypes.POINTER(Primaries),
        ctypes.POINTER(pointer),
    ]
    library.cmsCreateRGBProfile.restype = pointer
    library.cmsSaveProfileToMem.argtypes = [
        pointer,
        pointer,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    library.cmsSaveProfileToMem.restype = ctypes.c_int
    library.cmsCloseProfile.argtypes = [pointer]
    library.cmsCloseProfile.restype = ctypes.c_int
    library.cmsFreeToneCurve.argtypes = [pointer]
    library.cmsFreeToneCurve.restype = None
    if (decode is None) == (gamma is None):
        raise ValueError("Supply one transfer function.")
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in chromaticities):
        raise InvalidImage("Invalid color chromaticities.")
    if gamma is not None and (not math.isfinite(gamma) or gamma <= 0):
        raise InvalidImage("Invalid color gamma.")
    if gamma is not None:
        curve = library.cmsBuildGamma(None, gamma)
    else:
        table = (ctypes.c_uint16 * 4096)(
            *(round(max(0, min(1, decode(i / 4095))) * 65535) for i in range(4096))
        )
        curve = library.cmsBuildTabulatedToneCurve16(None, len(table), table)
    if not curve:
        raise InvalidImage("Invalid color transfer curve.")
    try:
        white = Chromaticity(*chromaticities[:2], 1)
        primaries = Primaries(
            *(Chromaticity(*chromaticities[i : i + 2], 1) for i in (2, 4, 6))
        )
        profile = library.cmsCreateRGBProfile(
            ctypes.byref(white),
            ctypes.byref(primaries),
            (pointer * 3)(curve, curve, curve),
        )
        if not profile:
            raise InvalidImage("Invalid RGB color profile.")
        try:
            length = ctypes.c_uint32()
            if not library.cmsSaveProfileToMem(profile, None, ctypes.byref(length)):
                raise InvalidImage("Cannot encode color profile.")
            buffer = ctypes.create_string_buffer(length.value)
            if not library.cmsSaveProfileToMem(profile, buffer, ctypes.byref(length)):
                raise InvalidImage("Cannot encode color profile.")
            return ImageCms.ImageCmsProfile(io.BytesIO(buffer.raw))
        finally:
            library.cmsCloseProfile(profile)
    finally:
        library.cmsFreeToneCurve(curve)


def srgb_decode(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def color_profile(image):
    profile = image.info.get("icc_profile")
    if profile:
        try:
            return ImageCms.ImageCmsProfile(io.BytesIO(profile))
        except OSError:
            raise InvalidImage("Invalid image color profile.") from None
    nclx = image.info.get("nclx_profile")
    if nclx and nclx["color_primaries"] != 2 and nclx["transfer_characteristics"] != 2:
        chromaticities = tuple(
            nclx[f"color_primary_{color}_{axis}"]
            for color in ("white", "red", "green", "blue")
            for axis in ("x", "y")
        )
        transfer = nclx["transfer_characteristics"]
        if transfer in (16, 18):
            return rgb_profile(
                chromaticities, decode=hlg_decode if transfer == 18 else pq_decode
            )
        if transfer == 13:
            return rgb_profile(chromaticities, decode=srgb_decode)
        if transfer in (4, 5, 8):
            return rgb_profile(chromaticities, gamma={4: 2.2, 5: 2.8, 8: 1}[transfer])
        if transfer in (1, 6, 11, 12, 14, 15):
            return rgb_profile(
                chromaticities,
                decode=lambda value: (
                    value / 4.5
                    if value < 4.5 * 0.018053968510807
                    else ((value + 0.099296826809442) / 1.099296826809442) ** (1 / 0.45)
                ),
            )
        if transfer == 7:
            return rgb_profile(
                chromaticities,
                decode=lambda value: (
                    value / 4
                    if value < 4 * 0.022821585529445
                    else ((value + 0.111572195921731) / 1.111572195921731) ** (1 / 0.45)
                ),
            )
        if transfer in (9, 10):
            return rgb_profile(
                chromaticities,
                decode=lambda value: (
                    0
                    if value == 0
                    else 10 ** ((value - 1) * (2 if transfer == 9 else 2.5))
                ),
            )
    if "srgb" in image.info:
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    if "gamma" in image.info or "chromaticity" in image.info:
        chromaticities = image.info.get(
            "chromaticity", (0.3127, 0.329, 0.64, 0.33, 0.3, 0.6, 0.15, 0.06)
        )
        gamma = image.info.get("gamma")
        if gamma is not None:
            if gamma <= 0:
                raise InvalidImage("Invalid image color gamma.")
            return rgb_profile(chromaticities, gamma=1 / gamma)
        return rgb_profile(chromaticities, decode=srgb_decode)
    return None


@contextmanager
def normalize_color(image):
    with ExitStack() as stack:
        if image.mode in {"I;16", "I;16B", "I;16L", "I"}:
            integer = stack.enter_context(closing(image.convert("I")))
            scaled = stack.enter_context(
                closing(integer.point(lambda value: value * (255 / 65535) + 0.5))
            )
            normalized = stack.enter_context(closing(scaled.convert("L")))
            normalized.info = image.info.copy()
            image = normalized
        profile = color_profile(image)
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        mode = "RGBA" if has_alpha else "RGB"
        nclx = image.info.get("nclx_profile", {})
        hdr = nclx.get("transfer_characteristics") in (16, 18)
        if profile and (hdr or profile.profile.xcolor_space.strip() != "RGB"):
            target = (
                rgb_profile(nclx_chromaticities(nclx), decode=srgb_decode)
                if hdr
                else ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
            )
            try:
                result = stack.enter_context(
                    closing(
                        ImageCms.profileToProfile(
                            image, profile, target, outputMode="RGB"
                        )
                    )
                )
            except ImageCms.PyCMSError:
                raise InvalidImage("Invalid image color model.") from None
            if has_alpha:
                rgba = stack.enter_context(closing(image.convert("RGBA")))
                alpha = stack.enter_context(closing(rgba.getchannel("A")))
                result.putalpha(alpha)
            profile = target
        else:
            result = stack.enter_context(closing(image.convert(mode)))
        yield result, profile.tobytes() if profile else None


def hlg_decode(value):
    a = 0.17883277
    b = 1 - 4 * a
    c = 0.5 - a * math.log(4 * a)
    return value * value / 3 if value <= 0.5 else (math.exp((value - c) / a) + b) / 12


def pq_decode(value):
    power = value ** (32 / 2523)
    return (max(power - 3424 / 4096, 0) / (2413 / 128 - 2392 / 128 * power)) ** (
        16384 / 2610
    )


def nclx_chromaticities(nclx):
    return tuple(
        nclx[f"color_primary_{color}_{axis}"]
        for color in ("white", "red", "green", "blue")
        for axis in ("x", "y")
    )
