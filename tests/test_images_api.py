import asyncio
from contextlib import ExitStack
from tempfile import SpooledTemporaryFile

import pytest
from fastapi import HTTPException
from starlette.requests import ClientDisconnect, Request

from backend import main


def multipart(parts):
    chunks = []
    for name, value, filename in parts:
        disposition = f'form-data; name="{name}"'
        if filename is not None:
            disposition += f'; filename="{filename}"'
        chunks.append(
            f"--test\r\nContent-Disposition: {disposition}\r\n\r\n".encode()
            + value
            + b"\r\n"
        )
    return b"".join(chunks) + b"--test--\r\n"


def request(body, ending=None, content_type="multipart/form-data; boundary=test"):
    position = 0

    async def receive():
        nonlocal position
        if position >= len(body) and ending:
            if ending == "disconnect":
                return {"type": "http.disconnect"}
            raise asyncio.CancelledError()
        chunk = body[position : position + 65536]
        position += len(chunk)
        return {
            "type": "http.request",
            "body": chunk,
            "more_body": position < len(body) or bool(ending),
        }

    return Request(
        {"type": "http", "headers": [(b"content-type", content_type.encode())]},
        receive,
    )


@pytest.fixture
def handles(monkeypatch):
    opened = []
    with ExitStack() as stack:

        def spool(*args, **kwargs):
            handle = stack.enter_context(SpooledTemporaryFile(*args, **kwargs))
            opened.append(handle)
            return handle

        monkeypatch.setattr("starlette.formparsers.SpooledTemporaryFile", spool)
        yield opened
        assert all(handle.closed for handle in opened)


@pytest.mark.parametrize(
    "fields,expected",
    [
        ([("output_format", "png")], (None, None, "png")),
        ([("max_width", "1200")], (1200, None, "jpeg")),
        ([("max_height", "300")], (None, 300, "jpeg")),
        ([("max_width", ""), ("output_format", "webp")], (None, None, "webp")),
        ([("max_width", "9" * 1024)], (int("9" * 1024), None, "jpeg")),
    ],
)
@pytest.mark.parametrize(
    "content_type",
    ["multipart/form-data; boundary=test", "Multipart/Form-Data; boundary=test"],
)
def test_parameters(fields, expected, handles, content_type):
    async def check():
        parts = [("file", b"image", "private.png")]
        parts += [(name, value.encode(), None) for name, value in fields]
        upload, width, height, output_format = await main.parse_image_request(
            request(multipart(parts), content_type=content_type)
        )
        try:
            assert (width, height, output_format) == expected
            assert await upload.read() == b"image"
        finally:
            await upload.close()

    asyncio.run(check())


@pytest.mark.parametrize(
    "parts,status",
    [
        ([("output_format", b"png", None)], 422),
        ([("file", b"", "private.png"), ("output_format", b"png", None)], 422),
        ([("file", b"image", "private.png")], 422),
        ([("file", b"image", "private.png"), ("max_width", b"", None)], 422),
        *[
            ([("file", b"image", "private.png"), ("max_width", value, None)], 422)
            for value in (b"0", b"-1", b"1.5", b"1e3", b"nan", b" 1", b"+1")
        ],
        *[
            ([("file", b"image", "private.png"), ("output_format", value, None)], 422)
            for value in (b"", b"gif", b"JPEG")
        ],
        ([("file", b"image", "private.png"), ("file", b"other", "other.png")], 422),
        (
            [
                ("file", b"image", "private.png"),
                ("max_width", b"1", None),
                ("max_width", b"2", None),
            ],
            422,
        ),
        ([("file", b"image", "private.png"), ("unknown", b"x", None)], 422),
        ([("file", b"image", None), ("output_format", b"png", None)], 422),
    ],
)
def test_parameter_rejections(parts, status, handles):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.parse_image_request(request(multipart(parts))))
    assert caught.value.status_code == status
    assert "private.png" not in str(caught.value.detail)


@pytest.mark.parametrize("size", [19_999_999, 20_000_000, 20_000_001])
def test_file_byte_boundary(size, handles):
    body = multipart(
        [("file", b"x" * size, "private.png"), ("output_format", b"png", None)]
    )

    async def check():
        if size > 20_000_000:
            with pytest.raises(HTTPException) as caught:
                await main.parse_image_request(request(body))
            assert caught.value.status_code == 413
        else:
            upload, *_ = await main.parse_image_request(request(body))
            assert upload.size == size
            await upload.close()

    asyncio.run(check())


@pytest.mark.parametrize("ending", [None, "disconnect", "cancel"])
def test_partial_upload_cleanup(ending, handles):
    body = multipart([("file", b"x" * 2_000_000, "private.png")])[:-12]
    error = {
        None: HTTPException,
        "disconnect": ClientDisconnect,
        "cancel": asyncio.CancelledError,
    }[ending]
    with pytest.raises(error) as caught:
        asyncio.run(main.parse_image_request(request(body, ending)))
    if ending is None:
        assert caught.value.status_code == 400
    assert handles


@pytest.mark.parametrize(
    "body,content_type,status",
    [
        (b"not multipart", "application/json", 415),
        (b"not multipart", "multipart/form-data", 400),
        (b"not multipart", "multipart/form-data; boundary=test", 400),
        (
            multipart([("max_width", b"9" * 1025, None)]),
            "multipart/form-data; boundary=test",
            413,
        ),
        (b"--test\r\n" + b"X" * 16385, "multipart/form-data; boundary=test", 413),
        (
            b"--test--\r\n" + b" " * 20_065_536,
            "multipart/form-data; boundary=test",
            413,
        ),
    ],
)
def test_transport_rejections(body, content_type, status, handles):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.parse_image_request(request(body, content_type=content_type)))
    assert caught.value.status_code == status
