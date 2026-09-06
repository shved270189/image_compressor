import importlib
import io
import struct
from pathlib import Path

import pytest
from PIL import Image

from backend import main

FIXTURES = Path(__file__).parent / "fixtures" / "images"


def image_module():
    assert hasattr(main, "images"), "Image decoding is not implemented"
    return importlib.import_module("backend.images")


def encoded(format="PNG", size=(12, 8), mode="RGB", color="red", **options):
    with Image.new(mode, size, color) as image, io.BytesIO() as stream:
        image.save(stream, format=format, **options)
        return stream.getvalue()


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP", "HEIF"])
def test_decode_supported_content(format):
    images = image_module()
    with io.BytesIO(encoded(format)) as source, images.decode_image(source) as image:
        assert image.size == (12, 8)
        assert image.getpixel((0, 0))[0] >= 240


def test_heic_nonfirst_primary():
    images = image_module()
    path = FIXTURES / "zPug_3.heic"
    with Image.open(path) as expected:
        assert expected.tell() == 1 and expected.info["primary"]
        pixels, size = expected.tobytes(), expected.size
    with path.open("rb") as source, images.decode_image(source) as image:
        assert image.size == size
        assert image.tobytes() == pixels


@pytest.mark.parametrize("format", ["PNG", "WEBP"])
def test_reject_animation(format):
    images = image_module()
    with Image.new("RGB", (8, 8), "blue") as other:
        data = encoded(
            format, (8, 8), save_all=True, append_images=[other], duration=100
        )
    with (
        io.BytesIO(data) as source,
        pytest.raises(images.InvalidImage),
        images.decode_image(source),
    ):
        pytest.fail("Animated image accepted")


@pytest.mark.parametrize(
    "data,kind",
    [
        (b"", "InvalidImage"),
        (b"bad", "InvalidImage"),
        (encoded("BMP"), "UnsupportedImage"),
        (encoded()[:50], "InvalidImage"),
    ],
)
def test_reject_invalid_content(data, kind):
    images = image_module()
    with (
        io.BytesIO(data) as source,
        pytest.raises(getattr(images, kind)),
        images.decode_image(source),
    ):
        pytest.fail("Invalid image accepted")


@pytest.mark.parametrize(
    "width,accepted", [(7_999, True), (8_000, True), (8_001, False)]
)
def test_pixel_boundary(width, accepted, monkeypatch):
    images = image_module()
    data = encoded("PNG", (width, 5_000), "L", 100)
    calls = []
    original = Image.Image.load

    def load(image, *args, **kwargs):
        calls.append(image.size)
        return original(image, *args, **kwargs)

    monkeypatch.setattr(Image.Image, "load", load)
    with io.BytesIO(data) as source:
        if accepted:
            with images.decode_image(source) as image:
                assert image.size == (width, 5_000)
                assert image.getpixel((0, 0)) == 100
            assert calls
        else:
            with pytest.raises(images.ImageTooLarge), images.decode_image(source):
                pytest.fail("Oversized image accepted")
            assert not calls


@pytest.mark.parametrize("failure", ["load", "dimensions"])
def test_decoding_failure_closes_image(failure, monkeypatch):
    images = image_module()
    source = Image.new("RGB", (2, 2))
    closed = []
    original_close = source.close

    def close():
        closed.append(True)
        original_close()

    def load():
        if failure == "load":
            raise OSError("private decoder detail")
        source._size = (40_000_001, 1)

    source.format = "PNG"
    monkeypatch.setattr(source, "load", load)
    monkeypatch.setattr(source, "close", close)
    monkeypatch.setattr(Image, "open", lambda *args, **kwargs: source)
    with (
        io.BytesIO(b"image") as buffer,
        pytest.raises(images.InvalidImage),
        images.decode_image(buffer),
    ):
        pytest.fail("Invalid decode accepted")
    assert closed


@pytest.mark.parametrize("orientation,size", [(2, (12, 8)), (6, (8, 12)), (8, (8, 12))])
def test_orientation_once(orientation, size):
    images = image_module()
    exif = Image.Exif()
    exif[274] = orientation
    with (
        io.BytesIO(encoded("PNG", exif=exif)) as source,
        images.decode_image(source) as image,
    ):
        assert image.size == size
        assert image.getexif().get(274, 1) == 1


def test_heic_primary_alpha():
    images = image_module()
    with (
        (FIXTURES / "RGBA_10__128x128.heif").open("rb") as source,
        images.decode_image(source) as image,
    ):
        assert image.mode == "RGBA"
        with image.getchannel("A") as alpha:
            assert alpha.getextrema()[0] < 255


def box(kind, payload=b""):
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def timeline(
    durations=(40, 40, 40), offsets=None, edits=None, media_scale=1000, movie_scale=1000
):
    stts = box(
        b"stts",
        struct.pack(">II", 0, len(durations))
        + b"".join(struct.pack(">II", 1, d) for d in durations),
    )
    ctts = (
        b""
        if offsets is None
        else box(
            b"ctts",
            struct.pack(">II", 1 << 24, len(offsets))
            + b"".join(struct.pack(">Ii", 1, d) for d in offsets),
        )
    )
    table = box(b"stbl", stts + ctts)
    mdhd = box(b"mdhd", struct.pack(">6I", 0, 0, 0, media_scale, sum(durations), 0))
    handler = box(b"hdlr", b"\0" * 8 + b"pict" + b"\0" * 12)
    media = box(b"mdia", mdhd + handler + box(b"minf", table))
    edit = (
        b""
        if edits is None
        else box(
            b"edts",
            box(
                b"elst",
                struct.pack(">II", 0, len(edits))
                + b"".join(
                    struct.pack(">Iihh", duration, start, rate, 0)
                    for duration, start, rate in edits
                ),
            ),
        )
    )
    tkhd = box(b"tkhd", struct.pack(">6I", 3, 0, 0, 1, 0, 1000) + b"\0" * 60)
    mvhd = box(b"mvhd", struct.pack(">5I", 0, 0, 0, movie_scale, 1000) + b"\0" * 80)
    return box(b"ftyp", b"heic\0\0\0\0mif1") + box(
        b"moov", mvhd + box(b"trak", tkhd + media + edit)
    )


@pytest.mark.parametrize(
    "options,animated",
    [
        ({}, True),
        ({"durations": (0, 0, 0)}, False),
        ({"durations": (40,)}, False),
        ({"offsets": (80, 40, 0)}, False),
        ({"offsets": (80, 0, -80)}, True),
        ({"edits": []}, False),
        ({"edits": [(1000, -1, 1)]}, False),
        ({"edits": [(1000, 50, 0)]}, False),
        ({"edits": [(20, 50, 1)]}, False),
        ({"edits": [(50, 50, 1)]}, True),
        ({"edits": [(0, 50, 1)]}, True),
        ({"edits": [(0, 90, -1)]}, True),
        ({"edits": [(20, 0, 1), (20, 80, 1)]}, True),
        ({"edits": [(1, 0, 1)], "movie_scale": 10}, True),
    ],
)
def test_heif_presentation_timing(options, animated):
    images = image_module()
    assert hasattr(images, "heif_is_animated"), (
        "HEIF timeline classification is not implemented"
    )
    assert images.heif_is_animated(timeline(**options)) is animated


def test_real_heif_sequence_without_sequence_brands():
    images = image_module()
    data = bytearray((FIXTURES / "starfield_animation.heic").read_bytes())
    size = int.from_bytes(data[:4])
    data[8:12] = b"heic"
    for position in range(16, size, 4):
        data[position : position + 4] = b"mif1"
    with (
        io.BytesIO(data) as source,
        pytest.raises(images.InvalidImage),
        images.decode_image(source),
    ):
        pytest.fail("Sequence with spoofed brands accepted")


@pytest.mark.parametrize(
    "data",
    [
        b"1234567",
        struct.pack(">I4s", 1, b"ftyp"),
        struct.pack(">I4s", 7, b"ftyp"),
        struct.pack(">I4sQ", 1, b"ftyp", 2**64 - 1),
        timeline() + b"x",
        timeline(offsets=(0,)),
    ],
)
def test_malformed_heif_boxes(data):
    images = image_module()
    with pytest.raises(images.InvalidImage):
        images.heif_is_animated(data)


def test_repeat_edit_respects_first_presentation_offset():
    images = image_module()
    data = bytearray(timeline(durations=(40,), edits=[(90, -1, 1), (10, 0, 0)]))
    offset = data.index(b"elst") + 4
    data[offset : offset + 4] = (1).to_bytes(4)
    offset = data.index(b"tkhd") + 4 + 20
    data[offset : offset + 4] = (150).to_bytes(4)
    assert not images.heif_is_animated(data)
