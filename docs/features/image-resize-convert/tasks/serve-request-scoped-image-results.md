---
id: "T8"
title: "Serve request-scoped image results"
layer: "ports"
deps: ["T1", "T7"]
blocks: ["T10", "T12"]
acs: ["AC-07", "AC-11", "AC-12", "AC-13", "AC-14", "AC-15", "AC-16"]
files_hint: ["backend/main.py", "backend/images.py", "tests/test_images_api.py", "tests/fixtures/images/"]
owner: "Tech Lead"
estimate: "8h"
context_budget: "M"
status: "todo"
dod: "tests/test_images_api.py endpoint and ownership regressions pass, including actual socket interruption and raw cancellation, correct binary headers/errors, no retrieval capability and no leaked upload/image/response owners."
file: "docs/features/image-resize-convert/tasks/serve-request-scoped-image-results.md"
---

# T8 — Serve request-scoped image results

## Place in the sequence

- **Blocked by:** T1 — Bound multipart parsing, T7 — Convert HDR to ordinary SDR output. **Blocks:** T10 — Submit and download the current result, T12 — Verify security and container behavior. **Wave:** 7 (after its prerequisites).
- **Lane:** Shares files with T1, T2, T3, T4, T5, T6, T7, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 74 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** the Результат to download automatically after successful processing and the form to reset
> **So that** I can use the completed file without overwriting the Оригінал and immediately select the next image.

— `spec.md §4, US-04, verbatim` · [Full text](../spec.md)

Serve request-scoped image results delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Failure and interruption.** Recoverable validation, processing and transfer errors restore controls with the same selected file and parameters. Closing or reloading invalidates browser work without restoration. The server closes upload handles and image resources on success, errors and interruption; native work may finish before its resources can be closed. The response owns encoded output only until response completion or failure. No prior result can be restored. The diagram shows logical lifecycle completion, not permission to keep a decoded image alive throughout a response unnecessarily.

— `sad.md §6, Failure and interruption, verbatim` · [Full text](../sad.md)

> | Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |

— `spec.md §6, Transient resources, verbatim` · [Full text](../spec.md)

> | Form concurrency | At most one submitted processing operation from the current form; file selection and all transformation parameter controls disabled while processing | Duplicate-submit and disabled-control checks, including clean-form reset after successful download handoff and retained input after recoverable failure |

— `spec.md §6, Form concurrency, verbatim` · [Full text](../spec.md)

> Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in backend/main.py and image functions in backend/images.py.

— `adr/0001-extend-web-frontend-and-backend-service.md §Decision outcome, ADR-0001, abridged` · [Full text](../adr/0001-extend-web-frontend-and-backend-service.md)

> Use one processing request with a complete binary response and no result ID, lookup or second retrieval request. Lock file selection, parameters and repeated submission while it is pending. On complete success, verify currentness and consume the operation once, initiate a native download with the matching filename extension, and reset the form. A separate handoff owner releases the result Blob URL when safe; resetting form state must not revoke it prematurely. Retain current input after recoverable errors. Invalidate page work on teardown and release server resources on success, failure and interruption, allowing already-running native decoding to finish before its resources are released.

— `adr/0004-return-results-within-the-current-operation.md §Decision outcome, ADR-0004, verbatim` · [Full text](../adr/0004-return-results-within-the-current-operation.md)

> Preserve the verified worker ownership transfer and partial-parser cleanup. Document bounded multipart transport representation and error mapping in the implementation contract without inventing a numeric maximum dimension. Pin and verify the version-sensitive Starlette and bundled LittleCMS bindings.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

> Ownership transfers to the synchronous worker before processing; an async
> FormData context must not close that source while the worker still uses it.
> Actual Pillow work, raw cancellation and socket interruption are exercised.
> Full HEIC route integration, post-decode dimension validation and confidential
> error/log behavior remain implementation acceptance obligations. The pixel
> boundary probe uses a real PPM header and load spy, not a full 40M-pixel decode.
> Observation deadlines are test controls, not production retention timers.

— `_audit/pre-tasks-feasibility.md §Server ownership evidence, verified mechanism, verbatim` · [Full text](../_audit/pre-tasks-feasibility.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

`POST /api/v1/images/process` (`processImage`), multipart `file`, optional `max_width` / `max_height`, and `output_format` (`jpeg`, `png`, `webp`). Empty dimensions impose no bound; dimensions with omitted format use JPEG, but no supplied parameter is 422. Explicit empty format is invalid. No product upper dimension bound.

200: complete binary `image/jpeg`, `image/png` or `image/webp`, with required `Content-Disposition: attachment; filename="result.jpg"` (or `result.png` / `result.webp`). No result ID, JSON wrapper or retrieval endpoint. Errors: 400 malformed multipart, 413 excess file bytes/pixels, 415 unsupported request/content, 422 missing/invalid parameters or empty/corrupt/animated input, 500 safe internal failure. `detail` is a readable string or a 422 validation array with `loc`, `msg`, `type`; wording/order is not a machine contract. Never expose image data, filenames or internal exception details. An interrupted response may have no error body.

— `contracts/openapi.yaml §paths, operationId processImage and schemas, abridged` · [Full text](../contracts/openapi.yaml)

## Acceptance criteria

### AC-07 (US-03) — happy

> **Given** a supported static JPEG, PNG, WebP or HEIC Оригінал,
> **When** Власник картинки chooses JPEG, PNG or WebP and processes it,
> **Then** a decodable Результат is produced in the chosen format; JPEG is the initial output choice for every input, including JPEG itself, and there is no guarantee of smaller file size or byte-identical output.

— `spec.md §5, AC-07, verbatim` · [Full text](../spec.md)

### AC-11 (US-05) — error

> **Given** no file, no supplied transformation parameter, an invalid dimension or an unsupported output choice,
> **When** processing is attempted,
> **Then** the system rejects the attempt and explains the reason even when form restrictions are bypassed; dimensions must be positive whole pixel counts, empty dimensions impose no bound, and a supplied output format including the form's default JPEG counts as a parameter. Valid supplied dimensions with no output format produce JPEG; omitting both dimensions and output format remains an error.

— `spec.md §5, AC-11, verbatim` · [Full text](../spec.md)

### AC-12 (US-05) — error

> **Given** an empty, corrupted, unsupported or animated Оригінал, or an input above 20 million bytes or 40 million decoded pixels,
> **When** processing is attempted,
> **Then** the system rejects it with an understandable reason and produces no successful Результат; exact limits are allowed, support is determined from actual content, and additional HEIC images are subject to the primary-image rule rather than treated as animation. The form checks only whether the selected file is empty or exceeds the byte limit before preparing Preview; the server checks content, animation and decoded pixel count when processing is submitted, and enforces all input limits even when form restrictions are bypassed.

— `spec.md §5, AC-12, verbatim` · [Full text](../spec.md)

### AC-13 (US-04) — cross-context

> **Given** successful processing for the current selection,
> **When** the current operation's complete Результат is ready,
> **Then** the page initiates exactly one automatic browser download without a separate download action; the file has the requested output format and matching filename extension, and the Оригінал remains untouched. After handing the file to the browser for download, the page returns to the initial form without reloading: the selected file, Preview, Результат and errors are removed, both dimension limits become empty and format resets to JPEG. File selection is available, transformation controls are disabled or hidden and processing is disabled until another eligible file is selected. No result characteristics or repeat-download action remain on the page. Reset must not interrupt the initiated download and does not wait for confirmation that the browser saved the file to disk. The next selected file starts an independent conversion, including when it is the same file as before.

— `spec.md §5, AC-13, verbatim` · [Full text](../spec.md)

### AC-14 (US-04) — authorization

> **Given** a Результат belongs to a different operation or is no longer available to the current page,
> **When** Власник картинки attempts to retrieve it,
> **Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.

— `spec.md §5, AC-14, verbatim` · [Full text](../spec.md)

### AC-15 (US-05) — error

> **Given** processing is in progress,
> **When** Власник картинки waits, processing fails or the page closes,
> **Then** the form disables file selection, all transformation parameter controls and repeat submission while processing, shows a truthful busy state without fabricated percentages, restores the controls and retry with the selected file and parameters after a recoverable error, and offers no result restoration after closing or reloading the page. Successful completion initiates the automatic download and resets the form as specified in AC-13; only the current operation may initiate that download, and no stale or duplicate completion may initiate it again.

— `spec.md §5, AC-15, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] In backend/main.py, expose POST /api/v1/images/process only now that parsing, timeline and color paths are complete. Call ordinary backend/images.py functions off the asynchronous event loop.
- [ ] Transfer upload ownership to the synchronous worker before processing. Do not allow async FormData cleanup to close an in-use source after raw Task.cancel(); close native resources only when work actually ends.
- [ ] Return complete binary bytes, matching media type and result.jpg/result.png/result.webp attachment header. Map safe 400/413/415/422/500 errors, retain no result ID/lookup and release response buffers on send completion/failure.
- [ ] Extend tests/test_images_api.py with HTTPX format/validation tests plus real socket interruption, raw cancellation, decoder/encoder/send faults, handle/reference cleanup and confidential error/log assertions.

## Edge cases

| Case | Required behavior |
|---|---|
| Async cancellation while native work runs | Worker keeps source alive until it finishes, then releases it. |
| Send fails after response starts | Release output; no guarantee of a later HTTP error body. |
| Another operation or unknown retrieval path | No image lookup or result restoration exists. |

— `spec.md §5, AC-07, AC-11, AC-12, AC-13, AC-14, AC-15, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] tests/test_images_api.py endpoint and ownership regressions pass, including actual socket interruption and raw cancellation, correct binary headers/errors, no retrieval capability and no leaked upload/image/response owners.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
