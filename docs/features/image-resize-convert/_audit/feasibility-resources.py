"""Isolated resource feasibility probe; not the production image endpoint."""

import asyncio
import gc
import io
import json
import os
import platform
import socket
import threading
import weakref
from importlib.metadata import version
from unittest.mock import patch

import anyio
import anyio.lowlevel
import uvicorn
from fastapi import FastAPI, Request
from PIL import Image
from starlette.datastructures import Headers
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.requests import ClientDisconnect
from starlette.responses import Response, StreamingResponse

MAX_BYTES = 20_000_000
MAX_PIXELS = 40_000_000
MAX_ENVELOPE_BYTES = MAX_BYTES + 65_536
MAX_HEADER_BYTES = 16_384
HEAD = b'--probe\r\nContent-Disposition: form-data; name="file"; filename="private.png"\r\n\r\n'
TAIL = b"\r\n--probe--\r\n"
HEADERS = Headers({"content-type": "multipart/form-data; boundary=probe"})
RESULTS = []


async def bounded_stream(source):
    size = 0
    async for chunk in source:
        size += len(chunk)
        if size > MAX_ENVELOPE_BYTES:
            raise MultiPartException("Multipart envelope exceeds resource budget.")
        yield chunk


class BoundedParser(MultiPartParser):
    complete = False
    file_bytes = 0
    header_bytes = 0

    def __init__(self, headers, source):
        super().__init__(
            headers,
            bounded_stream(source),
            max_files=1,
            max_fields=3,
            max_part_size=1024,
        )

    def on_header_field(self, data, start, end):
        self.header_bytes += end - start
        if self.header_bytes > MAX_HEADER_BYTES:
            raise MultiPartException("Multipart headers exceed resource budget.")
        super().on_header_field(data, start, end)

    def on_header_value(self, data, start, end):
        self.header_bytes += end - start
        if self.header_bytes > MAX_HEADER_BYTES:
            raise MultiPartException("Multipart headers exceed resource budget.")
        super().on_header_value(data, start, end)

    def on_part_data(self, data, start, end):
        if self._current_part.file is not None:
            self.file_bytes += end - start
            if self.file_bytes > MAX_BYTES:
                raise MultiPartException("Input exceeds 20000000 bytes.")
        super().on_part_data(data, start, end)

    def on_end(self):
        self.complete = True

    async def parse(self):
        try:
            form = await super().parse()
            if not self.complete:
                raise MultiPartException("Malformed multipart request.")
            return form
        except BaseException:
            for handle in self._files_to_close_on_error:
                handle.close()
            raise


async def stream(size, ending="complete"):
    yield HEAD
    remaining = size
    while remaining:
        count = min(remaining, 65536)
        yield b"x" * count
        remaining -= count
    if ending == "disconnect":
        raise ClientDisconnect()
    if ending == "cancel":
        raise asyncio.CancelledError()
    if ending == "complete":
        yield TAIL


def record(case, outcome="PASS"):
    RESULTS.append({"case": case, "outcome": outcome})


async def parsing():
    raw = MultiPartParser(HEADERS, stream(2_000_000, "eof"))
    form = await raw.parse()
    assert not form and len(raw._files_to_close_on_error) == 1
    assert not raw._files_to_close_on_error[0].closed
    raw._files_to_close_on_error[0].close()
    record(
        "stock parser accepts truncated EOF and leaves partial spool open",
        "CONFIRMED GAP",
    )
    for parser_type in (MultiPartParser, BoundedParser):
        for ending in ("disconnect", "cancel"):
            parser = parser_type(HEADERS, stream(2_000_000, ending))
            try:
                await parser.parse()
                raise AssertionError("Interruption accepted")
            except ClientDisconnect, asyncio.CancelledError:
                pass
            assert parser._files_to_close_on_error
            assert all(f.closed for f in parser._files_to_close_on_error)
            record(f"{parser_type.__name__}: {ending} closes rolled upload")
    for size, ending, accepted in (
        (MAX_BYTES, "complete", True),
        (MAX_BYTES + 1, "complete", False),
        (2_000_000, "eof", False),
    ):
        parser = BoundedParser(HEADERS, stream(size, ending))
        try:
            form = await parser.parse()
            assert accepted
            upload = form["file"]
            assert upload.size == size and upload.file._rolled
            descriptor = upload.file.fileno()
            await form.close()
            try:
                os.fstat(descriptor)
                raise AssertionError("Descriptor remains open")
            except OSError:
                pass
        except MultiPartException:
            assert not accepted
        assert all(f.closed for f in parser._files_to_close_on_error)
        record(f"candidate: {size} file bytes, {ending}; handles closed")


async def envelope_limits():
    async def request_body(extra=None):
        async for chunk in stream(MAX_BYTES, "eof"):
            yield chunk
        for name, value in (
            ("max_width", "9" * 1024),
            ("max_height", "1"),
            ("output_format", "png"),
        ):
            yield (
                f'\r\n--probe\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}'
            ).encode()
        if extra == "header":
            yield (
                b'\r\n--probe\r\nContent-Disposition: form-data; name="'
                + b"z" * MAX_HEADER_BYTES
            )
        elif extra == "envelope":
            yield TAIL + b" " * 65_536
        elif extra == "field":
            yield b'\r\n--probe\r\nContent-Disposition: form-data; name="extra"\r\n\r\nx'
        else:
            yield TAIL

    for extra in (None, "header", "envelope", "field"):
        parser = BoundedParser(HEADERS, request_body(extra))
        try:
            form = await parser.parse()
            assert extra is None
            assert form["file"].size == MAX_BYTES
            assert form["max_width"] == "9" * 1024
            assert form["max_height"] == "1" and form["output_format"] == "png"
            await form.close()
        except MultiPartException:
            assert extra is not None
        assert parser._files_to_close_on_error and all(
            f.closed for f in parser._files_to_close_on_error
        )
        record(
            f"bounded envelope with exact-limit upload: {extra or 'three scalars accepted'}; spool closed"
        )


def pixel_limits():
    for dimensions, accepted in (((8000, 5000), True), ((1, 40_000_001), False)):
        header = b"P6\n%d %d\n255\n" % dimensions
        calls = []
        with (
            io.BytesIO(header) as source,
            Image.open(source) as image,
            patch.object(
                image, "load", side_effect=lambda calls=calls: calls.append(True)
            ),
        ):
            allowed = image.width * image.height <= MAX_PIXELS
            if allowed:
                image.load()
            assert allowed == accepted and bool(calls) == accepted
        record(f"pixel header gate: {dimensions}, decode called={accepted}")
    record(
        "pixel probe uses real Pillow header parsing and load spy; no 40M-pixel decode claimed"
    )


def processing(source, refs, fail=None):
    with Image.open(source) as image:
        refs.append(weakref.ref(image))
        image.load()
        with image.copy() as intermediate, io.BytesIO() as output:
            refs.extend([weakref.ref(intermediate), weakref.ref(output)])
            if fail == "encode":
                intermediate.save(output, format="NONEXISTENT")
            intermediate.save(output, format="PNG")
            return output.getvalue()


async def lifecycle():
    with io.BytesIO() as seed:
        with Image.new("RGB", (8, 8), "red") as image:
            image.save(seed, format="PNG")
        valid = seed.getvalue()
    for failure in (None, "decode", "encode", "response", "response_cancel"):
        refs = []

        async def upload_stream(failure=failure):
            yield HEAD
            yield b"bad" if failure == "decode" else valid
            yield TAIL

        form = await BoundedParser(HEADERS, upload_stream()).parse()
        source = form["file"].file
        response_ref = None
        try:
            with source:
                output = await anyio.to_thread.run_sync(
                    processing, source, refs, failure
                )
            response = Response(output, media_type="image/png")
            response_ref = weakref.ref(response)
            del output

            async def send(message, failure=failure):
                if message["type"] == "http.response.body":
                    if failure == "response":
                        raise OSError("Transfer interrupted")
                    if failure == "response_cancel":
                        raise asyncio.CancelledError()
                    with Image.open(io.BytesIO(message["body"])) as decoded:
                        assert decoded.size == (8, 8)

            try:
                await response({"type": "http"}, None, send)
            finally:
                del response
        except OSError, KeyError, asyncio.CancelledError:
            assert failure is not None
        else:
            assert failure is None
        await form.close()
        assert source.closed
        with anyio.fail_after(2):
            while any(ref() is not None for ref in refs):
                gc.collect()
                await anyio.sleep(0.01)
        assert response_ref is None or response_ref() is None
        record(
            f"processing/response {failure or 'success'}: closed upload, no image/output/response owners"
        )


async def native_cancellation():
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    owner_closed = anyio.Event()
    source = io.BytesIO(b"owned")

    def work():
        started.set()
        assert release.wait(5), "Test release did not arrive"
        assert not source.closed and source.read() == b"owned"
        finished.set()

    async def owner(scope):
        with scope:
            try:
                await anyio.to_thread.run_sync(work, abandon_on_cancel=False)
            finally:
                assert finished.is_set()
                source.close()
                owner_closed.set()

    scope = anyio.CancelScope()
    async with anyio.create_task_group() as group:
        group.start_soon(owner, scope)
        while not started.is_set():
            await anyio.lowlevel.checkpoint()
        scope.cancel()
        await anyio.sleep(0.02)
        assert not source.closed and not owner_closed.is_set()
        release.set()
    assert source.closed and finished.is_set()
    record(
        "AnyIO cancellation retains upload owner until non-abandoning worker finishes"
    )


async def raw_cancellation():
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    source = io.BytesIO(b"owned")
    observed = []

    def work():
        started.set()
        assert release.wait(5)
        observed.append(source.closed)
        finished.set()

    async def owner():
        try:
            await anyio.to_thread.run_sync(work, abandon_on_cancel=False)
        finally:
            source.close()

    task = asyncio.create_task(owner())
    while not started.is_set():
        await anyio.lowlevel.checkpoint()
    task.cancel()
    await anyio.sleep(0.02)
    assert source.closed
    release.set()
    try:
        await task
    except asyncio.CancelledError:
        pass
    while not finished.is_set():
        await anyio.lowlevel.checkpoint()
    assert observed == [True]
    record(
        "raw Task.cancel: AnyIO alone releases caller-owned source before worker ends",
        "CONFIRMED GAP",
    )


async def worker_owned_cancellation():
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    refs = []
    with io.BytesIO() as seed, Image.new("RGB", (32, 32), "red") as image:
        image.save(seed, format="PNG")
        source = io.BytesIO(seed.getvalue())

    def work():
        try:
            with source:
                started.set()
                assert release.wait(5)
                assert not source.closed
                return processing(source, refs)
        finally:
            finished.set()

    task = asyncio.create_task(anyio.to_thread.run_sync(work))
    while not started.is_set():
        await anyio.lowlevel.checkpoint()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert not source.closed and not finished.is_set()
    release.set()
    with anyio.fail_after(2):
        while not finished.is_set() or any(ref() is not None for ref in refs):
            gc.collect()
            await anyio.sleep(0.01)
    assert source.closed and refs
    record(
        "raw Task.cancel with worker-owned source: Pillow work finishes and closes upload/images/output without caller shield"
    )


async def sockets():
    app = FastAPI()
    parsed = anyio.Event()
    sent = anyio.Event()
    handles = []
    refs = []
    native_started = threading.Event()
    native_release = threading.Event()
    native_finished = threading.Event()
    native_disconnected = anyio.Event()
    native_refs = []
    native_handles = []

    @app.post("/native")
    async def native(request: Request):
        form = await BoundedParser(HEADERS, request.stream()).parse()
        source = form["file"].file
        native_handles.append(source)

        def work():
            try:
                with source:
                    native_started.set()
                    assert native_release.wait(5)
                    assert not source.closed
                    return processing(source, native_refs)
            finally:
                native_finished.set()

        async def observe_disconnect():
            assert (await request.receive())["type"] == "http.disconnect"
            native_disconnected.set()

        observer = asyncio.create_task(observe_disconnect())
        try:
            output = await anyio.to_thread.run_sync(work)
            response = Response(output, media_type="image/png")
            native_refs.append(weakref.ref(response))
            return response
        finally:
            await observer

    @app.post("/upload")
    async def upload(request: Request):
        parser = BoundedParser(HEADERS, request.stream())
        try:
            form = await parser.parse()
            await form.close()
        except ClientDisconnect:
            pass
        finally:
            handles.extend(parser._files_to_close_on_error)
            parsed.set()
        return Response(status_code=400)

    @app.get("/result")
    async def result():
        async def chunks():
            with io.BytesIO(b"x" * 65536) as output:
                refs.append(weakref.ref(output))
                try:
                    for _ in range(10000):
                        yield output.getvalue()
                        await anyio.lowlevel.checkpoint()
                finally:
                    sent.set()

        return StreamingResponse(chunks(), media_type="application/octet-stream")

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, log_level="critical", access_log=False, lifespan="off")
    )
    server_task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        with anyio.fail_after(5):
            while not server.started:
                await anyio.lowlevel.checkpoint()
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                b"POST /upload HTTP/1.1\r\nHost: localhost\r\nContent-Type: multipart/form-data; boundary=probe\r\nContent-Length: 10000000\r\n\r\n"
                + HEAD
                + b"x" * 2_000_000
            )
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            await parsed.wait()
            assert handles and all(handle.closed for handle in handles)
            record("loopback Uvicorn interrupted multipart closes partial spool")
            with io.BytesIO() as seed, Image.new("RGB", (32, 32), "red") as image:
                image.save(seed, format="PNG")
                body = HEAD + seed.getvalue() + TAIL
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                f"POST /native HTTP/1.1\r\nHost: localhost\r\nContent-Type: multipart/form-data; boundary=probe\r\nContent-Length: {len(body)}\r\n\r\n".encode()
                + body
            )
            await writer.drain()
            while not native_started.is_set():
                await anyio.lowlevel.checkpoint()
            writer.close()
            await writer.wait_closed()
            await native_disconnected.wait()
            assert (
                native_handles
                and not native_handles[0].closed
                and not native_finished.is_set()
            )
            native_release.set()
            while (
                not native_finished.is_set()
                or not native_refs
                or any(ref() is not None for ref in native_refs)
            ):
                gc.collect()
                await anyio.sleep(0.01)
            assert native_handles[0].closed
            record(
                "loopback disconnect during worker-owned Pillow work: source stays open until completion; upload/images/output/response released"
            )
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(b"GET /result HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await writer.drain()
            assert await reader.read(4096)
            writer.close()
            await writer.wait_closed()
            await sent.wait()
            await anyio.sleep(0.02)
            gc.collect()
            assert refs and all(ref() is None for ref in refs)
            record(
                "loopback Uvicorn response disconnect releases streaming output owner"
            )
    finally:
        server.should_exit = True
        await server_task
        listener.close()


async def main():
    await parsing()
    await envelope_limits()
    pixel_limits()
    await lifecycle()
    await native_cancellation()
    await raw_cancellation()
    await worker_owned_cancellation()
    await sockets()
    print(
        json.dumps(
            {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "versions": {
                    p: version(p)
                    for p in (
                        "fastapi",
                        "starlette",
                        "Pillow",
                        "python-multipart",
                        "anyio",
                        "uvicorn",
                    )
                },
                "results": RESULTS,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    anyio.run(main)
