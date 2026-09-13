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
        ([("output_format", "png")], (None, None, "png", None)),
        ([("max_width", "1200")], (1200, None, "jpeg", None)),
        ([("max_height", "300")], (None, 300, "jpeg", None)),
        ([("max_width", ""), ("output_format", "webp")], (None, None, "webp", None)),
        ([("max_width", "9" * 1024)], (int("9" * 1024), None, "jpeg", None)),
        ([("size_limit", ""), ("max_width", "1200")], (1200, None, "jpeg", None)),
        ([("size_limit", ""), ("size_unit", "kb"), ("output_format", "png")], (None, None, "png", None)),
        ([("size_limit", "0.5"), ("size_unit", "mb")], (None, None, "jpeg", 524_288)),
        ([("size_limit", "200"), ("size_unit", "kb")], (None, None, "jpeg", 204_800)),
        (
            [("size_limit", "0.5"), ("size_unit", "mb"), ("max_width", "1200")],
            (1200, None, "jpeg", 524_288),
        ),
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
        upload, width, height, output_format, size_limit_bytes = (
            await main.parse_image_request(
                request(multipart(parts), content_type=content_type)
            )
        )
        try:
            assert (width, height, output_format, size_limit_bytes) == expected
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
        *[
            ([("file", b"image", "private.png"), ("size_limit", value, None), ("size_unit", b"mb", None)], 422)
            for value in (b"0", b"-1", b"abc", b"1e3", b"nan")
        ],
        ([("file", b"image", "private.png"), ("size_limit", b"0.5", None)], 422),
        ([("file", b"image", "private.png"), ("size_limit", b"0.5", None), ("size_unit", b"gb", None)], 422),
        ([("file", b"image", "private.png"), ("size_unit", b"mb", None)], 422),
    ],
)
def test_parameter_rejections(parts, status, handles):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.parse_image_request(request(multipart(parts))))
    assert caught.value.status_code == status
    assert "private.png" not in str(caught.value.detail)


@pytest.mark.parametrize(
    "fields,detail",
    [
        ([("size_limit", "0"), ("size_unit", "mb")], "size_limit must be a positive number with mb or kb or left empty."),
        ([("size_limit", "-1"), ("size_unit", "kb")], "size_limit must be a positive number with mb or kb or left empty."),
        ([("size_limit", "nope"), ("size_unit", "mb")], "size_limit must be a positive number with mb or kb or left empty."),
        ([("size_limit", "0.5")], "size_limit requires size_unit mb or kb."),
        ([("size_limit", "0.5"), ("size_unit", "gb")], "size_unit must be mb or kb."),
        ([], "Supply dimensions, an output format or a size limit."),
    ],
)
def test_size_limit_rejection_copy(fields, detail, handles):
    parts = [("file", b"image", "private.png")]
    parts += [(name, value.encode(), None) for name, value in fields]
    with pytest.raises(HTTPException) as caught:
        asyncio.run(main.parse_image_request(request(multipart(parts))))
    assert caught.value.status_code == 422
    assert caught.value.detail == detail


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


def valid_image(format="PNG", size=(12, 8), color="red"):
    import io

    from PIL import Image

    with Image.new("RGB", size, color) as image, io.BytesIO() as output:
        image.save(output, format=format)
        return output.getvalue()


@pytest.mark.parametrize("input_format", ["JPEG", "PNG", "WEBP", "HEIF"])
@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_processing_endpoint(input_format, output_format, handles):
    import io

    import httpx
    from PIL import Image

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={
                    "file": ("private.gif", valid_image(input_format), "text/plain")
                },
                data={"output_format": output_format, "max_width": "6"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/" + output_format
        extension = "jpg" if output_format == "jpeg" else output_format
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="result.{extension}"'
        )
        with Image.open(io.BytesIO(response.content)) as image:
            assert image.size == (6, 4) and image.format == output_format.upper()

    asyncio.run(check())


def test_size_limit_only_jpeg_is_enough_to_process(handles):
    import io

    import httpx
    from PIL import Image

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={"file": ("input.png", valid_image(), "image/png")},
                data={"size_limit": "0.5", "size_unit": "mb"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        with Image.open(io.BytesIO(response.content)) as image:
            assert image.format == "JPEG"
            assert len(response.content) <= 524_288

    asyncio.run(check())


@pytest.mark.parametrize("data,status", [(b"bad", 422), (valid_image("BMP"), 415)])
def test_content_rejection_is_safe(data, status, handles, caplog):
    import httpx

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={"file": ("private.png", data)},
                data={"output_format": "png"},
            )
        assert response.status_code == status
        assert isinstance(response.json()["detail"], str)
        assert "private" not in response.text + caplog.text

    asyncio.run(check())


def test_parser_diagnostics_are_private(caplog):
    import httpx

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                content=b"x",
                headers={"content-type": "multipart/form-data; boundary=test"},
            )
        assert response.status_code == 400
        assert not caplog.text

    asyncio.run(check())


@pytest.mark.parametrize("failure", [None, "decode", "encode"])
def test_processing_cleanup_and_safe_failures(failure, handles, monkeypatch, caplog):
    import httpx

    if failure:

        def fail(*args, **kwargs):
            raise RuntimeError("Private filename and decoder internals")

        monkeypatch.setattr(main.images, "process_image", fail)

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={"file": ("private.png", valid_image())},
                data={"output_format": "png"},
            )
        assert response.status_code == (500 if failure else 200)
        assert "Private" not in response.text + caplog.text if failure else True

    asyncio.run(check())


def test_raw_cancellation_keeps_worker_source_open(handles, monkeypatch):
    import threading

    started, release, finished = threading.Event(), threading.Event(), threading.Event()
    real = main.images.process_image
    observed = []

    def processing(source, *args):
        started.set()
        try:
            assert release.wait(5)
            observed.append(source.closed)
            return real(source, *args)
        finally:
            finished.set()

    monkeypatch.setattr(main.images, "process_image", processing)

    async def check():
        body = multipart(
            [("file", valid_image(), "private.png"), ("output_format", b"png", None)]
        )
        task = asyncio.create_task(main.process_image(request(body)))
        try:
            async with asyncio.timeout(5):
                while not started.is_set():
                    await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert handles and not handles[0].closed
        finally:
            release.set()
        async with asyncio.timeout(5):
            while not finished.is_set() or not all(handle.closed for handle in handles):
                await asyncio.sleep(0.001)
        assert observed == [False]

    asyncio.run(check())


@pytest.mark.parametrize("failure", [None, "send", "cancel"])
def test_response_releases_body(failure):
    response = main.ImageResponse(b"private image", media_type="image/png")

    async def send(message):
        if message["type"] == "http.response.body":
            if failure == "send":
                raise OSError("disconnected")
            if failure == "cancel":
                raise asyncio.CancelledError()
            assert message["body"] == b"private image"

    async def check():
        try:
            await response({"type": "http"}, None, send)
        except OSError, asyncio.CancelledError:
            assert failure
        assert response.body == b""

    asyncio.run(check())


def test_socket_disconnect_during_upload_and_processing(handles, monkeypatch):
    import socket
    import threading

    import uvicorn

    started, release, finished = threading.Event(), threading.Event(), threading.Event()
    real = main.images.process_image
    observed = []

    def processing(source, *args):
        started.set()
        try:
            assert release.wait(5)
            observed.append(source.closed)
            return real(source, *args)
        finally:
            finished.set()

    monkeypatch.setattr(main.images, "process_image", processing)

    async def check():
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            server = uvicorn.Server(
                uvicorn.Config(
                    main.app, log_level="critical", access_log=False, lifespan="off"
                )
            )
            task = asyncio.create_task(server.serve(sockets=[listener]))
            try:
                async with asyncio.timeout(5):
                    while not server.started:
                        await asyncio.sleep(0.001)
                    for partial in (True, False):
                        _, writer = await asyncio.open_connection("127.0.0.1", port)
                        body = multipart(
                            [
                                (
                                    "file",
                                    b"x" * 2_000_000 if partial else valid_image(),
                                    "private.png",
                                ),
                                ("output_format", b"png", None),
                            ]
                        )
                        size = len(body) + (1000 if partial else 0)
                        writer.write(
                            f"POST /api/v1/images/process HTTP/1.1\r\nHost: localhost\r\nContent-Type: multipart/form-data; boundary=test\r\nContent-Length: {size}\r\n\r\n".encode()
                            + body
                        )
                        await writer.drain()
                        if not partial:
                            while not started.is_set():
                                await asyncio.sleep(0.001)
                        writer.close()
                        await writer.wait_closed()
                        if partial:
                            while not handles or not all(
                                handle.closed for handle in handles
                            ):
                                await asyncio.sleep(0.001)
                        else:
                            assert not handles[-1].closed
                            release.set()
                            while not finished.is_set() or not all(
                                handle.closed for handle in handles
                            ):
                                await asyncio.sleep(0.001)
                            assert observed == [False]
            finally:
                release.set()
                server.should_exit = True
                await task

    asyncio.run(check())


def test_real_encoder_failure_is_internal_error(monkeypatch, handles):
    import httpx
    from PIL import Image

    data = valid_image()

    def fail(*args, **kwargs):
        raise OSError("private encoder failure")

    monkeypatch.setattr(Image.Image, "save", fail)

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={"file": ("private.png", data)},
                data={"output_format": "png"},
            )
        assert response.status_code == 500
        assert "private" not in response.text

    asyncio.run(check())


@pytest.mark.parametrize("output_format", ["jpeg", "png", "webp"])
def test_sixteen_bit_png_retains_midgray(output_format):
    import io
    import struct

    import httpx
    from PIL import Image

    with (
        Image.frombytes("I;16", (1, 1), struct.pack("<H", 32768)) as image,
        io.BytesIO() as buffer,
    ):
        image.save(buffer, format="PNG")
        data = buffer.getvalue()

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={"file": ("gray.png", data)},
                data={"output_format": output_format},
            )
        assert response.status_code == 200
        with Image.open(io.BytesIO(response.content)) as result:
            assert all(abs(channel - 128) <= 1 for channel in result.getpixel((0, 0)))

    asyncio.run(check())


@pytest.mark.parametrize("width,output_format", [(16_384, "webp"), (65_501, "jpeg")])
def test_output_format_limit_returns_actionable_error(width, output_format):
    import httpx

    data = valid_image(size=(width, 1))
    assert len(data) < 20_000_000

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/images/process",
                files={"file": ("wide.png", data)},
                data={"output_format": output_format},
            )
        assert response.status_code == 422
        assert "Reduce" in response.json()["detail"]

    asyncio.run(check())


@pytest.mark.parametrize("limit,output_format", [(16_383, "webp"), (65_500, "jpeg")])
@pytest.mark.parametrize("axis", [0, 1])
def test_encoder_boundary_and_explicit_resize(limit, output_format, axis, handles):
    import io

    import httpx
    from PIL import Image

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            for extra in (0, 1):
                size = [1, 1]
                size[axis] = limit + extra
                fields = {"output_format": output_format}
                if extra:
                    fields["max_width" if axis == 0 else "max_height"] = str(limit)
                response = await client.post(
                    "/api/v1/images/process",
                    files={"file": ("wide.png", valid_image(size=tuple(size)))},
                    data=fields,
                )
                assert response.status_code == 200
                with Image.open(io.BytesIO(response.content)) as result:
                    assert result.size[axis] == limit

    asyncio.run(check())
