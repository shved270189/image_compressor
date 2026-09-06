# Selection implementation acceptance

Chrome, 2026-09-06. Existing Playwright CLI; no new test infrastructure.

RED: initial application had no file input (AC-01).
GREEN: initial disabled parameters; eligible PNG preview; JPEG default; exact 1024-digit dimension retention; conditional JPEG notice; replacement resets all parameters; empty and 20,000,001-byte files rejected before preview; exactly 20,000,000 bytes eligible; failed native decoding omits preview; rapid PNG/HEIF replacement cannot restore old preview; zero processing POSTs before submission; no horizontal overflow at 360 and 1280 pixels; reduced motion; reload restores no selection.

Review follow-up 2026-09-06: empty form (no file, no upload) shows `HEIC: only the primary image is used; extra images are omitted. HDR becomes ordinary 8-bit output and may not retain its original appearance.` Matching screens.md / AC-10. Chrome Playwright snapshot on http://localhost:5173.

Object URL instrumentation confirmed obsolete previews are released. Native text inputs with numeric input mode avoid JavaScript number coercion and preserve the unbounded dimension contract. Positive-whole validation belongs to T10.

Checks: `npm --prefix frontend run build`, `npm --prefix frontend run lint`, `uv run ruff check .`, `uv run pytest -q` (174 passed). Browser acceptance across other engines and real iPhone remains T11.
