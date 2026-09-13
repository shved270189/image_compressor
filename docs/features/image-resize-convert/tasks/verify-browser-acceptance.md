---
id: "T11"
title: "Verify browser acceptance"
layer: "tests"
deps: ["T10"]
blocks: ["T13"]
acs: ["AC-01", "AC-02", "AC-03", "AC-08", "AC-10", "AC-13", "AC-15", "AC-16"]
files_hint: ["docs/features/image-resize-convert/_audit/browser-acceptance.md"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "The implemented-flow browser matrix in _audit/browser-acceptance.md passes on desktop Chrome/Safari/Firefox and iPhone Safari, including complete downloads, recovery/closure, both widths, keyboard/reduced motion and recorded owner contrast acceptance."
file: "docs/features/image-resize-convert/tasks/verify-browser-acceptance.md"
---

# T11 — Verify browser acceptance

## Place in the sequence

- **Blocked by:** T10 — Submit and download the current result. **Blocks:** T13 — Document the completed workflow. **Wave:** 9 (after its prerequisites).
- **Lane:** Own lane; may run alongside ready tasks with disjoint files.
- **Context:** 71 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As an** Image owner
> **I want** the Result to download automatically after successful processing and the form to reset
> **So that** I can use the completed file without overwriting the Original and immediately select the next image.

— `spec.md §4, US-04, verbatim` · [Full text](../spec.md)

Verify browser acceptance delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Completion.** Wait for the whole successful response before attempting a download. Recheck that the operation is current and not consumed. Hand the Blob URL to a native download action once, with the requested format and matching filename extension, then return to the initial form. Reset clears the native file input too, allowing the same file to be selected again. No result panel, repeat-download control or result object remains in application state.

— `sad.md §6, Completion, verbatim` · [Full text](../sad.md)

> | Accessibility | Every interactive control is keyboard-usable with visible focus; every label, error and action passes the project owner's manual readable-contrast review; with reduced motion, zero decorative animations and zero loss of functionality | Full keyboard flow, visible-focus review, manual contrast acceptance by the project owner without numeric contrast thresholds, and reduced-motion browser check |

— `spec.md §6, Accessibility, verbatim` · [Full text](../spec.md)

> | Responsive UI | Complete flow at viewport widths 360 and 1280 CSS pixels with no horizontal page overflow | Browser visual review at both widths |

— `spec.md §6, Responsive UI, verbatim` · [Full text](../spec.md)

> Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in backend/main.py and image functions in backend/images.py.

— `adr/0001-extend-web-frontend-and-backend-service.md §Decision outcome, ADR-0001, abridged` · [Full text](../adr/0001-extend-web-frontend-and-backend-service.md)

> Use one processing request with a complete binary response and no result ID, lookup or second retrieval request. Lock file selection, parameters and repeated submission while it is pending. On complete success, verify currentness and consume the operation once, initiate a native download with the matching filename extension, and reset the form. A separate handoff owner releases the result Blob URL when safe; resetting form state must not revoke it prematurely. Retain current input after recoverable errors. Invalidate page work on teardown and release server resources on success, failure and interruption, allowing already-running native decoding to finish before its resources are released.

— `adr/0004-return-results-within-the-current-operation.md §Decision outcome, ADR-0004, verbatim` · [Full text](../adr/0004-return-results-within-the-current-operation.md)

> Full browser failure/retry/closure coverage belongs to implemented-flow acceptance.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

`POST /api/v1/images/process` (`processImage`), multipart `file`, optional `max_width` / `max_height`, and `output_format` (`jpeg`, `png`, `webp`). Empty dimensions impose no bound; dimensions with omitted format use JPEG, but no supplied parameter is 422. Explicit empty format is invalid. No product upper dimension bound.

200: complete binary `image/jpeg`, `image/png` or `image/webp`, with required `Content-Disposition: attachment; filename="result.jpg"` (or `result.png` / `result.webp`). No result ID, JSON wrapper or retrieval endpoint. Errors: 400 malformed multipart, 413 excess file bytes/pixels, 415 unsupported request/content, 422 missing/invalid parameters or empty/corrupt/animated input, 500 safe internal failure. `detail` is a readable string or a 422 validation array with `loc`, `msg`, `type`; wording/order is not a machine contract. Never expose image data, filenames or internal exception details. An interrupted response may have no error body.

— `contracts/openapi.yaml §paths, operationId processImage and schemas, abridged` · [Full text](../contracts/openapi.yaml)

## Acceptance criteria

### AC-01 (US-01) — happy

> **Given** no Original has been selected,
> **When** Image owner opens the form,
> **Then** the file-selection control remains available, transformation parameter controls are disabled or hidden and processing is disabled; selecting a non-empty file of at most 20,000,000 bytes reveals or enables the transformation controls with JPEG selected and empty dimension limits, and enables processing without waiting for content validation. Selecting an empty file or a file above that byte limit immediately shows an understandable error, omits Preview and keeps processing disabled.

— `spec.md §5, AC-01, verbatim` · [Full text](../spec.md)

### AC-02 (US-01) — happy

> **Given** a supported Original within the input limits,
> **When** Image owner selects it,
> **Then** a supported Preview appears above the form, preserves the complete image and correct orientation and is prepared entirely on the owner's device without sending the file for preview generation; when the browser cannot display the file, no Preview or broken-image placeholder is shown, and this absence does not block processing, including for HEIC.

— `spec.md §5, AC-02, verbatim` · [Full text](../spec.md)

### AC-03 (US-01, US-04) — cross-context

> **Given** an Original has been selected,
> **When** Image owner makes a new file selection,
> **Then** the previous Preview disappears, dimensions reset to empty and format resets to JPEG, including when the newly selected file is empty or above the byte limit; delayed work for an old selection or completed operation must never replace the current Preview, repopulate a reset form or trigger another download. An unavailable or failed Preview is omitted rather than displaying the old picture, a broken-image placeholder or a processing error.

— `spec.md §5, AC-03, verbatim` · [Full text](../spec.md)

### AC-08 (US-03) — domain invariant

> **Given** a selected Original, whether or not its transparency is known or Preview is available,
> **When** Image owner chooses JPEG,
> **Then** the form always shows a conditional warning before processing: if the image has transparency, it will become white; this also applies when JPEG is selected by default and requires no advance transparency detection. The JPEG Result uses white behind partial and full transparency; PNG and WebP output retain transparency.

— `spec.md §5, AC-08, verbatim` · [Full text](../spec.md)

### AC-10 (US-01, US-03) — happy

> **Given** a HEIC Original with additional images or high-dynamic-range content,
> **When** Image owner processes it,
> **Then** only the designated primary static image is used; the form explains the general HEIC rules before submission: extra images are omitted and high-dynamic-range content becomes ordinary 8-bit output, with no promise of retaining the original high-dynamic-range appearance; this notice requires no advance server inspection.

— `spec.md §5, AC-10, verbatim` · [Full text](../spec.md)

### AC-13 (US-04) — cross-context

> **Given** successful processing for the current selection,
> **When** the current operation's complete Result is ready,
> **Then** the page initiates exactly one automatic browser download without a separate download action; the file has the requested output format and matching filename extension, and the Original remains untouched. After handing the file to the browser for download, the page returns to the initial form without reloading: the selected file, Preview, Result and errors are removed, both dimension limits become empty and format resets to JPEG. File selection is available, transformation controls are disabled or hidden and processing is disabled until another eligible file is selected. No result characteristics or repeat-download action remain on the page. Reset must not interrupt the initiated download and does not wait for confirmation that the browser saved the file to disk. The next selected file starts an independent conversion, including when it is the same file as before.

— `spec.md §5, AC-13, verbatim` · [Full text](../spec.md)

### AC-15 (US-05) — error

> **Given** processing is in progress,
> **When** Image owner waits, processing fails or the page closes,
> **Then** the form disables file selection, all transformation parameter controls and repeat submission while processing, shows a truthful busy state without fabricated percentages, restores the controls and retry with the selected file and parameters after a recoverable error, and offers no result restoration after closing or reloading the page. Successful completion initiates the automatic download and resets the form as specified in AC-13; only the current operation may initiate that download, and no stale or duplicate completion may initiate it again.

— `spec.md §5, AC-15, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] Use existing browser tooling against the implemented SCR-01 flow; record _audit/browser-acceptance.md with browser/platform, scenario, expected/actual result and evidence. No new browser test infrastructure.
- [ ] Exercise desktop Chrome/Safari/Firefox and real iPhone Safari: full download/reset, optional/unavailable Preview, failure/retry, stale/duplicate suppression, same-file second conversion and closure. Downloaded output must be complete.
- [ ] Review 360/1280 CSS pixels, long filenames/errors, full keyboard flow, focus after reset and reduced motion. Obtain the Project owner's readable-contrast acceptance; viewport emulation does not replace the real mobile download check.
- [ ] Record real failures for the owning implementation task; do not mark this task done from feasibility-probe evidence or add fixes outside its files_hint. Android remains owner-deferred.

## Edge cases

| Case | Required behavior |
|---|---|
| Mobile device unavailable | Keep the required implemented-flow check open; prior feasibility is not full acceptance. |
| Long filename/error at 360 px | No horizontal page overflow. |
| Reduced motion enabled | Remove decorative motion without changing flow or delaying download. |

— `spec.md §5, AC-01, AC-02, AC-03, AC-08, AC-10, AC-13, AC-15, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] The implemented-flow browser matrix in _audit/browser-acceptance.md passes on desktop Chrome/Safari/Firefox and iPhone Safari, including complete downloads, recovery/closure, both widths, keyboard/reduced motion and recorded owner contrast acceptance.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
