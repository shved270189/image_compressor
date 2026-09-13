import asyncio
import io
import os
import re
from pathlib import Path

import httpx
from PIL import Image

from backend.main import app

HEIC_NOTICE = (
    "HEIC: only the primary image is used; extra images are omitted. "
    "HDR becomes ordinary 8-bit output and may not retain its original appearance."
)
SIZE_LIMIT_ERROR = (
    "Ліміт ваги must be a positive number with Mb or Kb or left empty"
)
SIZE_LIMIT_HELP = "Leave empty for no result size bound."


def test_heic_notice_copy():
    source = Path("frontend/src/App.tsx").read_text()
    assert HEIC_NOTICE in source


def test_size_limit_form_copy():
    source = Path("frontend/src/App.tsx").read_text()
    assert "Size limit" in source
    assert SIZE_LIMIT_ERROR in source
    assert SIZE_LIMIT_HELP in source
    assert 'id="size-limit-help"' in source
    assert 'type="radio"' in source
    number = source.index('id="size-limit"')
    assert source.index('value="mb"') < number
    assert source.index('value="kb"') < number
    assert 'aria-describedby="size-limit-help file-error"' in source


def test_size_limit_miss_and_submit_wiring():
    source = Path("frontend/src/App.tsx").read_text()
    assert "body.append('size_limit', sizeLimit)" in source
    assert "body.append('size_unit', sizeUnit)" in source
    assert "x-size-limit-met" in source
    assert "x-result-bytes" in source
    assert "The result is " in source
    assert "The size limit was exceeded." in source
    assert 'aria-live="polite"' in source
    assert "size_limit" in source and "size_unit" in source
    assert "setMiss(" in source


def test_skeleton():
    async def check():
        base_url = os.environ.get("SMOKE_BASE_URL")
        transport = None if base_url else httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            base_url=base_url or "http://test", transport=transport
        ) as client:
            health = await client.get("/api/health")
            assert health.status_code == 200
            assert health.json() == {"status": "ok"}

            page = await client.get("/")
            assert page.status_code == 200
            assert "text/html" in page.headers["content-type"]
            assert '<div id="root"></div>' in page.text

            assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', page.text)
            assert any(asset.endswith(".js") for asset in assets)
            assert any(asset.endswith(".css") for asset in assets)
            for asset in assets:
                response = await client.get(asset)
                assert response.status_code == 200
                assert response.content
                assert "text/html" not in response.headers["content-type"]

            with (
                Image.new("RGBA", (4, 2), (30, 60, 90, 128)) as image,
                io.BytesIO() as source,
            ):
                image.save(source, "PNG")
                response = await client.post(
                    "/api/v1/images/process",
                    files={"file": ("input.png", source.getvalue(), "image/png")},
                    data={"max_width": "2", "output_format": "webp"},
                )
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/webp"
            assert response.headers["content-disposition"] == (
                'attachment; filename="result.webp"'
            )
            assert "x-result-bytes" not in response.headers
            assert "x-size-limit-met" not in response.headers
            with Image.open(io.BytesIO(response.content)) as result:
                result.load()
                assert result.size == (2, 1)
                pixel = result.getpixel((0, 0))
                assert pixel[3] == 128
                assert all(abs(actual - expected) <= 1 for actual, expected in zip(
                    pixel[:3], (30, 60, 90), strict=True
                ))

            with (
                Image.new("RGB", (4, 2), (30, 60, 90)) as image,
                io.BytesIO() as source,
            ):
                image.save(source, "PNG")
                jpeg = await client.post(
                    "/api/v1/images/process",
                    files={"file": ("input.png", source.getvalue(), "image/png")},
                    data={"size_limit": "0.5", "size_unit": "mb"},
                )
            assert jpeg.status_code == 200
            assert jpeg.headers["content-type"] == "image/jpeg"
            assert jpeg.headers["content-disposition"] == (
                'attachment; filename="result.jpg"'
            )
            with Image.open(io.BytesIO(jpeg.content)) as result:
                assert result.format == "JPEG"

            for path in (
                "/api", "/api/missing", "/api/missing/nested",
                "/api/v1/images/result.webp",
            ):
                for accept in ("application/json", "text/html"):
                    response = await client.get(path, headers={"Accept": accept})
                    assert response.status_code == 404
                    assert "image/" not in response.headers.get("content-type", "")

    asyncio.run(check())
