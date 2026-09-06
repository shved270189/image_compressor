---
id: "T7"
title: "Convert HDR to ordinary SDR output"
layer: "domain"
deps: ["T6"]
blocks: ["T8"]
acs: ["AC-09", "AC-10"]
files_hint: ["backend/images.py", "tests/test_images.py", "tests/fixtures/images/"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "tests/test_images.py HDR controls pass on macOS/Linux: real HLG and independent HLG/PQ anchors produce ordinary 8-bit output with matching color profiles, primary-image semantics and resource cleanup."
file: "docs/features/image-resize-convert/tasks/convert-hdr-to-ordinary-sdr-output.md"
---

# T7 — Convert HDR to ordinary SDR output

## Place in the sequence

- **Blocked by:** T6 — Preserve compatible color profiles. **Blocks:** T8 — Serve request-scoped image results. **Wave:** 6 (after its prerequisites).
- **Lane:** Shares files with T2, T3, T4, T5, T6, T8, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 50 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** to choose JPEG, PNG or WebP, with JPEG initially selected
> **So that** I receive a Результат in the desired supported format.

— `spec.md §4, US-03, verbatim` · [Full text](../spec.md)

Convert HDR to ordinary SDR output delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Validation and transformation.** Enforce parameters at the HTTP boundary. Bound upload parsing and validate actual file bytes before expensive decoding. Inspect supported content, static-image rules and selected-image dimensions before full pixel decoding; preserve decoder safety protections and verify decoded dimensions again where a decoder can change them. Apply orientation before calculating dimensions. Use the largest proportional scale not exceeding one or either supplied bound; round each dimension to the nearest whole pixel with halves up and minimum one. The specified 1000 by 333 image with width 500 must become 500 by 167; an unverified library thumbnail rounding rule is not a substitute. Ineffective bounds and same-format requests still normalize the output.

— `sad.md §6, Validation and transformation, verbatim` · [Full text](../sad.md)

> | Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |

— `spec.md §6, Transient resources, verbatim` · [Full text](../spec.md)

> Use the pillow-heif Pillow plugin. Register and configure it at application initialization, retain a strict accepted-format boundary, and process only the primary static image. HEIC validation must distinguish additional still images from animation rather than blindly rejecting the plugin's multi-frame flag. Disable unused thumbnail, depth and auxiliary handling without removing alpha needed by the primary image.

— `adr/0002-load-heic-through-pillow-plugin.md §Decision outcome, ADR-0002, verbatim` · [Full text](../adr/0002-load-heic-through-pillow-plugin.md)

> Preserve compatible color interpretation instead of converting every image to sRGB. When a pixel color model must change, use ImageCms where applicable and attach only a profile matching the resulting pixels. Apply orientation before removing orientation/service metadata. Remove GPS, camera, EXIF, XMP and textual service metadata. Composite transparency onto white for JPEG and retain alpha for PNG and WebP.

— `adr/0003-preserve-compatible-color-profiles.md §Decision outcome, ADR-0003, verbatim` · [Full text](../adr/0003-preserve-compatible-color-profiles.md)

> Cover supported decoder/color combinations and validate dimensions before and after decode. Pin and verify the version-sensitive Starlette and bundled LittleCMS bindings.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

> The verified color route uses LittleCMS already bundled with Pillow: create an
> RGB ICC from primaries/white point and gamma or sampled transfer curves, then
> use normal ImageCms transforms when required. The probe accesses exported
> LittleCMS functions through `ctypes` and Pillow's `_imagingcms` extension.
> This binding is version/platform-sensitive; pin and verify the implementation
> builds. No additional color-engine dependency is introduced by this experiment.
> HLG inverse OETF and normalized PQ EOTF map the full source range into SDR;
> the output keeps source primaries with an SDR transfer curve. HLG is scene-relative
> inverse OETF, not a display OOTF; PQ is EOTF normalized by 10,000 cd/m².
> Transfer equations follow [BT.2100](https://www.itu.int/rec/r-rec-bt.2100). This deliberately
> does not promise original HDR display appearance or universal sRGB conversion.
> The discarded metadata-clearing path lost NCLX/gAMA/HLG interpretation.

— `_audit/pre-tasks-feasibility.md §HEIC and color evidence, verified mechanism, verbatim` · [Full text](../_audit/pre-tasks-feasibility.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

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

## Checklist

- [ ] In backend/images.py, apply the audited HLG inverse OETF and normalized PQ EOTF color route to ordinary 8-bit SDR, preserving source primaries with a matching SDR profile.
- [ ] Keep conversion inside the common Pillow/ImageCms pipeline and ensure primary alpha, orientation and service-metadata removal survive the HDR path.
- [ ] Extend tests/test_images.py with the pinned real HLG fixture and independent HLG/PQ analytic anchors for all output formats on macOS/Linux; describe fixture limitations without claiming a photographed PQ fixture.

## Edge cases

| Case | Required behavior |
|---|---|
| HDR appearance differs | Output ordinary 8-bit SDR; promise no original HDR appearance. |
| Extra HEIC images | Process only the primary, including the HDR path. |
| HLG versus PQ | Use their distinct verified transfer functions, not one shared gamma guess. |

— `spec.md §5, AC-09, AC-10, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] tests/test_images.py HDR controls pass on macOS/Linux: real HLG and independent HLG/PQ anchors produce ordinary 8-bit output with matching color profiles, primary-image semantics and resource cleanup.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
