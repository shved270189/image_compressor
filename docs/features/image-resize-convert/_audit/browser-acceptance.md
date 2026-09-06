# Implemented browser acceptance — 2026-09-06

Status: PASS — T11 acceptance completed on 2026-09-06. These observations concern the implemented
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
| Firefox 155.0 / WebKit 26.5 automation | Failure/retry, stale/duplicate, closure, both widths, reduced motion, keyboard | PASS; engine evidence, with native Safari server-error retry checked separately |
| Real iPhone Safari and iOS Firefox | Download and form reset | PASS, owner-reported; iPhone Safari network failure/retry also confirmed. Other follow-ups did not identify a browser |
| Project owner | Readability of labels, fields and buttons on phone and desktop | ACCEPTED by owner on 2026-09-06 |

Chrome test scripts were run through the existing Playwright CLI in
`/tmp/image-implementation-fixtures`; no browser test framework was added.
Native Safari/Firefox were operated through CUA. The Playwright Firefox engine
was unavailable; its failed launch is not counted as a test pass. Safari's
accessibility setValue did not update React's width state in the happy-path check;
that check therefore establishes default conversion, not resizing. Firefox used
actual typing and verifies resizing.

At the earlier checkpoint, the pending matrix required a corrupt input error and replacement,
closing/reloading during processing, and opening the saved output. Repeated
selection is owner-confirmed for the tested browser; its exact browser was not
specified in the follow-up. Owner readability acceptance is recorded below.
Android remains deferred. Desktop viewport emulation is not real-device evidence.

## Owner verification — 2026-09-06

The owner tested the implemented application over LAN in iOS Safari, desktop
Safari, iOS Firefox and desktop Firefox. The initial report of a stuck Processing
state was explicitly withdrawn: everything worked correctly. Download and form
reset are therefore recorded as owner-confirmed. The owner subsequently confirmed
that labels, fields and buttons are readable on phone and desktop.

This closes real-device happy-path verification and owner readability acceptance.
It does not assert unreported failure/retry, interruption or
reduced-motion checks on those browsers. At that checkpoint, the remaining matrix and Security Lead review were open;
the final follow-up below supersedes that status. No application code was changed
for the withdrawn report.

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

## Final engine and native follow-up — 2026-09-06

Existing Playwright CLI now has matching Firefox 155.0 and WebKit 26.5 engines.
Only tool-managed browser runtimes were installed; project dependencies and test
infrastructure did not change. Both engines pass the existing download/retry
checks: exact output size/name, complete body before download, native reset/focus,
zero live Blob URLs, one POST despite duplicate submits, safe structured 422
messages and successful retry with retained input.

Both pass controlled partial-body failure and stale completion after pagehide,
360/1280px overflow checks, reduced-motion checks, keyboard submission, HEIC
conversion to each output format, actual corrupt-content rejection and actual
page closure with a request pending. Twelve downloaded files were independently
decoded with Pillow and matched expected formats/dimensions. Firefox HEIC files
use the original `heic.*` artifact names; WebKit files use `webkit-heic.*`.

WebKit's first keyboard assertion failed because ordinary Tab skips buttons under
its macOS keyboard-navigation defaults. Option+Tab reaches Process image with a
visible outline; Enter submits and downloads. Re-running with that native keyboard
sequence passes. No application change was required.

Native Safari additionally passes real server-error recovery: a generated
16,384x1 PNG to WebP returns actionable 422 and retains file/preview/format; entering
width 100 and retrying downloads a complete 100x1 WebP, clears the form and focuses
file selection. Pillow independently decoded the saved file.

WebKit automation is engine evidence, not a claim of physical iPhone execution or
Safari UI automation. Owner-reported native/mobile checks remain separately
attributed above. The final real iPhone Safari network-failure/retained-input/retry check was
subsequently confirmed by the owner, as recorded below. Acceptance combines the
explicitly attributed native/device observations and automated engine checks;
it does not claim every scenario was automated on a physical iPhone.

Firefox/WebKit selection checks also pass: exact byte boundaries, preview failure
without blocked processing, old URL release, rapid replacement, exact long-bound
text retention, no upload before submit and reload without restored selection.

## Final owner confirmation — 2026-09-06

The owner explicitly confirmed the requested real iPhone Safari network-failure
scenario: the selected file remains after the failed offline submission, and
restoring connectivity then retrying downloads the result and clears the form.
This closes the final requested manual acceptance check. T11 is complete based
on the evidence matrix above, including owner readability acceptance, native
Safari/Firefox downloads and recovery, and automated lifecycle/accessibility
checks. Browser/version and automation-versus-device distinctions remain intact.
