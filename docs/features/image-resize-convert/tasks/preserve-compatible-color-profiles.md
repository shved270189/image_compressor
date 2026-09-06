---
id: "T6"
title: "Preserve compatible color profiles"
layer: "domain"
deps: ["T5"]
blocks: ["T7"]
acs: ["AC-09"]
files_hint: ["backend/images.py", "pyproject.toml", "uv.lock", "tests/test_images.py", "tests/fixtures/images/"]
owner: "Tech Lead"
estimate: "8h"
context_budget: "L" # justified: Profile implementation, regression fixtures and version-sensitive binding pins must be reviewed together.
status: "todo"
dod: "tests/test_images.py SDR color checks pass on macOS and Linux for compatible ICC, pixel-model conversions, NCLX-only and PNG gAMA/cHRM sources; emitted profiles match output pixels while identifying metadata is absent."
file: "docs/features/image-resize-convert/tasks/preserve-compatible-color-profiles.md"
---

# T6 — Preserve compatible color profiles

## Place in the sequence

- **Blocked by:** T5 — Resize and normalize output. **Blocks:** T7 — Convert HDR to ordinary SDR output. **Wave:** 5 (after its prerequisites).
- **Lane:** Shares files with T1, T2, T3, T4, T5, T7, T8, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 43 non-empty lines from Why through Acceptance criteria; 5 implementation/test/config locations in play; L reflects file context, not elapsed work. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** to choose JPEG, PNG or WebP, with JPEG initially selected
> **So that** I receive a Результат in the desired supported format.

— `spec.md §4, US-03, verbatim` · [Full text](../spec.md)

Preserve compatible color profiles delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Validation and transformation.** Enforce parameters at the HTTP boundary. Bound upload parsing and validate actual file bytes before expensive decoding. Inspect supported content, static-image rules and selected-image dimensions before full pixel decoding; preserve decoder safety protections and verify decoded dimensions again where a decoder can change them. Apply orientation before calculating dimensions. Use the largest proportional scale not exceeding one or either supplied bound; round each dimension to the nearest whole pixel with halves up and minimum one. The specified 1000 by 333 image with width 500 must become 500 by 167; an unverified library thumbnail rounding rule is not a substitute. Ineffective bounds and same-format requests still normalize the output.

— `sad.md §6, Validation and transformation, verbatim` · [Full text](../sad.md)

> | Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |

— `spec.md §6, Transient resources, verbatim` · [Full text](../spec.md)

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

## Checklist

- [ ] In backend/images.py, preserve compatible ICC and transform incompatible pixel models using ImageCms; do not universally convert to sRGB or attach mismatched source profiles.
- [ ] Complete SDR NCLX and PNG gAMA/cHRM interpretation using the audited bundled LittleCMS mechanism. Pin and verify version-sensitive bindings through pyproject.toml/uv.lock, without adding a separate color engine.
- [ ] Extend tests/test_images.py and fixtures for compatible wide gamut, RGB/gray/CMYK and applicable profile conversions, alpha, NCLX-only and non-ICC PNG controls across output formats; compare independent color expectations on macOS/Linux.

## Edge cases

| Case | Required behavior |
|---|---|
| Source profile describes another pixel model | Transform pixels and attach a matching profile. |
| NCLX or PNG color information without ICC | Preserve equivalent interpretation rather than silently dropping or relabeling it. |
| Compatible wide-gamut profile | Preserve it without unnecessary universal sRGB conversion. |

— `spec.md §5, AC-09, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] tests/test_images.py SDR color checks pass on macOS and Linux for compatible ICC, pixel-model conversions, NCLX-only and PNG gAMA/cHRM sources; emitted profiles match output pixels while identifying metadata is absent.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
