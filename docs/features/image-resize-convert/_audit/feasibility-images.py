import argparse
import ctypes
import hashlib
import io
import json
import math
import platform
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

import PIL
import pillow_heif
from PIL import Image, ImageChops, ImageCms, ImageOps, ImageStat, _imagingcms

UPSTREAM = "https://raw.githubusercontent.com/bigcat88/pillow_heif/11a2a9f2e0259f0a5594e1e5df1afbe7b9204cce/tests/images/"
NOKIA = "https://raw.githubusercontent.com/nokiatech/heif/897fdf20ec788a406c3e7dee5225caf9e0dcf79a/content/image_sequences/"
FIXTURES = {
    "primary": (
        UPSTREAM + "heif/zPug_3.heic",
        "daf1515c651e15968ad6ec142e443759156fee76c65715e4f5713cf1ad072774",
    ),
    "10bit": (
        UPSTREAM + "heif/RGB_10__128x128.heif",
        "7fbf1573c1e5c1693953b31bb287327c53eaefa74a6f1324e7391a08b3ed1e73",
    ),
    "12bit": (
        UPSTREAM + "heif/RGB_12__128x128.heif",
        "92c048d4bead7eebd3e0da5cb13a2e286cccbde3acb23580ee9c5f6b4cfde812",
    ),
    "alpha": (
        UPSTREAM + "heif/RGBA_10__128x128.heif",
        "ca7bc70f1d8b1103e7094c3758a70991ad31e2cbcabb02f4ec7e79e5a6d4bc5f",
    ),
    "orientation": (
        UPSTREAM + "heif_other/arrow.heic",
        "73f604d7353df4848505a1f45a5517f736857fe047372f95c2f3d671df92c22c",
    ),
    "nclx": (
        UPSTREAM + "heif_special/guitar_cw90.hif",
        "f0d5e88be07b9d70a3715218ca612ccf45b126e5b4b42172dce14a62d2099932",
    ),
    "sequence": (
        NOKIA + "starfield_animation.heic",
        "fbf31cd9aa6fc4c997d7eb2ea05541627bf3dbcb4115b7d453f63dcd1ec4fb26",
    ),
    "hlg": (
        "https://raw.githubusercontent.com/certiday/LUMIX2HLG/00bd2e4457220df012ec530c4f0d2e59bfc5cfba/DEMO_BT2100_HLG.heic",
        "75481b8fa596cedcdc782f593d946624c34a96196c02eb1ee4abaab8db45175e",
    ),
}


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
    assert (decode is None) != (gamma is None)
    if gamma is not None:
        curve = library.cmsBuildGamma(None, gamma)
    else:
        table = (ctypes.c_uint16 * 4096)(
            *(round(max(0, min(1, decode(i / 4095))) * 65535) for i in range(4096))
        )
        curve = library.cmsBuildTabulatedToneCurve16(None, len(table), table)
    assert curve
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
        assert profile
        try:
            length = ctypes.c_uint32()
            assert library.cmsSaveProfileToMem(profile, None, ctypes.byref(length))
            buffer = ctypes.create_string_buffer(length.value)
            assert library.cmsSaveProfileToMem(profile, buffer, ctypes.byref(length))
            return ImageCms.ImageCmsProfile(io.BytesIO(buffer.raw))
        finally:
            library.cmsCloseProfile(profile)
    finally:
        library.cmsFreeToneCurve(curve)


def srgb_decode(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


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


def fetch_fixtures(directory):
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, (url, digest) in FIXTURES.items():
        path = directory / url.rsplit("/", 1)[1]
        if not path.exists():
            path.write_bytes(urllib.request.urlopen(url, timeout=60).read())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        paths[name] = path
    return paths


def encode(image, output_format, profile=None):
    options = {"icc_profile": profile} if profile else {}
    if output_format == "WEBP":
        options["lossless"] = True
    with image.copy() as output, io.BytesIO() as buffer:
        output.info.clear()
        output.save(buffer, format=output_format, **options)
        return buffer.getvalue()


def primary_and_sequence(paths):
    with Image.open(paths["primary"]) as image:
        assert image.tell() == 1 and image.info["primary"]
        assert image.n_frames == 3 and image.is_animated
        assert pillow_heif.get_file_mimetype(paths["primary"]) == "image/heic"
        expected = image.tobytes()
        with Image.open(io.BytesIO(encode(image, "PNG"))) as result:
            assert result.n_frames == 1 and result.tobytes() == expected
    with Image.open(paths["sequence"]) as image:
        assert image.n_frames == 1 and not image.is_animated
        assert pillow_heif.get_file_mimetype(paths["sequence"]) == "image/heif-sequence"
        image.load()
    return "Non-first primary exported alone; MIME distinguishes this true sequence, frame count does not."


def bit_depth_and_alpha(paths):
    for name, depth in (("10bit", 10), ("12bit", 12), ("alpha", 10)):
        with Image.open(paths[name]) as image:
            assert image.info["bit_depth"] == depth
            assert image.size == (128, 128)
            assert image.mode == ("RGBA" if name == "alpha" else "RGB")
            assert len(image.tobytes()) == 128 * 128 * len(image.getbands())
            for output_format in ("PNG", "WEBP"):
                with Image.open(io.BytesIO(encode(image, output_format))) as result:
                    assert result.tobytes() == image.tobytes()
            if name == "alpha":
                with image.getchannel("A") as alpha:
                    assert alpha.getextrema()[0] < 255
    with Image.new("RGBA", (16, 16), (255, 0, 0, 128)) as half:
        with (
            Image.new("RGBA", half.size, "white") as white,
            Image.alpha_composite(white, half).convert("RGB") as result,
        ):
            assert result.getpixel((0, 0)) == (255, 127, 127)
            with Image.open(io.BytesIO(encode(result, "JPEG"))) as jpeg:
                assert all(
                    abs(a - b) <= 2
                    for a, b in zip(jpeg.getpixel((0, 0)), (255, 127, 127))
                )
        half.putalpha(0)
        with (
            Image.new("RGBA", half.size, "white") as white,
            Image.alpha_composite(white, half).convert("RGB") as result,
            Image.open(io.BytesIO(encode(result, "JPEG"))) as jpeg,
        ):
            assert jpeg.getpixel((0, 0)) == (255, 255, 255)
    return "10/12-bit inputs decode to 8-bit; disabled auxiliary processing retains HEIC alpha; white JPEG compositing works."


def orientation_and_icc(paths):
    with Image.open(paths["orientation"]) as image:
        assert image.info["original_orientation"] == 6
        assert image.size == (3024, 4032)
        assert image.getexif().get(274, 1) == 1
        profile = image.info["icc_profile"]
        assert "Display P3" in ImageCms.getProfileName(
            ImageCms.ImageCmsProfile(io.BytesIO(profile))
        )
        with ImageOps.exif_transpose(image) as oriented:
            assert oriented.size == image.size and oriented.tobytes() == image.tobytes()
            with oriented.resize((30, 40)) as small:
                for output_format in ("JPEG", "PNG", "WEBP"):
                    with Image.open(
                        io.BytesIO(encode(small, output_format, profile))
                    ) as result:
                        assert result.info["icc_profile"] == profile
                        assert not result.getexif() and not result.info.get("xmp")
                        assert not getattr(result, "text", {})
                        if output_format != "JPEG":
                            assert result.tobytes() == small.tobytes()
    return "HEIC orientation is already applied once; a subsequent exif_transpose is inert; compatible P3 ICC survives all outputs without EXIF/XMP/text."


def mode_transform():
    lab = ImageCms.createProfile("LAB")
    srgb = ImageCms.createProfile("sRGB")
    with (
        Image.new("LAB", (1, 1), (255, 128, 128)) as source,
        ImageCms.profileToProfile(source, lab, srgb, outputMode="RGB") as result,
    ):
        assert min(result.getpixel((0, 0))) >= 254
        assert (
            ImageCms.ImageCmsProfile(
                io.BytesIO(result.info["icc_profile"])
            ).profile.xcolor_space.strip()
            == "RGB"
        )
    return "ImageCms changes a neutral D50 Lab white to RGB white and attaches a matching RGB profile; this is not CMYK fixture coverage."


def orientation_reference(paths, reference):
    with Image.open(paths["orientation"]) as image, Image.open(reference) as native:
        assert native.size == (4032, 3024) and native.getexif()[274] == 6
        with native.transpose(Image.Transpose.ROTATE_270) as expected:
            assert image.size == expected.size
            with ImageChops.difference(image, expected) as difference:
                means = ImageStat.Stat(difference).mean
                assert max(means) < 2, means
    return f"Apple ImageIO/sips independent decoder; EXIF 6 explicitly rotates 90 degrees clockwise; mean absolute channel differences {means}."


def nclx_preservation(paths):
    with Image.open(paths["nclx"]) as image:
        assert "icc_profile" not in image.info
        nclx = image.info["nclx_profile"]
        assert (nclx["color_primaries"], nclx["transfer_characteristics"]) == (1, 13)
        profile = rgb_profile(nclx_chromaticities(nclx), decode=srgb_decode).tobytes()
        with image.resize((32, 48)) as small:
            for output_format in ("JPEG", "PNG", "WEBP"):
                with Image.open(
                    io.BytesIO(encode(small, output_format, profile))
                ) as result:
                    assert result.info["icc_profile"] == profile
                    assert not result.getexif() and not result.info.get("xmp")
                    if output_format != "JPEG":
                        assert result.tobytes() == small.tobytes()
    return "NCLX chromaticities and sRGB transfer become a matching LCMS RGB ICC; all outputs retain it, unchanged lossless pixels and no service metadata."


def png_color_preservation():
    def chunk(name, payload):
        return (
            struct.pack(">I", len(payload))
            + name
            + payload
            + struct.pack(">I", zlib.crc32(name + payload))
        )

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    data += chunk(b"gAMA", struct.pack(">I", 100000))
    data += chunk(
        b"cHRM",
        struct.pack(">8I", 31270, 32900, 64000, 33000, 30000, 60000, 15000, 6000),
    )
    data += chunk(b"IDAT", zlib.compress(b"\x00\x80\x80\x80"))
    data += chunk(b"IEND", b"")
    with Image.open(io.BytesIO(data)) as image:
        assert image.info["gamma"] == 1.0 and len(image.info["chromaticity"]) == 8
        assert "icc_profile" not in image.info
        assert image.getpixel((0, 0)) == (128, 128, 128)
        profile = rgb_profile(image.info["chromaticity"], gamma=1 / image.info["gamma"])
        srgb = ImageCms.createProfile("sRGB")
        for output_format in ("JPEG", "PNG", "WEBP"):
            with Image.open(
                io.BytesIO(encode(image, output_format, profile.tobytes()))
            ) as result:
                assert result.info["icc_profile"] == profile.tobytes()
                assert result.getpixel((0, 0)) == (128, 128, 128)
                with ImageCms.profileToProfile(
                    result, profile, srgb, outputMode="RGB"
                ) as display:
                    assert all(
                        abs(channel - 188) <= 1 for channel in display.getpixel((0, 0))
                    )
    return "PNG gAMA=1/cHRM becomes an equivalent ICC without changing pixels; every output's linear RGB128 displays as sRGB188 within one code value."


def hlg_color_conversion(paths):
    data = paths["hlg"].read_bytes()
    offset = data.index(b"colrnclx") + 8
    assert struct.unpack(">HHHB", data[offset : offset + 7]) == (9, 18, 9, 128)
    with Image.open(paths["hlg"]) as image:
        assert image.size == (6016, 4016) and image.mode == "RGB"
        assert image.info["bit_depth"] == 10 and "icc_profile" not in image.info
        assert image.info["nclx_profile"]["transfer_characteristics"] == 18
        assert len(image.tobytes()) == 6016 * 4016 * 3
        chromaticities = nclx_chromaticities(image.info["nclx_profile"])
        source = rgb_profile(chromaticities, decode=hlg_decode)
        target = rgb_profile(chromaticities, decode=srgb_decode)
        assert source.profile.red_colorant == target.profile.red_colorant
        with (
            image.resize((60, 40)) as small,
            ImageCms.profileToProfile(
                small, source, target, outputMode="RGB"
            ) as normalized,
        ):
            assert normalized.tobytes() != small.tobytes()
            for output_format in ("JPEG", "PNG", "WEBP"):
                with Image.open(
                    io.BytesIO(encode(normalized, output_format, target.tobytes()))
                ) as result:
                    result.load()
                    assert result.size == small.size and result.mode == "RGB"
                    assert result.info["icc_profile"] == target.tobytes()
                    assert not result.getexif() and not result.info.get("xmp")
                    if output_format != "JPEG":
                        assert result.tobytes() == normalized.tobytes()
    return "Real 10-bit HLG fixture converts to ordinary 8-bit SDR RGB with matching BT.2020 ICC in JPEG/PNG/WebP; source gamut remains, full-range relative HLG light replaces HDR appearance."


def analytical_transfer_checks():
    chromaticities = (0.3127, 0.3290, 0.708, 0.292, 0.170, 0.797, 0.131, 0.046)
    target = rgb_profile(chromaticities, decode=srgb_decode)
    srgb = ImageCms.createProfile("sRGB")
    assert target.profile.red_colorant != srgb.red_colorant
    for decode, expected in (
        (hlg_decode, (0, 40, 82, 142, 255)),
        (pq_decode, (0, 2, 24, 89, 255)),
    ):
        source = rgb_profile(chromaticities, decode=decode)
        assert source.profile.red_colorant == target.profile.red_colorant
        with Image.new("RGB", (10, 1)) as samples:
            samples.putdata(
                [(v, v, v) for v in (0, 64, 128, 192, 255)]
                + [(v, 0, 0) for v in (0, 64, 128, 192, 255)]
            )
            with ImageCms.profileToProfile(
                samples, source, target, outputMode="RGB"
            ) as result:
                for index, value in enumerate(expected):
                    assert all(
                        abs(channel - value) <= 1
                        for channel in result.getpixel((index, 0))
                    )
                    red, green, blue = result.getpixel((index + 5, 0))
                    assert abs(red - value) <= 1 and max(green, blue) <= 1
    assert abs(hlg_decode(0.5) - 1 / 12) < 1e-8
    assert abs(pq_decode(0.5080784215) - 0.01) < 1e-8
    assert abs(pq_decode(0.7518270962) - 0.1) < 1e-8
    return "Independent analytical HLG/PQ neutral and red anchors match within one 8-bit code; PQ100/1000-nit anchors map to 0.01/0.1 relative light; source primaries remain BT.2020."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--orientation-reference", type=Path)
    args = parser.parse_args()
    pillow_heif.register_heif_opener(
        thumbnails=False, depth_images=False, aux_images=False
    )
    paths = fetch_fixtures(args.fixtures)
    results = []
    for name, status, probe in (
        ("primary-and-sequence-fixtures", "PASS", lambda: primary_and_sequence(paths)),
        ("high-bit-depth-and-alpha", "PASS", lambda: bit_depth_and_alpha(paths)),
        ("orientation-and-compatible-icc", "PASS", lambda: orientation_and_icc(paths)),
        ("imagecms-mode-transform", "PASS", mode_transform),
        ("nclx-preservation", "PASS", lambda: nclx_preservation(paths)),
        ("png-color-preservation", "PASS", png_color_preservation),
        ("hlg-sdr-color-conversion", "PASS", lambda: hlg_color_conversion(paths)),
        ("analytical-hlg-pq-transfers", "PASS", analytical_transfer_checks),
    ):
        results.append({"case": name, "status": status, "evidence": probe()})
    if args.orientation_reference:
        results.append(
            {
                "case": "independent-orientation-oracle",
                "status": "PASS",
                "evidence": orientation_reference(paths, args.orientation_reference),
                "reference_sha256": hashlib.sha256(
                    args.orientation_reference.read_bytes()
                ).hexdigest(),
            }
        )
    else:
        results.append(
            {
                "case": "independent-orientation-oracle",
                "status": "BLOCKED",
                "evidence": "Pass an Apple ImageIO/sips PNG decode of the pinned arrow.heic fixture.",
            }
        )
    print(
        json.dumps(
            {
                "platform": platform.platform(),
                "architecture": platform.machine(),
                "python": platform.python_version(),
                "pillow": PIL.__version__,
                "pillow_heif": pillow_heif.__version__,
                "libheif": pillow_heif.libheif_info(),
                "littlecms": _imagingcms.littlecms_version,
                "fixtures": {
                    name: {"url": url, "sha256": digest}
                    for name, (url, digest) in FIXTURES.items()
                },
                "results": results,
                "scope": "color-feasibility",
                "gate": "PASS"
                if all(result["status"] == "PASS" for result in results)
                else "OPEN",
            },
            indent=2,
        )
    )
    return int(any(result["status"] != "PASS" for result in results))


if __name__ == "__main__":
    sys.exit(main())
