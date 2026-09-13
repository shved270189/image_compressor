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


def noisy(size=(2400, 1200)):
    width, height = size
    payload = bytes((index * 37) % 256 for index in range(width * height * 3))
    with Image.frombytes("RGB", size, payload) as image, io.BytesIO() as stream:
        image.save(stream, "PNG")
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


def test_dwell_after_composition_timeline_end_is_not_presented():
    images = image_module()
    data = timeline(durations=(100, 1), offsets=(0, -99), edits=[(1, 50, 0), (1, 0, 0)])
    assert not images.heif_is_animated(data)


def test_fractional_forward_edit_rate():
    images = image_module()
    data = bytearray(timeline(edits=[(100, 0, 0)]))
    offset = data.index(b"elst") + 20
    data[offset : offset + 4] = (32768).to_bytes(4)
    assert images.heif_is_animated(data)


@pytest.mark.parametrize(
    "name,animated",
    [("fragmented-sequence.heic", True), ("fragmented-gallery.heic", False)],
)
def test_independently_encoded_fragmented_controls(name, animated):
    images = image_module()
    path = FIXTURES / name
    with Image.open(path) as primary:
        assert primary.size == (128, 128)
        expected = primary.tobytes()
    assert images.heif_is_animated(path.read_bytes()) is animated
    with path.open("rb") as source:
        if animated:
            with pytest.raises(images.InvalidImage), images.decode_image(source):
                pytest.fail("Fragmented animation accepted")
        else:
            with images.decode_image(source) as result:
                assert result.tobytes() == expected


@pytest.mark.parametrize(
    "explicit,composition,animated",
    [
        (True, (0, -40), False),
        (True, (0, 0), True),
        (False, (0, -40), False),
        (False, (0, 0), True),
    ],
)
def test_fragment_duration_defaults_and_signed_composition(
    explicit, composition, animated
):
    images = image_module()
    data = timeline(durations=())
    movie = data[28:] + box(
        b"mvex", box(b"trex", struct.pack(">6I", 0, 1, 1, 40, 0, 0))
    )
    data = data[:20] + box(b"moov", movie)
    for index, offset in enumerate(composition):
        header = box(b"tfhd", struct.pack(">II", 0, 1))
        flags = 0x1000800 | (256 if explicit else 0)
        values = struct.pack(">I", 40) if explicit else b""
        run = box(
            b"trun", struct.pack(">II", flags, 1) + values + struct.pack(">i", offset)
        )
        base = box(b"tfdt", struct.pack(">II", 0, 0)) if index == 0 else b""
        data += box(b"moof", box(b"traf", header + base + run))
    assert images.heif_is_animated(data) is animated


@pytest.mark.parametrize(
    "size,width,height,expected",
    [
        ((2400, 1200), 1200, None, (1200, 600)),
        ((2400, 1200), None, 300, (600, 300)),
        ((2400, 1200), 1200, 300, (600, 300)),
        ((1000, 333), 500, None, (500, 167)),
        ((800, 600), 1600, None, (800, 600)),
        ((1, 4000), 1, 1, (1, 1)),
        ((4000, 1), 1, 1, (1, 1)),
        ((12, 8), 10**1000, None, (12, 8)),
    ],
)
def test_geometry_and_encoded_bounds(size, width, height, expected):
    images = image_module()
    assert hasattr(images, "process_image"), "Image transformation is not implemented"
    assert images.output_size(size, width, height) == expected
    with io.BytesIO(encoded(size=size)) as source:
        data = images.process_image(source, width, height, "png")
    with Image.open(io.BytesIO(data)) as result:
        assert result.size == expected


@pytest.mark.parametrize("input_format", ["JPEG", "PNG", "WEBP", "HEIF"])
@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_all_format_pairs(input_format, output_format):
    images = image_module()
    with io.BytesIO(encoded(input_format)) as source:
        data = images.process_image(source, None, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.format == output_format.upper()
        assert result.size == (12, 8)
        assert result.n_frames == 1 if hasattr(result, "n_frames") else True


@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
@pytest.mark.parametrize("alpha", [0, 128])
def test_output_transparency(output_format, alpha):
    images = image_module()
    with io.BytesIO(encoded(mode="RGBA", color=(255, 0, 0, alpha))) as source:
        data = images.process_image(source, None, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        if output_format == "jpeg":
            expected = (255, 255 - alpha, 255 - alpha)
            assert all(
                abs(a - b) <= 2 for a, b in zip(result.getpixel((0, 0)), expected)
            )
        else:
            assert result.getpixel((0, 0))[3] == alpha


@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_normalization_removes_service_metadata(output_format):
    from PIL.PngImagePlugin import PngInfo

    images = image_module()
    exif = Image.Exif()
    exif[274] = 6
    exif[271] = "Private camera"
    metadata = PngInfo()
    metadata.add_text("Description", "Private location")
    with io.BytesIO(encoded(exif=exif, pnginfo=metadata)) as source:
        data = images.process_image(source, 4, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.size == (4, 6)
        assert not result.getexif()
        assert not getattr(result, "text", {})
        assert not result.info.get("xmp")


def test_reverse_fragment_edit_starts_at_visible_upper_boundary():
    images = image_module()
    data = timeline(durations=(), edits=[(20, 70, -1), (20, 0, 0)])
    header = box(b"tfhd", struct.pack(">III", 8, 1, 40))
    run = box(b"trun", struct.pack(">II", 0, 3))
    data += box(b"moof", box(b"traf", header + run))
    assert images.heif_is_animated(data)


def png_color_sample():
    import zlib

    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"gAMA", struct.pack(">I", 100000))
        + chunk(
            b"cHRM",
            struct.pack(">8I", 31270, 32900, 64000, 33000, 30000, 60000, 15000, 6000),
        )
        + chunk(b"IDAT", zlib.compress(b"\x00\x80\x80\x80"))
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_png_gamma_preserves_color_interpretation(output_format):
    from PIL import ImageCms

    images = image_module()
    with io.BytesIO(png_color_sample()) as source:
        data = images.process_image(source, None, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.info.get("icc_profile"), "PNG gamma/chromaticities were lost"
        profile = ImageCms.ImageCmsProfile(io.BytesIO(result.info["icc_profile"]))
        with ImageCms.profileToProfile(
            result, profile, ImageCms.createProfile("sRGB"), outputMode="RGB"
        ) as display:
            assert all(abs(v - 188) <= 1 for v in display.getpixel((0, 0)))


@pytest.mark.parametrize("name", ["arrow.heic", "guitar_cw90.hif"])
@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_heic_wide_gamut_and_nclx_profiles(name, output_format):
    from PIL import ImageCms

    images = image_module()
    with (FIXTURES / name).open("rb") as source:
        data = images.process_image(source, 32, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.info.get("icc_profile")
        profile = ImageCms.ImageCmsProfile(io.BytesIO(result.info["icc_profile"]))
        assert profile.profile.xcolor_space.strip() == "RGB"
        if name == "arrow.heic":
            assert "Display P3" in ImageCms.getProfileName(profile)
        assert not result.getexif()


@pytest.mark.parametrize(
    "mode,profile_name,color,expected",
    [
        ("CMYK", "cmyk.icc", (100, 50, 0, 20), (137, 165, 196)),
        ("L", "gray.icc", 128, (146, 146, 146)),
    ],
)
@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_color_model_conversion(mode, profile_name, color, expected, output_format):
    from PIL import ImageCms

    images = image_module()
    profile = (FIXTURES / profile_name).read_bytes()
    with io.BytesIO(
        encoded(
            "JPEG" if mode == "CMYK" else "PNG",
            mode=mode,
            color=color,
            icc_profile=profile,
        )
    ) as source:
        data = images.process_image(source, None, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.mode == "RGB"
        assert (
            ImageCms.ImageCmsProfile(
                io.BytesIO(result.info["icc_profile"])
            ).profile.xcolor_space.strip()
            == "RGB"
        )
        assert all(
            abs(value - target) <= 2
            for value, target in zip(result.getpixel((0, 0)), expected)
        )


@pytest.mark.parametrize(
    "transfer,expected", [(18, (0, 40, 82, 142, 255)), (16, (0, 2, 24, 89, 255))]
)
def test_hdr_analytic_anchors(transfer, expected):
    images = image_module()
    with Image.open(FIXTURES / "DEMO_BT2100_HLG.heic") as real:
        nclx = dict(real.info["nclx_profile"])
    nclx["transfer_characteristics"] = transfer
    with Image.new("RGBA", (5, 1)) as sample:
        sample.putdata([(v, v, v, 128) for v in (0, 64, 128, 192, 255)])
        sample.info["nclx_profile"] = nclx
        with images.normalize_color(sample) as (result, profile):
            assert profile
            for x, value in enumerate(expected):
                pixel = result.getpixel((x, 0))
                assert all(abs(channel - value) <= 1 for channel in pixel[:3])
                assert pixel[3] == 128


@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_real_hlg_becomes_eight_bit_sdr(output_format):
    from PIL import ImageCms

    images = image_module()
    with (FIXTURES / "DEMO_BT2100_HLG.heic").open("rb") as source:
        data = images.process_image(source, 60, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.mode == "RGB" and result.size == (60, 40)
        profile = ImageCms.ImageCmsProfile(io.BytesIO(result.info["icc_profile"]))
        assert profile.profile.xcolor_space.strip() == "RGB"
        assert (
            profile.profile.red_colorant != ImageCms.createProfile("sRGB").red_colorant
        )
        assert not result.getexif()


@pytest.mark.parametrize("output_format", ["png", "webp"])
def test_color_key_transparency_is_expanded_before_resize(output_format):
    images = image_module()
    with Image.new("RGB", (2, 1)) as image, io.BytesIO() as source:
        image.putdata([(255, 0, 0), (0, 0, 255)])
        image.save(source, "PNG", transparency=(255, 0, 0))
        source.seek(0)
        data = images.process_image(source, 1, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.getpixel((0, 0)) == (0, 0, 255, 128)


@pytest.mark.parametrize("output_format", ["png", "webp"])
def test_sixteen_bit_transparency_uses_original_samples(output_format):
    images = image_module()
    with (
        Image.frombytes("I;16", (2, 1), struct.pack("<HH", 32768, 32769)) as image,
        io.BytesIO() as source,
    ):
        image.save(source, "PNG", transparency=32768)
        source.seek(0)
        data = images.process_image(source, None, None, output_format)
    with Image.open(io.BytesIO(data)) as result:
        assert result.mode == "RGBA"
        assert result.getpixel((0, 0))[3] == 0
        assert result.getpixel((1, 0)) == (128, 128, 128, 255)


@pytest.mark.parametrize("has_movie", [False, True])
def test_orphan_fragment_is_rejected(has_movie):
    images = image_module()
    data = timeline(durations=()) if has_movie else (
        FIXTURES / "RGB_10__128x128.heif"
    ).read_bytes()
    header = box(b"tfhd", struct.pack(">III", 8, 77, 40))
    run = box(b"trun", struct.pack(">II", 0, 3))
    data += box(b"moof", box(b"traf", header + run))
    with pytest.raises(images.InvalidImage):
        images.heif_is_animated(data)
    if not has_movie:
        with (
            io.BytesIO(data) as source,
            pytest.raises(images.InvalidImage),
            images.decode_image(source),
        ):
            pytest.fail("Orphan fragment accepted during decoding")


def test_omitted_size_limit_keeps_largest_proportional_fit():
    images = image_module()
    with io.BytesIO(encoded(size=(2400, 1200))) as source:
        data = images.process_image(source, 1200, None, "png", size_limit_bytes=None)
    with Image.open(io.BytesIO(data)) as result:
        assert result.size == (1200, 600)


def test_extra_shrink_undercuts_ceiling_while_preserving_aspect():
    images = image_module()
    source_bytes = noisy()
    with io.BytesIO(source_bytes) as source:
        ceiling = images.process_image(source, 1200, None, "jpeg")
    bound = len(ceiling) - 1
    with io.BytesIO(source_bytes) as source:
        data = images.process_image(source, 1200, None, "jpeg", size_limit_bytes=bound)
    with Image.open(io.BytesIO(data)) as result:
        assert result.format == "JPEG"
        assert result.size[0] < 1200
        assert result.size == images.output_size((2400, 1200), result.size[0], None)
    assert len(data) <= bound


def test_one_pixel_miss_still_returns_encoded_file():
    images = image_module()
    with io.BytesIO(noisy()) as source:
        data = images.process_image(source, 1200, None, "jpeg", size_limit_bytes=1)
    assert data
    with Image.open(io.BytesIO(data)) as result:
        assert result.format == "JPEG"
        assert result.size == images.output_size((2400, 1200), 1, None)
    assert len(data) > 1


def test_size_limit_comparison_uses_whole_encoded_bytes():
    images = image_module()
    source_bytes = noisy()
    with io.BytesIO(source_bytes) as source:
        ceiling = images.process_image(source, 1200, None, "jpeg")
    bound = len(ceiling)
    with io.BytesIO(source_bytes) as source:
        data = images.process_image(source, 1200, None, "jpeg", size_limit_bytes=bound)
    assert len(data) <= bound
    with Image.open(io.BytesIO(data)) as result:
        assert result.size == (1200, 600)
