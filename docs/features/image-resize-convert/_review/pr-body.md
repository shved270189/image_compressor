## Summary

Ships the local resize-and-convert workflow: one form selects a static JPEG, PNG, WebP or HEIC image, optionally bounds its dimensions, converts the format, and downloads the current result. See [spec](docs/features/image-resize-convert/spec.md).

## Acceptance criteria

- AC-01 — empty form keeps processing disabled; a valid file enables JPEG-default processing ✓
- AC-02 — local Preview when the browser can display the file; missing Preview does not block processing ✓
- AC-03 — a new selection replaces Preview and resets dimensions/format; stale work cannot overwrite the current form ✓
- AC-04 — 2400×1200 with width 1200 → 1200×600; height 300 → 600×300; both → 600×300 ✓
- AC-05 — largest proportional fit, nearest-pixel rounding (halves up, minimum 1px); 1000×333 width 500 → 500×167 ✓
- AC-06 — ineffective bounds and same-format conversion remain valid and still normalize ✓
- AC-07 — JPEG/PNG/WebP output for JPEG, PNG, WebP and HEIC input; no smaller-file guarantee ✓
- AC-08 — JPEG transparency warning on the form; JPEG composites onto white; PNG/WebP retain alpha ✓
- AC-09 — Preview and result share visible orientation; GPS/camera/textual metadata omitted ✓
- AC-10 — HEIC uses the primary static image; form notice covers extra images, HDR→8-bit, and appearance ✓
- AC-11 — missing parameters, invalid dimensions and unsupported format choices are rejected with a reason ✓
- AC-12 — empty, corrupted, unsupported, animated, oversize and over-pixel inputs are rejected ✓
- AC-13 — one automatic download, then a clean form with no result characteristics left on the page ✓
- AC-14 — no history, lookup or retrieval of another operation's result ✓
- AC-15 — processing locks controls; recoverable errors retain input; stale completions cannot download ✓
- AC-16 — no server-side original or result retained for later retrieval; Preview never uploads the file ✓

## Design

- Spec: `docs/features/image-resize-convert/spec.md`
- Architecture: `docs/features/image-resize-convert/sad.md`
- Decisions: `docs/features/image-resize-convert/adr/`
- Data model: `docs/features/image-resize-convert/data-model.md` (no migration)
- API: `docs/features/image-resize-convert/contracts/openapi.yaml`

## Tasks (SDD-Task trailers)

Most implementation commits predate trailer enforcement. Mapping from the tracker and `git log`:

- T1 `6c7cfdc` feat: bound image upload parsing
- T2 `777aaa7` feat: decode supported static images
- T3 `5bdc32c` feat: classify HEIF presentation timelines (`0a13e1c`, `e9661f2`, `d062859`)
- T4 `01c0638` feat: handle fragmented HEIF timelines
- T5 `c9eee13` feat: resize and normalize image output
- T6 `1e85b74` feat: preserve compatible image color profiles
- T7 `4b3aa06` feat: convert HDR images to ordinary SDR output
- T8 `23c8c84` feat: serve request-scoped image results (`08698b0`)
- T9 `1d027e7` feat: select images with local preview
- T10 `52eaa85` feat: process images and download current result
- T11–T13 browser/security/docs acceptance (`3c18251` … `40c8817`)
- Review follow-up `4918067` fix(image-resize-convert): restore HEIC notice and pin preview orientation
  - `SDD-Task: T9`
  - `SDD-Task: T11`
  - `SDD-AC: AC-02, AC-09, AC-10`

`9f95edc` (SDD plugin install) is on this history and is not product behavior.

## Verification

- Unit: `uv run pytest -q` — 181 passed (host)
- Integration: `SMOKE_BASE_URL=http://127.0.0.1:8000 uv run pytest -q` against `image-compressor:smoke` — 181 passed
- Lint + vet: `uv run ruff check .` pass; `npm --prefix frontend run lint` pass; `npm --prefix frontend run build` (`tsc --noEmit` + Vite) pass
- Ran the feature (container on `http://127.0.0.1:8000`, UID 10001):
  - AC-04: live POST 2400×1200 PNG → 1200×600 / 600×300 / 600×300
  - AC-05: 1000×333 width 500 → 500×167
  - AC-07: PNG→JPEG `result.jpg`, PNG→WebP
  - AC-08: transparent PNG→JPEG pixel (255,255,255)
  - AC-10: HEIC `arrow.heic` processed to PNG
  - AC-11: `max_width=0` → 422; omitted parameters → 422
  - AC-12: BMP → 415; corrupt bytes → 422
  - AC-14: GET `/api/v1/images/abc` and `/results/1` → 404
  - AC-01/AC-08/AC-10: empty form, JPEG warning and HEIC notice visible, controls disabled
  - AC-02: local blob Preview after selecting PNG; no upload until Process
  - AC-11/AC-15: width `0` rejected in the UI; file retained
  - AC-13: Process → one `result.jpg` blob download, POST 200, form reset to empty JPEG defaults

## Operational notes

- Migration: none.
- Feature flag / config: none.
- Rollback: revert the deploy or feature commits. No stored images to purge.
