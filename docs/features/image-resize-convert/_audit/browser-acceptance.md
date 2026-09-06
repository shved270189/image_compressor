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
| Real iPhone Safari and iOS Firefox | Download and form reset | PASS, owner-reported on the implemented LAN application; retry/closure matrix remains open |
| Project owner | Readability of labels, fields and buttons on phone and desktop | ACCEPTED by owner on 2026-09-06 |

Chrome test scripts were run through the existing Playwright CLI in
`/tmp/image-implementation-fixtures`; no browser test framework was added.
Native Safari/Firefox were operated through CUA. The Playwright Firefox engine
was unavailable; its failed launch is not counted as a test pass. Safari's
accessibility setValue did not update React's width state in the happy-path check;
that check therefore establishes default conversion, not resizing. Firefox used
actual typing and verifies resizing.

The pending matrix requires checking a corrupt input error and replacement,
closing/reloading during processing, and opening the saved output. Repeated
selection is owner-confirmed for the tested browser; its exact browser was not
specified in the follow-up. Owner review must include the initial, selected and error states.
Android remains deferred. Desktop viewport emulation is not real-device evidence.

## Owner verification — 2026-09-06

The owner tested the implemented application over LAN in iOS Safari, desktop
Safari, iOS Firefox and desktop Firefox. The initial report of a stuck Processing
state was explicitly withdrawn: everything worked correctly. Download and form
reset are therefore recorded as owner-confirmed. The owner subsequently confirmed
that labels, fields and buttons are readable on phone and desktop.

This closes real-device happy-path verification and owner readability acceptance.
It does not assert unreported failure/retry, interruption or
reduced-motion checks on those browsers. The remaining matrix and Security Lead
acceptance stay open; no application code was changed for the withdrawn report.

The owner also selected and processed the same image twice consecutively and
explicitly confirmed that both downloads completed and the form cleared after
each operation. This records a passed repeated-selection check; the follow-up
did not identify which browser was used, so no all-browser coverage is inferred.

The owner confirmed that submitting an image and immediately reloading opens an
empty form. Exact browser and whether server processing was still pending at
reload were not specified; this proves the observed empty-form outcome, not the
complete interruption matrix or suppression of every late download.

The owner confirmed local dimension validation and correction: width 0 shows an
error, and changing it to 100 allows a successful download. The exact browser
was not specified. This verifies local validation recovery, not recovery from
a server rejection or an interrupted response.
