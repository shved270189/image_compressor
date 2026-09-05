import asyncio
import os
import re

import httpx

from backend.main import app


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

            for path in ("/api", "/api/missing", "/api/missing/nested"):
                for accept in ("application/json", "text/html"):
                    response = await client.get(path, headers={"Accept": accept})
                    assert response.status_code == 404

    asyncio.run(check())
