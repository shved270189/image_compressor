---
id: "T2"
title: "Decode supported static images"
layer: "domain"
deps: []
blocks: ["T3"]
acs: ["AC-07", "AC-09", "AC-10", "AC-12", "AC-16"]
files_hint: ["backend/images.py", "backend/main.py", "pyproject.toml", "uv.lock", "tests/test_images.py", "tests/fixtures/images/"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "L" # justified: Decoder code, initialization, manifests, lockfile and fixtures are one testable plugin integration.
status: "todo"
dod: "tests/test_images.py decoding regressions pass for all four input formats, non-first HEIC primary and pre/post-decode pixel boundaries; decoding exceptions release every owned image."
file: "docs/features/image-resize-convert/tasks/decode-supported-static-images.md"
---

# T2 — Decode supported static images

## Place in the sequence

- **Blocked by:** None. **Blocks:** T3 — Classify HEIF presentation timelines. **Wave:** 1 (after its prerequisites).
- **Lane:** Shares files with T1, T3, T4, T5, T6, T7, T8, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 56 non-empty lines from Why through Acceptance criteria; 6 implementation/test/config locations in play; L reflects file context, not elapsed work. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** to choose JPEG, PNG or WebP, with JPEG initially selected
> **So that** I receive a Результат in the desired supported format.

— `spec.md §4, US-03, verbatim` · [Full text](../spec.md)

Decode supported static images delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

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

> Use the pillow-heif Pillow plugin. Register and configure it at application initialization, retain a strict accepted-format boundary, and process only the primary static image. HEIC validation must distinguish additional still images from animation rather than blindly rejecting the plugin's multi-frame flag. Disable unused thumbnail, depth and auxiliary handling without removing alpha needed by the primary image.

— `adr/0002-load-heic-through-pillow-plugin.md §Decision outcome, ADR-0002, verbatim` · [Full text](../adr/0002-load-heic-through-pillow-plugin.md)

> Preserve compatible color interpretation instead of converting every image to sRGB. When a pixel color model must change, use ImageCms where applicable and attach only a profile matching the resulting pixels. Apply orientation before removing orientation/service metadata. Remove GPS, camera, EXIF, XMP and textual service metadata. Composite transparency onto white for JPEG and retain alpha for PNG and WebP.

— `adr/0003-preserve-compatible-color-profiles.md §Decision outcome, ADR-0003, verbatim` · [Full text](../adr/0003-preserve-compatible-color-profiles.md)

> Cover supported decoder/color combinations and validate dimensions before and after decode. Pin and verify the version-sensitive Starlette and bundled LittleCMS bindings.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

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

### AC-12 (US-05) — error

> **Given** an empty, corrupted, unsupported or animated Оригінал, or an input above 20 million bytes or 40 million decoded pixels,
> **When** processing is attempted,
> **Then** the system rejects it with an understandable reason and produces no successful Результат; exact limits are allowed, support is determined from actual content, and additional HEIC images are subject to the primary-image rule rather than treated as animation. The form checks only whether the selected file is empty or exceeds the byte limit before preparing Preview; the server checks content, animation and decoded pixel count when processing is submitted, and enforces all input limits even when form restrictions are bypassed.

— `spec.md §5, AC-12, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] Add pillow-heif through pyproject.toml and uv.lock; configure its Pillow plugin once at application initialization in backend/main.py. Pin the audited version-sensitive image stack.
- [ ] Create ordinary functions in backend/images.py for content detection, designated HEIC primary selection, safe decoding and explicit image ownership. Disable unneeded thumbnail/depth/auxiliary work while preserving primary alpha.
- [ ] Check selected-image pixels before expensive decoding and again after decode; preserve decoder protections and apply orientation once. Reject known animated PNG/WebP; HEIF timeline completeness is delivered by T3/T4 before any public route exists.
- [ ] Add tests/test_images.py and pinned or generated tests/fixtures/images controls for the four actual input formats, non-first HEIC primary, alpha, orientation, corrupt/disguised/unsupported input, inclusive pixels and resource release.

## Edge cases

| Case | Required behavior |
|---|---|
| HEIC primary is not first | Decode only the designated primary; extra still images are not animation. |
| Decoder changes dimensions | Recheck the 40,000,000-pixel limit after decode. |
| Filename or MIME disguises content | Use actual content and preserve decoder safety protections. |

— `spec.md §5, AC-07, AC-09, AC-10, AC-12, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] tests/test_images.py decoding regressions pass for all four input formats, non-first HEIC primary and pre/post-decode pixel boundaries; decoding exceptions release every owned image.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
