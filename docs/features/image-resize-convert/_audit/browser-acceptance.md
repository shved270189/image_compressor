# Implemented browser acceptance — 2026-09-06

Status: partial; T11 remains open. These observations concern the implemented
application, not the previous feasibility probe.

| Environment | Scenario | Actual result |
|---|---|---|
| Desktop Chrome, existing Playwright CLI | Selection/preview, exact byte boundaries, replacement, no preview upload | PASS; see implementation-selection.md |
| Desktop Chrome | PNG/JPEG complete download, dimensions, reset/focus, same-file second conversion | PASS; saved files independently decoded with Pillow |
| Desktop Chrome | Busy lock, duplicate submit, structured 422, retained retry | PASS; input/ctx sentinels absent from displayed errors |
| Desktop Chrome | Partial body interruption, stale completion after pagehide, actual page closure while request pending | PASS; no premature/stale download; failure retains input |
| Desktop Chrome | HEIC to JPEG/PNG/WebP at 360px; actual corrupt input error | PASS; three complete downloadable files, no preview requirement |
| Desktop Chrome | 360/1280px, 500-character unbroken error, keyboard Tab/Enter, reset focus, reduced motion | PASS; overflow defect fixed before acceptance |
| Native macOS Safari 26.6.2 | PNG selection/preview, default JPEG processing, automatic download/reset/focus | PASS; Downloads reports result.jpg 637 bytes; Pillow decodes 32x16 JPEG |
| Native macOS Firefox 155.0 | PNG selection/preview, width16, automatic JPEG download/reset | PASS; Downloads reports result(1).jpg 633 bytes; Pillow decodes 16x8 JPEG |
| Native Safari/Firefox | Complete failure/retry, stale/duplicate, closure, both widths and reduced-motion matrix | OPEN; happy path alone is insufficient |
| Real iPhone Safari | Implemented download/reset/retry/closure matrix | OPEN; physical device unavailable to this session |
| Project owner | Readable contrast of all labels/errors/actions | OPEN; no owner acceptance received |

Chrome test scripts were run through the existing Playwright CLI in
`/tmp/image-implementation-fixtures`; no browser test framework was added.
Native Safari/Firefox were operated through CUA. The Playwright Firefox engine
was unavailable; its failed launch is not counted as a test pass. Safari's
accessibility setValue did not update React's width state in the happy-path check;
that check therefore establishes default conversion, not resizing. Firefox used
actual typing and verifies resizing.

The pending matrix requires selecting the same image twice, checking a corrupt
input error and replacement, closing/reloading during processing, and opening the
saved output. Owner review must include the initial, selected and error states.
Android remains deferred. Desktop viewport emulation is not real-device evidence.
