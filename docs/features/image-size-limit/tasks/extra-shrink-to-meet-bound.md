---
id: T1
title: "Extra-shrink encoded output to meet a byte bound"
layer: "domain"
deps: []
blocks: ["T2"]
acs: ["AC-04", "AC-05", "AC-12"]
files_hint: ["backend/images.py", "tests/test_images.py"]
owner: "Tech Lead"
estimate: "M"
context_budget: "M"
status: "todo"
dod: "tests/test_images.py extra-shrink and empty-bound geometry cases pass: 2400x1200 with width 1200 stays 1200x600 when unbound; a tighter bound yields width under 1200 at 2:1; one-pixel miss still returns a file; comparison uses whole encoded bytes."
file: "docs/features/image-size-limit/tasks/extra-shrink-to-meet-bound.md"
---

# T1 — Extra-shrink encoded output to meet a byte bound

## Place in the sequence

- **Blocked by:** none · **Blocks:** T2 — Parse and convert optional size_limit fields · **Wave:** 1, with T4.
- **Lane:** own lane for `backend/images.py` / `tests/test_images.py`. T2 consumes the new optional `size_limit_bytes` argument after this lands.

## Why (user story)

> **As an** Image owner
> **I want** a supplied Size limit to outrank Maximum dimensions as a floor
> **So that** the system may reduce pixels below those maxima and below the Original to meet the budget, while maxima remain a ceiling, without cropping, stretching, enlargement or a silent format change.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task adds extra-shrink in image functions so a byte bound can undercut the dimension ceiling.

## Inlined context

> The committed approach is one form with an independent Size limit. When supplied, it is the primary constraint: the result may use fewer pixels than the supplied maxima and the original, without cropping, stretching, enlargement or a silent format change.
>
> — `spec.md §1, committed approach, abridged` · full text: [spec.md](../spec.md)

> Empty Size limit keeps the current geometry rule in `output_size`: largest proportional fit to supplied maxima, no extra reduction. A supplied bound is the primary constraint: after that ceiling, `backend/images.py` may reduce pixels below maxima and below the Original, without cropping, stretching, enlargement or a silent format change, and stop at the largest proportional size and highest encoding quality that already meets the bound. One pixel and the smallest file of the chosen format that still exceed the bound are a miss, not a rejection without a file. The exact search procedure is task-level provided AC-05 holds.
>
> — `sad.md §4, Apply bound-driven extra shrink, abridged` · full text: [sad.md](../sad.md)

> `backend/images.py` — Existing decode/orient/encode plus extra-shrink search when a bound is supplied
>
> — `sad.md §5, building block view, abridged` · full text: [sad.md](../sad.md)

> Bound omitted: fit maxima only, no extra shrink. Bound supplied and encoded bytes meet it: extra-shrink to largest proportional fit that meets the bound. Bound supplied and even one pixel exceeds it: encode smallest chosen-format file. Never exceed maxima or original, never enlarge, crop, stretch, or change format. Halves round up, minimum one pixel.
>
> — `sad.md §6, Shrink below dimension ceiling, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Extra-shrink search procedure is not locked. The implementer chooses the search in `backend/images.py` as long as AC-05 holds (largest proportional size and highest encoding quality that already meets the bound; nearest-pixel rounding, halves up, minimum one pixel).
>
> — `sad.md §11, Accepted debt, verbatim` · full text: [sad.md](../sad.md)

> **Hard rule:** HTTP validation belongs in `backend/main.py`; extra-shrink and encoding belong in `backend/images.py`.
>
> — `sad.md §2, Technical constraints, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [openapi.yaml](../contracts/openapi.yaml) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-04 — domain invariant

> **Given** supplied Maximum dimensions and an empty Size limit,
> **When** Image owner processes the Original,
> **Then** the Result uses the largest proportional scale that fits all supplied bounds without enlarging and with no additional reduction. An oriented original of 2400 by 1200 pixels with only maximum width 1200 yields 1200 by 600.
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

### AC-05 — domain invariant

> **Given** a Size limit and optional Maximum dimensions,
> **When** Image owner processes the Original,
> **Then** the Result never exceeds any supplied dimension bound or either original oriented dimension, never enlarges, never crops or stretches, and keeps the chosen output format. Additional reduction happens only while the encoded file is larger than the Size limit and stops at the largest proportional size and highest encoding quality the chosen format allows that already meets the bound. If even one pixel and the smallest file of that format still exceed the bound, that is a miss under AC-07, not a rejection without a file. Each scaled dimension is rounded to the nearest whole pixel, with exact half-pixel values rounded up and a minimum of one pixel. An oriented original of 2400 by 1200 pixels with maximum width 1200 and a Size limit smaller than the 1200-by-600 encoding yields a result shorter than 1200 in width, with aspect ratio 2 to 1 subject to that rounding.
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-12 — domain invariant

> **Given** a supplied Size limit,
> **When** the encoded Result is compared with that bound,
> **Then** the bound in bytes equals the entered number multiplied by 1,048,576 for Mb or by 1,024 for Kb, comparison uses whole bytes of the encoded Result, and 0.5 Mb equals 524,288 bytes.
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

This task owns the whole-byte comparison given `size_limit_bytes`. T2 owns converting the entered number and unit.

## Checklist

- [ ] Add optional `size_limit_bytes=None` to `process_image` in `backend/images.py`. Existing callers stay valid.
- [ ] When the bound is omitted, keep `output_size` as the only geometry step. Preserve the 2400-by-1200 / width-1200 → 1200-by-600 case.
- [ ] When the bound is supplied, encode in the chosen format and reduce pixels and encoding quality only while encoded bytes exceed the bound. Stop at the largest proportional size and highest quality that already meets it. Do not crop, stretch, enlarge or change format.
- [ ] If one pixel and the smallest chosen-format file still exceed the bound, return that file. Do not raise a client-error rejection.
- [ ] Extend `tests/test_images.py` with empty-bound geometry, extra-shrink below the ceiling, one-pixel miss returning bytes, and whole-byte comparison against a bound already expressed in bytes.

## Edge cases

| Case | Behaviour |
|---|---|
| Bound omitted | Existing largest-fit geometry; no extra shrink |
| Bound larger than the ceiling encoding | Keep ceiling size; still meet the bound |
| Bound smaller than the 1200-by-600 encoding of 2400-by-1200 with width 1200 | Width under 1200, aspect 2:1 after rounding |
| One pixel still over the bound | Return that file; miss is T3's header, not a raise |
| Half-pixel scale | Round nearest, exact halves up, minimum one pixel |

## Definition of Done

- [ ] tests/test_images.py extra-shrink and empty-bound geometry cases pass: 2400x1200 with width 1200 stays 1200x600 when unbound; a tighter bound yields width under 1200 at 2:1; one-pixel miss still returns a file; comparison uses whole encoded bytes.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
