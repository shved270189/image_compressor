import importlib
import io
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
