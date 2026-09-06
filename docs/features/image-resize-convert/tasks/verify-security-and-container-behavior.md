---
id: "T12"
title: "Verify security and container behavior"
layer: "tests"
deps: ["T8"]
blocks: ["T13"]
acs: ["AC-07", "AC-09", "AC-10", "AC-11", "AC-12", "AC-14", "AC-16"]
files_hint: ["tests/test_images_api.py", "tests/test_images.py", "tests/test_smoke.py", "docs/features/image-resize-convert/_audit/security-container-acceptance.md"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "Host feature tests, Linux image/color verification and live-container smoke pass; _audit/security-container-acceptance.md records closed ownership checks, confidential errors/logs and Security Lead acceptance."
file: "docs/features/image-resize-convert/tasks/verify-security-and-container-behavior.md"
---

# T12 — Verify security and container behavior

## Place in the sequence

- **Blocked by:** T8 — Serve request-scoped image results. **Blocks:** T13 — Document the completed workflow. **Wave:** 8 (after its prerequisites).
- **Lane:** Shares files with T1, T2, T3, T4, T5, T6, T7, T8; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 68 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** clear validation and processing errors with a retry
> **So that** I can correct my input without unnecessary reselection.

— `spec.md §4, US-05, verbatim` · [Full text](../spec.md)

Verify security and container behavior delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Failure and interruption.** Recoverable validation, processing and transfer errors restore controls with the same selected file and parameters. Closing or reloading invalidates browser work without restoration. The server closes upload handles and image resources on success, errors and interruption; native work may finish before its resources can be closed. The response owns encoded output only until response completion or failure. No prior result can be restored. The diagram shows logical lifecycle completion, not permission to keep a decoded image alive throughout a response unnecessarily.

— `sad.md §6, Failure and interruption, verbatim` · [Full text](../sad.md)

> | Input limits | At most 20,000,000 bytes and 40,000,000 decoded pixels of the selected static image; equality allowed | Processing boundary tests before expensive server decoding; selection checks reject empty files and files above the byte limit before preparing a local Preview, while server content, animation and pixel-count checks run on submission |

— `spec.md §6, Input limits, verbatim` · [Full text](../spec.md)

> | Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |

— `spec.md §6, Transient resources, verbatim` · [Full text](../spec.md)

> Use the pillow-heif Pillow plugin. Register and configure it at application initialization, retain a strict accepted-format boundary, and process only the primary static image. HEIC validation must distinguish additional still images from animation rather than blindly rejecting the plugin's multi-frame flag. Disable unused thumbnail, depth and auxiliary handling without removing alpha needed by the primary image.

— `adr/0002-load-heic-through-pillow-plugin.md §Decision outcome, ADR-0002, verbatim` · [Full text](../adr/0002-load-heic-through-pillow-plugin.md)

> Preserve compatible color interpretation instead of converting every image to sRGB. When a pixel color model must change, use ImageCms where applicable and attach only a profile matching the resulting pixels. Apply orientation before removing orientation/service metadata. Remove GPS, camera, EXIF, XMP and textual service metadata. Composite transparency onto white for JPEG and retain alpha for PNG and WebP.

— `adr/0003-preserve-compatible-color-profiles.md §Decision outcome, ADR-0003, verbatim` · [Full text](../adr/0003-preserve-compatible-color-profiles.md)

> Use one processing request with a complete binary response and no result ID, lookup or second retrieval request. Lock file selection, parameters and repeated submission while it is pending. On complete success, verify currentness and consume the operation once, initiate a native download with the matching filename extension, and reset the form. A separate handoff owner releases the result Blob URL when safe; resetting form state must not revoke it prematurely. Retain current input after recoverable errors. Invalidate page work on teardown and release server resources on success, failure and interruption, allowing already-running native decoding to finish before its resources are released.

— `adr/0004-return-results-within-the-current-operation.md §Decision outcome, ADR-0004, verbatim` · [Full text](../adr/0004-return-results-within-the-current-operation.md)

> Preserve the verified worker ownership transfer and partial-parser cleanup. Document bounded multipart transport representation and error mapping in the implementation contract without inventing a numeric maximum dimension. Pin and verify the version-sensitive Starlette and bundled LittleCMS bindings.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

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

### AC-09 (US-01, US-03) — domain invariant

> **Given** an Оригінал with orientation information or service metadata,
> **When** Власник картинки processes it,
> **Then** the Результат and any available Preview have the correct visible orientation, and dimension limits apply to that orientation; the Результат omits GPS, camera and textual metadata while retaining information required for correct color interpretation.

— `spec.md §5, AC-09, verbatim` · [Full text](../spec.md)

### AC-10 (US-01, US-03) — happy

> **Given** a HEIC Оригінал with additional images or high-dynamic-range content,
> **When** Власник картинки processes it,
> **Then** only the designated primary static image is used; the form explains the general HEIC rules before submission: extra images are omitted and high-dynamic-range content becomes ordinary 8-bit output, with no promise of retaining the original high-dynamic-range appearance; this notice requires no advance server inspection.

— `spec.md §5, AC-10, verbatim` · [Full text](../spec.md)

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

### AC-14 (US-04) — authorization

> **Given** a Результат belongs to a different operation or is no longer available to the current page,
> **When** Власник картинки attempts to retrieve it,
> **Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.

— `spec.md §5, AC-14, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] Extend existing tests/test_images_api.py and tests/test_images.py only for remaining specified security/platform gaps: actual supported-format limits, post-decode dimensions, malformed/animated inputs, parser EOF, raw/socket cancellation, output failure and safe logs.
- [ ] Preserve and extend tests/test_smoke.py for structural regressions. Build the real application image, verify Linux HEIC/color bindings and run shared smoke against it through SMOKE_BASE_URL; retain non-root execution and API/assets behavior.
- [ ] Record commands/results and explicit handle/reference cleanup evidence in _audit/security-container-acceptance.md. Allocator RSS is not an ownership oracle; no timing benchmarks or image/filename/metadata logging.
- [ ] Obtain Security Lead review of untrusted decoding, multipart bounds and confidentiality before acceptance. Return defects to their owning task rather than expanding this verification task into unrelated production edits.

## Edge cases

| Case | Required behavior |
|---|---|
| Exact byte/pixel boundary | Accept equality; reject excess before expensive decoding and recheck decoded size. |
| Canceled parser/worker/response | Release each owner at its real lifecycle boundary. |
| Unknown /api path with HTML Accept | Preserve 404; never serve SPA as an API result. |

— `spec.md §5, AC-07, AC-09, AC-10, AC-11, AC-12, AC-14, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] Host feature tests, Linux image/color verification and live-container smoke pass; _audit/security-container-acceptance.md records closed ownership checks, confidential errors/logs and Security Lead acceptance.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
