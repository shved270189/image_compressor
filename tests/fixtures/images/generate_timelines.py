import struct
import subprocess
import tempfile
from pathlib import Path

DIRECTORY = Path(__file__).parent


def box(kind, payload):
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def parts(data):
    position = 0
    while position < len(data):
        length, kind = struct.unpack_from(">I4s", data, position)
        yield kind, data[position + 8 : position + length]
        position += length


def relocate_movie(data, shift, gallery):
    result = []
    for kind, payload in parts(data):
        if kind in {b"trak", b"mdia", b"minf", b"stbl"}:
            payload = relocate_movie(payload, shift, gallery)
            if kind == b"trak" and gallery:
                payload = b"".join(box(k, p) for k, p in parts(payload) if k != b"edts")
                payload += box(b"edts", box(b"elst", b"\0" * 8))
        elif kind == b"stco":
            payload = payload[:8] + b"".join(
                struct.pack(">I", value[0] + shift)
                for value in struct.iter_unpack(">I", payload[8:])
            )
        result.append(box(kind, payload))
    return b"".join(result)


def main():
    with tempfile.TemporaryDirectory() as directory:
        movie = Path(directory) / "movie.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=32x32:rate=2",
                "-frames:v",
                "3",
                "-c:v",
                "libx265",
                "-x265-params",
                "log-level=error:pools=1",
                "-tag:v",
                "hvc1",
                "-movflags",
                "default_base_moof+frag_every_frame+skip_trailer",
                str(movie),
            ],
            check=True,
        )
        tracks = list(parts(movie.read_bytes()))
        primary = (DIRECTORY / "RGB_10__128x128.heif").read_bytes()
        for name, gallery in (
            ("fragmented-sequence.heic", False),
            ("fragmented-gallery.heic", True),
        ):
            data = primary
            for kind, payload in tracks:
                if kind == b"ftyp":
                    continue
                if kind == b"moov":
                    extra = len(relocate_movie(payload, 0, gallery)) - len(payload)
                    shift = len(primary) - (len(tracks[0][1]) + 8) + extra
                    payload = relocate_movie(payload, shift, gallery)
                data += box(kind, payload)
            (DIRECTORY / name).write_bytes(data)


if __name__ == "__main__":
    main()
