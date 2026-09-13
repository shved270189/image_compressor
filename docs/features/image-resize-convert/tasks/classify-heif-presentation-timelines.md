---
id: "T3"
title: "Classify HEIF presentation timelines"
layer: "domain"
deps: ["T2"]
blocks: ["T4"]
acs: ["AC-10", "AC-12"]
files_hint: ["backend/images.py", "tests/test_images.py", "tests/fixtures/images/"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "HEIF non-fragmented timing regressions in tests/test_images.py pass for real sequences and static edit/composition controls, without using image count or brands as the classification oracle."
file: "docs/features/image-resize-convert/tasks/classify-heif-presentation-timelines.md"
---

# T3 — Classify HEIF presentation timelines

## Place in the sequence

- **Blocked by:** T2 — Decode supported static images. **Blocks:** T4 — Handle fragmented HEIF timelines. **Wave:** 2 (after its prerequisites).
- **Lane:** Shares files with T2, T4, T5, T6, T7, T8, T12; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 47 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As an** Image owner
> **I want** to choose JPEG, PNG or WebP, with JPEG initially selected
> **So that** I receive a Result in the desired supported format.

— `spec.md §4, US-03, verbatim` · [Full text](../spec.md)

Classify HEIF presentation timelines delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

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

> **Required implementation carry-forward.** Complete HEIF edit-list/composition/fragmented timeline handling, preserving non-timed galleries; the diagnostic's `NEEDS_TIMELINE` is never a production accept/reject fallback.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

> Animation is determined from visual-track presentation, not image count or
> brands. The bounded probe proves the mechanism and exposes its coverage limit:
> `NEEDS_TIMELINE` must never silently become either static or animated in the
> feature. Implementation must handle edit lists, composition offsets and
> fragmented timing, preserve non-timed galleries with zero/one presentation
> samples, and reject genuine sequences. See
> [Nokia's technical description](https://nokiatech.github.io/heif/technical.html) and its pinned [presentation-count rule](https://github.com/nokiatech/heif/blob/503194eb85e13434b54797bab9d82ad7f88fd35b/srcs/reader/heifreaderimpl.cpp#L2099).
> Before acceptance, add edit-list/composition/fragmented controls and a complete
> independently generated non-timed track gallery; the current analytic gallery
> controls are timing structures, not decodable camera files. This is required
> implementation work, not a new product/design decision.

— `_audit/pre-tasks-feasibility.md §HEIC and color evidence, verified mechanism, verbatim` · [Full text](../_audit/pre-tasks-feasibility.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-10 (US-01, US-03) — happy

> **Given** a HEIC Original with additional images or high-dynamic-range content,
> **When** Image owner processes it,
> **Then** only the designated primary static image is used; the form explains the general HEIC rules before submission: extra images are omitted and high-dynamic-range content becomes ordinary 8-bit output, with no promise of retaining the original high-dynamic-range appearance; this notice requires no advance server inspection.

— `spec.md §5, AC-10, verbatim` · [Full text](../spec.md)

### AC-12 (US-05) — error

> **Given** an empty, corrupted, unsupported or animated Original, or an input above 20 million bytes or 40 million decoded pixels,
> **When** processing is attempted,
> **Then** the system rejects it with an understandable reason and produces no successful Result; exact limits are allowed, support is determined from actual content, and additional HEIC images are subject to the primary-image rule rather than treated as animation. The form checks only whether the selected file is empty or exceeds the byte limit before preparing Preview; the server checks content, animation and decoded pixel count when processing is submitted, and enforces all input limits even when form restrictions are bypassed.

— `spec.md §5, AC-12, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] In backend/images.py, reuse the audited bounded HEIF inspection approach, completing non-fragmented presentation counting with edit lists and composition offsets.
- [ ] Classify visible presentation rather than brands or image count. Preserve zero/one-presentation static galleries and reject genuine sequences, including spoofed sequence brands. Keep this internal until T4 completes fragmented handling.
- [ ] Extend tests/test_images.py and tests/fixtures/images with edit-list, dwell/empty-edit, composition-offset, malformed-box and spoofed-brand controls with independently specified presentation expectations.

## Edge cases

| Case | Required behavior |
|---|---|
| Multiple static items | Accept under the primary-image rule. |
| Removed sequence brands | Still reject a genuine presentation sequence. |
| Malformed timeline structures | Reject corrupted content safely; bound parsing by available input. |

— `spec.md §5, AC-10, AC-12, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] HEIF non-fragmented timing regressions in tests/test_images.py pass for real sequences and static edit/composition controls, without using image count or brands as the classification oracle.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
