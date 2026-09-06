---
id: "T5"
title: "Resize and normalize output"
layer: "domain"
deps: ["T4"]
blocks: ["T6"]
acs: ["AC-04", "AC-05", "AC-06", "AC-07", "AC-08", "AC-09"]
files_hint: ["backend/images.py", "tests/test_images.py", "tests/fixtures/images/"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "tests/test_images.py geometry/format regressions pass for the exact AC-04/05 examples, no enlargement, all 12 input/output combinations, alpha handling and service-metadata removal; color completion remains explicitly assigned to T6/T7."
file: "docs/features/image-resize-convert/tasks/resize-and-normalize-output.md"
---

# T5 — Resize and normalize output

## Place in the sequence

- **Blocked by:** T4 — Handle fragmented HEIF timelines. **Blocks:** T6 — Preserve compatible color profiles. **Wave:** 4 (after its prerequisites).
- **Lane:** Shares files with T2, T3, T4, T6, T7, T8, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 57 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** to set either or both Максимальні розміри independently
> **So that** the Результат fits my bounds without cropping, distortion or enlargement.

— `spec.md §4, US-02, verbatim` · [Full text](../spec.md)

Resize and normalize output delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Validation and transformation.** Enforce parameters at the HTTP boundary. Bound upload parsing and validate actual file bytes before expensive decoding. Inspect supported content, static-image rules and selected-image dimensions before full pixel decoding; preserve decoder safety protections and verify decoded dimensions again where a decoder can change them. Apply orientation before calculating dimensions. Use the largest proportional scale not exceeding one or either supplied bound; round each dimension to the nearest whole pixel with halves up and minimum one. The specified 1000 by 333 image with width 500 must become 500 by 167; an unverified library thumbnail rounding rule is not a substitute. Ineffective bounds and same-format requests still normalize the output.

— `sad.md §6, Validation and transformation, verbatim` · [Full text](../sad.md)

> | Input limits | At most 20,000,000 bytes and 40,000,000 decoded pixels of the selected static image; equality allowed | Processing boundary tests before expensive server decoding; selection checks reject empty files and files above the byte limit before preparing a local Preview, while server content, animation and pixel-count checks run on submission |

— `spec.md §6, Input limits, verbatim` · [Full text](../spec.md)

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

### AC-04 (US-02) — happy

> **Given** a correctly oriented Оригінал measuring 2400 by 1200 pixels,
> **When** Власник картинки sets only maximum width to 1200,
> **Then** the Результат measures 1200 by 600 pixels; a height-only limit of 300 yields 600 by 300; both width 1200 and height 300 yield 600 by 300.

— `spec.md §5, AC-04, verbatim` · [Full text](../spec.md)

### AC-05 (US-02) — domain invariant

> **Given** supplied Максимальні розміри,
> **When** Власник картинки processes the Оригінал,
> **Then** the Результат uses the largest proportional scale that fits all supplied bounds without enlarging the oriented original, with no additional reduction. Each scaled dimension is rounded to the nearest whole pixel, with exact half-pixel values rounded up and a minimum of one pixel. The Результат does not exceed either supplied bound or either original oriented dimension, contains the whole image and preserves aspect ratio subject only to this whole-pixel rounding and minimum. An oriented original of 1000 by 333 pixels with maximum width 500 produces a result of 500 by 167 pixels.

— `spec.md §5, AC-05, verbatim` · [Full text](../spec.md)

### AC-06 (US-02, US-03) — happy

> **Given** an Оригінал measuring 800 by 600 pixels,
> **When** Власник картинки supplies maximum width 1600 or selects the same output format as the original,
> **Then** processing remains allowed because a parameter is supplied; an ineffective dimension limit leaves dimensions unchanged, and a same-format operation still produces the agreed normalized Результат.

— `spec.md §5, AC-06, verbatim` · [Full text](../spec.md)

### AC-07 (US-03) — happy

> **Given** a supported static JPEG, PNG, WebP or HEIC Оригінал,
> **When** Власник картинки chooses JPEG, PNG or WebP and processes it,
> **Then** a decodable Результат is produced in the chosen format; JPEG is the initial output choice for every input, including JPEG itself, and there is no guarantee of smaller file size or byte-identical output.

— `spec.md §5, AC-07, verbatim` · [Full text](../spec.md)

### AC-08 (US-03) — domain invariant

> **Given** a selected Оригінал, whether or not its transparency is known or Preview is available,
> **When** Власник картинки chooses JPEG,
> **Then** the form always shows a conditional warning before processing: if the image has transparency, it will become white; this also applies when JPEG is selected by default and requires no advance transparency detection. The JPEG Результат uses white behind partial and full transparency; PNG and WebP output retain transparency.

— `spec.md §5, AC-08, verbatim` · [Full text](../spec.md)

### AC-09 (US-01, US-03) — domain invariant

> **Given** an Оригінал with orientation information or service metadata,
> **When** Власник картинки processes it,
> **Then** the Результат and any available Preview have the correct visible orientation, and dimension limits apply to that orientation; the Результат omits GPS, camera and textual metadata while retaining information required for correct color interpretation.

— `spec.md §5, AC-09, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] In backend/images.py, calculate the largest fitting scale at most one on oriented dimensions; round halves up, minimum one pixel, with no extra reduction.
- [ ] Encode JPEG/PNG/WebP, composite partial/full alpha onto white for JPEG and retain alpha otherwise. Strip service metadata after orientation; carry compatible color information forward for T6/T7 rather than clearing it wholesale.
- [ ] Extend tests/test_images.py with AC-04 exact sizes, 500x167 rounding, one-pixel extremes, ineffective bounds, same-format normalization, all 12 format combinations, alpha and metadata/orientation controls.

## Edge cases

| Case | Required behavior |
|---|---|
| 1000x333 with width 500 | Produce 500x167 using half-up rounding. |
| Both bounds exceed original | Keep original oriented size but still normalize. |
| Partial transparency to JPEG | Composite onto white; PNG/WebP keep alpha. |

— `spec.md §5, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] tests/test_images.py geometry/format regressions pass for the exact AC-04/05 examples, no enlargement, all 12 input/output combinations, alpha handling and service-metadata removal; color completion remains explicitly assigned to T6/T7.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
