---
id: "T1"
title: "Bound multipart parsing"
layer: "ports"
deps: []
blocks: ["T8"]
acs: ["AC-11", "AC-12", "AC-16"]
files_hint: ["backend/main.py", "pyproject.toml", "uv.lock", "tests/test_images_api.py", "docs/features/image-resize-convert/contracts/openapi.yaml"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "L" # justified: Parser, contract, regression test and locked dependencies form one boundary change; splitting would separate enforcement from its transport contract.
status: "todo"
dod: "Parser and parameter regressions in tests/test_images_api.py pass, including exact 20,000,000 file bytes and closed partial handles after EOF/disconnection; documented transport bounds match implementation."
file: "docs/features/image-resize-convert/tasks/bound-multipart-parsing.md"
---

# T1 — Bound multipart parsing

## Place in the sequence

- **Blocked by:** None. **Blocks:** T8 — Serve request-scoped image results. **Wave:** 1 (after its prerequisites).
- **Lane:** Shares files with T2, T6, T8, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 46 non-empty lines from Why through Acceptance criteria; 5 implementation/test/config locations in play; L reflects file context, not elapsed work. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As an** Image owner
> **I want** clear validation and processing errors with a retry
> **So that** I can correct my input without unnecessary reselection.

— `spec.md §4, US-05, verbatim` · [Full text](../spec.md)

Bound multipart parsing delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Validation and transformation.** Enforce parameters at the HTTP boundary. Bound upload parsing and validate actual file bytes before expensive decoding. Inspect supported content, static-image rules and selected-image dimensions before full pixel decoding; preserve decoder safety protections and verify decoded dimensions again where a decoder can change them. Apply orientation before calculating dimensions. Use the largest proportional scale not exceeding one or either supplied bound; round each dimension to the nearest whole pixel with halves up and minimum one. The specified 1000 by 333 image with width 500 must become 500 by 167; an unverified library thumbnail rounding rule is not a substitute. Ineffective bounds and same-format requests still normalize the output.

— `sad.md §6, Validation and transformation, verbatim` · [Full text](../sad.md)

> | Input limits | At most 20,000,000 bytes and 40,000,000 decoded pixels of the selected static image; equality allowed | Processing boundary tests before expensive server decoding; selection checks reject empty files and files above the byte limit before preparing a local Preview, while server content, animation and pixel-count checks run on submission |

— `spec.md §6, Input limits, verbatim` · [Full text](../spec.md)

> | Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |

— `spec.md §6, Transient resources, verbatim` · [Full text](../spec.md)

> Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in backend/main.py and image functions in backend/images.py.

— `adr/0001-extend-web-frontend-and-backend-service.md §Decision outcome, ADR-0001, abridged` · [Full text](../adr/0001-extend-web-frontend-and-backend-service.md)

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

### AC-11 (US-05) — error

> **Given** no file, no supplied transformation parameter, an invalid dimension or an unsupported output choice,
> **When** processing is attempted,
> **Then** the system rejects the attempt and explains the reason even when form restrictions are bypassed; dimensions must be positive whole pixel counts, empty dimensions impose no bound, and a supplied output format including the form's default JPEG counts as a parameter. Valid supplied dimensions with no output format produce JPEG; omitting both dimensions and output format remains an error.

— `spec.md §5, AC-11, verbatim` · [Full text](../spec.md)

### AC-12 (US-05) — error

> **Given** an empty, corrupted, unsupported or animated Original, or an input above 20 million bytes or 40 million decoded pixels,
> **When** processing is attempted,
> **Then** the system rejects it with an understandable reason and produces no successful Result; exact limits are allowed, support is determined from actual content, and additional HEIC images are subject to the primary-image rule rather than treated as animation. The form checks only whether the selected file is empty or exceeds the byte limit before preparing Preview; the server checks content, animation and decoded pixel count when processing is submitted, and enforces all input limits even when form restrictions are bypassed.

— `spec.md §5, AC-12, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] In pyproject.toml and uv.lock, add python-multipart and pin the version-sensitive Starlette/parser combination verified by the audit; use the existing uv workflow.
- [ ] In backend/main.py, implement directly tested parsing and parameter validation without exposing an incomplete processing endpoint. Bound actual file bytes, multipart fields/headers/body and close partial spools on every exit, including truncated normal EOF.
- [ ] In contracts/openapi.yaml, document chosen transport representation limits and their HTTP mapping before exposure. Audit budgets are probe settings, not an existing API promise; retain arbitrarily large positive logical bounds within the documented representation and no product maximum dimension.
- [ ] In tests/test_images_api.py, cover empty/missing/duplicate parts, malformed and truncated multipart, byte equality/overflow, empty dimensions, missing-all-parameters, explicit empty format, invalid dimensions, dimensions-only JPEG and cancellation.

## Edge cases

| Case | Required behavior |
|---|---|
| Missing closing boundary | Reject malformed multipart and close every partial spool. |
| Missing all parameters versus omitted format with dimensions | Reject the former; use JPEG for the latter. |
| Multipart overhead or huge dimension text | Enforce documented transport representation separately from the file allowance; do not invent a numeric dimension maximum. |

— `spec.md §5, AC-11, AC-12, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] Parser and parameter regressions in tests/test_images_api.py pass, including exact 20,000,000 file bytes and closed partial handles after EOF/disconnection; documented transport bounds match implementation.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
