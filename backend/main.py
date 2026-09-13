import asyncio
import logging
import re
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from python_multipart.exceptions import MultipartParseError
from python_multipart.multipart import parse_options_header
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.responses import Response

from backend import images

images.configure_codecs()
logging.getLogger("python_multipart.multipart").disabled = True

app = FastAPI()

MAX_FILE_BYTES = 20_000_000
MAX_BODY_BYTES = MAX_FILE_BYTES + 65_536
MAX_HEADER_BYTES = 16_384
MAX_FIELD_BYTES = 1024


async def bounded_body(source):
    size = 0
    async for chunk in source:
        size += len(chunk)
        if size > MAX_BODY_BYTES:
            raise HTTPException(413, "Multipart body is too large.")
        yield chunk


class ImageMultipartParser(MultiPartParser):
    def __init__(self, headers, source):
        super().__init__(
            headers,
            bounded_body(source),
            max_files=1,
            max_fields=5,
            max_part_size=MAX_FIELD_BYTES,
        )
        self.complete = False
        self.file_bytes = 0
        self.header_bytes = 0
        self.names = set()

    def count_header(self, size):
        self.header_bytes += size
        if self.header_bytes > MAX_HEADER_BYTES:
            raise HTTPException(413, "Multipart headers are too large.")

    def on_header_field(self, data, start, end):
        self.count_header(end - start)
        super().on_header_field(data, start, end)

    def on_header_value(self, data, start, end):
        self.count_header(end - start)
        super().on_header_value(data, start, end)

    def on_headers_finished(self):
        _, options = parse_options_header(self._current_part.content_disposition)
        name = options.get(b"name")
        if name is None:
            raise HTTPException(400, "Malformed multipart request.")
        if name not in {
            b"file",
            b"max_width",
            b"max_height",
            b"output_format",
            b"size_limit",
            b"size_unit",
        }:
            raise HTTPException(422, "Unexpected form field.")
        if name in self.names:
            raise HTTPException(422, "Duplicate form field.")
        self.names.add(name)
        if (name == b"file") != (b"filename" in options):
            raise HTTPException(422, "Expected one file and text parameters.")
        super().on_headers_finished()

    def on_part_data(self, data, start, end):
        if self._current_part.file is not None:
            self.file_bytes += end - start
            if self.file_bytes > MAX_FILE_BYTES:
                raise HTTPException(413, "Image exceeds 20,000,000 bytes.")
        elif len(self._current_part.data) + end - start > MAX_FIELD_BYTES:
            raise HTTPException(413, "Form field exceeds 1,024 bytes.")
        super().on_part_data(data, start, end)

    def on_end(self):
        self.complete = True

    async def parse(self):
        try:
            form = await super().parse()
            if not self.complete:
                raise HTTPException(400, "Incomplete multipart request.")
            return form
        except BaseException:
            for handle in self._files_to_close_on_error:
                handle.close()
            raise


async def parse_image_request(request: Request):
    content_type = request.headers.get("content-type", "")
    media_type, options = parse_options_header(content_type)
    if media_type.lower() != b"multipart/form-data":
        raise HTTPException(415, "Use multipart/form-data.")
    boundary = options.get(b"boundary", b"")
    if not boundary or len(boundary) > 70:
        raise HTTPException(400, "Invalid multipart boundary.")
    try:
        form = await ImageMultipartParser(request.headers, request.stream()).parse()
    except MultiPartException, MultipartParseError:
        raise HTTPException(400, "Malformed multipart request.") from None
    try:
        upload = form.get("file")
        if not isinstance(upload, UploadFile) or not upload.size:
            raise HTTPException(422, "Select a non-empty image.")
        dimensions = []
        for name in ("max_width", "max_height"):
            value = form.get(name, "")
            if value and (not re.fullmatch(r"[0-9]+", value) or int(value) == 0):
                raise HTTPException(
                    422, f"{name} must be a positive whole pixel count."
                )
            dimensions.append(int(value) if value else None)
        output_format = form.get("output_format")
        size_limit = form.get("size_limit") or ""
        size_unit = form.get("size_unit") or ""
        size_limit_bytes = None
        if size_limit:
            if (
                not re.fullmatch(r"(?:\d+\.?\d*|\.\d+)", size_limit)
                or not Decimal(size_limit) > 0
            ):
                raise HTTPException(
                    422,
                    "size_limit must be a positive number with mb or kb or left empty.",
                )
            if not size_unit:
                raise HTTPException(422, "size_limit requires size_unit mb or kb.")
            if size_unit not in {"mb", "kb"}:
                raise HTTPException(422, "size_unit must be mb or kb.")
            size_limit_bytes = int(
                Decimal(size_limit)
                * Decimal(1_048_576 if size_unit == "mb" else 1024)
            )
        if output_format is None and not any(dimensions) and size_limit_bytes is None:
            raise HTTPException(
                422, "Supply dimensions, an output format or a size limit."
            )
        if output_format is not None and output_format not in {"jpeg", "png", "webp"}:
            raise HTTPException(422, "Choose JPEG, PNG or WebP.")
        return upload, *dimensions, output_format or "jpeg", size_limit_bytes
    except BaseException:
        for _, value in form.multi_items():
            if isinstance(value, UploadFile):
                value.file.close()
        raise


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class ImageResponse(Response):
    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.body = b""


@app.post(
    "/api/v1/images/process", operation_id="processImage", response_class=ImageResponse
)
async def process_image(request: Request):
    upload, width, height, output_format, size_limit_bytes = await parse_image_request(
        request
    )

    def work():
        with upload.file:
            try:
                return images.process_image(
                    upload.file, width, height, output_format, size_limit_bytes
                )
            except images.ImageTooLarge:
                raise HTTPException(413, "Image exceeds 40,000,000 pixels.") from None
            except images.UnsupportedImage:
                raise HTTPException(
                    415, "Choose a JPEG, PNG, WebP or HEIC image."
                ) from None
            except images.OutputTooLarge as error:
                raise HTTPException(422, str(error)) from None
            except images.InvalidImage:
                raise HTTPException(
                    422,
                    "Image is corrupted, animated or has invalid color information.",
                ) from None
            except Exception:  # noqa: BLE001
                raise HTTPException(
                    500, "Image processing failed. Please try again."
                ) from None

    try:
        future = asyncio.get_running_loop().run_in_executor(None, work)
    except BaseException:
        upload.file.close()
        raise
    future.add_done_callback(
        lambda done: done.exception() if not done.cancelled() else None
    )
    output = await asyncio.shield(future)
    extension = "jpg" if output_format == "jpeg" else output_format
    headers = {"Content-Disposition": f'attachment; filename="result.{extension}"'}
    if size_limit_bytes is not None:
        headers["X-Result-Bytes"] = str(len(output))
        headers["X-Size-Limit-Met"] = (
            "true" if len(output) <= size_limit_bytes else "false"
        )
    return ImageResponse(
        output,
        media_type=f"image/{output_format}",
        headers=headers,
    )


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.frontend("/", directory=frontend_dist, fallback=None)
