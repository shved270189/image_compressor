# Security and container acceptance — 2026-09-06

Status: technical checks pass; Security Lead acceptance remains open.

## Checks

- `npm --prefix frontend run build`: TypeScript and production build pass.
- `uv run pytest -q`: 180 host tests pass. `uv run ruff check .` and
  `npm --prefix frontend run lint`: pass.
- `docker build -t image-compressor:implementation .`: pass, Linux arm64.
- Production image plus read-only test/config mounts: 180 Linux tests pass in
  9.77s. An isolated `/tmp/check` venv supplies pytest/httpx; PYTHONPATH includes
  `/app/.venv/lib/python3.14/site-packages:/app` to exercise the production image's
  locked runtime libraries. Initial test-runner setup omitted this path and failed
  collection; corrected setup passes. No production image dependencies changed.
- A fresh application container exposed only on a random loopback port passes
  `SMOKE_BASE_URL=<container-url> uv run pytest tests/test_smoke.py -q`: 1 passed.
  Smoke covers emitted JS/CSS, health, real RGBA PNG-to-WebP resize with preserved
  alpha and API 404s including a nonexistent result path. `docker exec <id> id -u`
  returns 10001. Container stopped after the check.

## Ownership and confidentiality

Existing feature tests cover partial multipart EOF, exact byte/pixel bounds,
post-decode dimensions, decoded core closure, worker startup/encoding failures,
raw cancellation while queued/running, real socket interruption, and response
body clearing after send success/failure. Worker ownership persists until native
processing finishes. ExitStack closes every decoded/intermediate image, and no
result ID, datastore or retrieval route exists. RSS is not used as an ownership
oracle. Safe error/log regressions reject image content and private diagnostics.

Independent read-only review examined the public parser/decoder/encoder path,
confidential errors and cancellation ownership. It found two defects: color-key
transparency lost by early resizing/16-bit scaling, and orphan HEIF fragments
accepted as static. Six RED regressions became GREEN after root-cause fixes in
commit `08698b0`; original sample alpha is expanded before resizing and unknown
fragment track IDs are rejected. All prior color/HDR/timeline tests remain green.
The review found no further confirmed ownership leak or private-data disclosure.

This is code/test evidence, not native-code fuzzing, a throughput guarantee or a
Security Lead signature. Formal acceptance must be recorded by the designated
reviewer before T12 is marked done.
