"""Bounded HEIF timing probe; unresolved timelines are not production rejections."""

import argparse
import hashlib
import json
import platform
import struct
from pathlib import Path

MAX_BYTES = 20_000_000
PINS = {
    "zPug_3.heic": "daf1515c651e15968ad6ec142e443759156fee76c65715e4f5713cf1ad072774",
    "starfield_animation.heic": "fbf31cd9aa6fc4c997d7eb2ea05541627bf3dbcb4115b7d453f63dcd1ec4fb26",
}


def boxes(data):
    position = 0
    while position < len(data):
        if len(data) - position < 8:
            raise ValueError("Truncated box header")
        size, kind = struct.unpack_from(">I4s", data, position)
        header = 8
        if size == 1:
            if len(data) - position < 16:
                raise ValueError("Truncated extended box header")
            size = struct.unpack_from(">Q", data, position + 8)[0]
            header = 16
        elif size == 0:
            size = len(data) - position
        if kind == b"uuid":
            header += 16
        if size < header or size > len(data) - position:
            raise ValueError("Invalid box extent")
        yield kind, data[position + header : position + size]
        position += size


def one(data, kind, required=True):
    found = None
    for name, payload in boxes(data):
        if name == kind:
            if found is not None:
                raise ValueError("Duplicate required box")
            found = payload
    if required and found is None:
        raise ValueError("Missing required box")
    return found


def classify(data):
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Input byte limit")
    data = memoryview(data)
    if next(boxes(data))[0] != b"ftyp":
        raise ValueError("Missing initial ftyp")
    ftyp = one(data, b"ftyp")
    if len(ftyp) < 8 or len(ftyp) % 4:
        raise ValueError("Invalid brands")
    movie = one(data, b"moov", required=False)
    if any(kind == b"moof" for kind, _ in boxes(data)):
        return "NEEDS_TIMELINE"
    if movie is None:
        return "NO_TIMED_TRACKS"
    unresolved = False
    for kind, track in boxes(movie):
        if kind != b"trak":
            continue
        media = one(track, b"mdia")
        handler = one(media, b"hdlr")
        if len(handler) < 12:
            raise ValueError("Truncated handler")
        if bytes(handler[8:12]) not in (b"pict", b"vide", b"auxv"):
            continue
        table = one(one(media, b"minf"), b"stbl")
        timing = one(table, b"stts")
        if len(timing) < 8 or bytes(timing[:4]) != b"\0" * 4:
            raise ValueError("Invalid stts")
        entries = struct.unpack_from(">I", timing, 4)[0]
        if len(timing) != 8 + entries * 8:
            raise ValueError("Invalid stts entries")
        samples = 0
        valid_runs = True
        for count, delta in struct.iter_unpack(">II", timing[8:]):
            samples += count
            valid_runs &= count > 0 and delta > 0
        if not valid_runs:
            unresolved = True
            continue
        edits = one(track, b"edts", required=False)
        if edits is None and one(table, b"ctts", required=False) is None:
            if samples > 1:
                return "TIMED_SEQUENCE"
            continue
        if edits is not None:
            edit = one(edits, b"elst")
            if len(edit) < 8 or edit[0] not in (0, 1):
                raise ValueError("Invalid edit list")
            flags = int.from_bytes(edit[1:4])
            count = struct.unpack_from(">I", edit, 4)[0]
            width = 12 if edit[0] == 0 else 20
            if len(edit) != 8 + count * width:
                raise ValueError("Invalid edit entries")
            if flags == 0 and count == 0:
                continue
            if flags == 0 and count == 1 and bytes(edit[-4:]) == b"\0" * 4:
                continue
        unresolved = True
    return "NEEDS_TIMELINE" if unresolved else "NO_TIMED_TRACKS"


def box(kind, payload=b"", size_mode=32):
    if size_mode == 64:
        return struct.pack(">I4sQ", 1, kind, len(payload) + 16) + payload
    size = 0 if size_mode == 0 else len(payload) + 8
    return struct.pack(">I4s", size, kind) + payload


def control(edits=None, handler=b"pict", samples=3):
    ftyp = box(b"ftyp", b"heic\0\0\0\0msf1hevc")
    hdlr = box(b"hdlr", b"\0" * 8 + handler + b"\0" * 12)
    stts = box(b"stts", struct.pack(">IIII", 0, 1, samples, 40))
    mdia = box(b"mdia", hdlr + box(b"minf", box(b"stbl", stts)))
    track = mdia if edits is None else mdia + box(b"edts", edits)
    return ftyp + box(b"meta", b"\0" * 4) + box(b"moov", box(b"trak", track))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    results = []

    def check(name, data, expected):
        actual = classify(data)
        assert actual == expected, (name, actual, expected)
        results.append({"case": name, "classification": actual, "outcome": "PASS"})

    fixtures = {}
    for name, digest in PINS.items():
        data = (args.fixtures / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, name
        fixtures[name] = data
    check(
        "Real three-item non-first-primary collection",
        fixtures["zPug_3.heic"],
        "NO_TIMED_TRACKS",
    )
    sequence = fixtures["starfield_animation.heic"]
    check("Real Nokia 120-frame timed sequence", sequence, "TIMED_SEQUENCE")
    spoofed = bytearray(sequence)
    spoofed[8:12] = b"heic"
    check("Real sequence with static major brand", spoofed, "TIMED_SEQUENCE")
    ftyp_size = struct.unpack_from(">I", spoofed)[0]
    for position in range(16, ftyp_size, 4):
        spoofed[position : position + 4] = b"mif1"
    check("Real sequence with all sequence brands removed", spoofed, "TIMED_SEQUENCE")
    check(
        "Analytic non-timed gallery: empty edit list",
        control(box(b"elst", b"\0" * 8)),
        "NO_TIMED_TRACKS",
    )
    dwell = box(b"elst", struct.pack(">IIIihh", 0, 1, 1000, 0, 0, 0))
    check(
        "Analytic non-timed gallery: one dwell edit", control(dwell), "NO_TIMED_TRACKS"
    )
    forward = box(b"elst", struct.pack(">IIIihh", 0, 1, 1000, 0, 1, 0))
    check("General forward edit needs timeline", control(forward), "NEEDS_TIMELINE")
    check("Analytic timed sequence", control(), "TIMED_SEQUENCE")
    check(
        "Analytic non-visual track does not make an animation",
        control(handler=b"soun"),
        "NO_TIMED_TRACKS",
    )
    check("Analytic single-sample visual track", control(samples=1), "NO_TIMED_TRACKS")
    for mode in (32, 64, 0):
        data = box(b"ftyp", b"heic\0\0\0\0mif1") + box(b"free", b"moov", mode)
        check(
            f"Box size{mode}; payload text is not a movie box", data, "NO_TIMED_TRACKS"
        )
    for name, data in (
        ("Short header", b"1234567"),
        ("Short extended header", struct.pack(">I4s", 1, b"ftyp")),
        ("Box smaller than header", struct.pack(">I4s", 7, b"ftyp")),
        ("Extended size overflow", struct.pack(">I4sQ", 1, b"ftyp", 2**64 - 1)),
        ("Missing uuid extension", struct.pack(">I4s", 8, b"uuid")),
        ("Truncated payload", struct.pack(">I4s", 30, b"ftyp") + b"12345678"),
        ("Trailing short header", fixtures["zPug_3.heic"] + b"x"),
        ("Oversized input", b"x" * (MAX_BYTES + 1)),
    ):
        try:
            classify(data)
        except ValueError:
            results.append(
                {"case": name, "outcome": "PASS", "classification": "MALFORMED"}
            )
        else:
            raise AssertionError(name)
    print(
        json.dumps(
            {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "results": results,
                "mechanism": "PASS: timed tracks distinguished from still collections and non-timed controls",
                "coverage": "Partial inspector; NEEDS_TIMELINE is neither a static verdict nor an animated verdict",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
