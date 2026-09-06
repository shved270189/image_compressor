import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from python_multipart.exceptions import MultipartParseError
from python_multipart.multipart import parse_options_header
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from backend import images

images.configure_codecs()

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
            max_fields=3,
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
        if name not in {b"file", b"max_width", b"max_height", b"output_format"}:
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
        if output_format is None and not any(dimensions):
            raise HTTPException(422, "Supply dimensions or an output format.")
        if output_format is not None and output_format not in {"jpeg", "png", "webp"}:
            raise HTTPException(422, "Choose JPEG, PNG or WebP.")
        return upload, *dimensions, output_format or "jpeg"
    except BaseException:
        for _, value in form.multi_items():
            if isinstance(value, UploadFile):
                value.file.close()
        raise


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.frontend("/", directory=frontend_dist, fallback=None)
