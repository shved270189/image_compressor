---
id: T2
title: "Parse and convert optional size_limit fields"
layer: "ports"
deps: ["T1"]
blocks: ["T3"]
acs: ["AC-01", "AC-03", "AC-08", "AC-12"]
files_hint: ["backend/main.py", "tests/test_images_api.py"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
dod: "tests/test_images_api.py accepts empty or omitted size_limit with existing geometry, accepts size_limit-only JPEG, converts 0.5 mb to 524288 and 200 kb to 204800, and returns 422 for zero, negative, non-numeric size_limit and missing/invalid size_unit without a result."
file: "docs/features/image-size-limit/tasks/parse-and-convert-size-limit.md"
---

# T2 — Parse and convert optional size_limit fields

## Place in the sequence

- **Blocked by:** T1 — Extra-shrink encoded output to meet a byte bound · **Blocks:** T3 — Signal miss versus met-limit with response headers · **Wave:** 2, after T1.
- **Lane:** shares `backend/main.py` and `tests/test_images_api.py` with T3 — serialized. Do not add miss headers here.

## Why (user story)

> **As a** Власник картинки
> **I want** to set an independently optional Ліміт ваги as a positive decimal with a unit choice of Mb or Kb to the left of the number, Mb initially selected, empty meaning no bound
> **So that** the Результат can target a file-size budget, and a supplied Ліміт ваги counts as a transformation parameter (processing may run with only that bound and the initial JPEG).
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

> **As a** Власник картинки
> **I want** zero, negative or non-positive Ліміт ваги rejected with a clear reason
> **So that** I can fix the field without losing the Оригінал. Empty remains valid and means no bound.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task accepts, converts or rejects the multipart bound at the HTTP boundary.

## Inlined context

> Optional multipart fields `size_limit` (positive decimal) and `size_unit` (`mb` or `kb`); empty omits the bound; server converts with 1 Mb = 1,048,576 and 1 Kb = 1,024.
>
> — `sad.md §8, Bound transport, abridged` · full text: [sad.md](../sad.md)

> `backend/main.py` — Multipart validation including Ліміт ваги, byte conversion, response headers, resource ownership
>
> — `sad.md §5, building block view, abridged` · full text: [sad.md](../sad.md)

> Bound empty: apply no result byte bound, keep existing dimension and format rules. Bound is a positive number: accept as a transformation parameter, including JPEG only and no maxima. Bound is zero, negative, or not a positive number: reject, keep Оригінал.
>
> — `sad.md §6, Set optional Ліміт ваги, abridged` · full text: [sad.md](../sad.md)

> **Decision:** Optional request fields `size_limit` and `size_unit` carry the bound; the Application converts them to whole bytes.
>
> — `adr/0002-signal-size-limit-miss-with-headers.md, Decision outcome, abridged` · full text: [adr/0002-signal-size-limit-miss-with-headers.md](../adr/0002-signal-size-limit-miss-with-headers.md)

> **Hard rule:** HTTP validation belongs in `backend/main.py`. Ліміт ваги is not an upload cap. Accept at most 20,000,000 file bytes and 40,000,000 decoded pixels, equality allowed.
>
> — `sad.md §2 and spec.md §6, Input limits, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [openapi.yaml](../contracts/openapi.yaml) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `POST /api/v1/images/process` (`processImage`) · request fields this task handles: `size_limit`, `size_unit`.
- Empty or omitted `size_limit` applies no byte bound and is not a supplied parameter. A positive `size_limit` counts as a transformation parameter, including with omitted maxima and omitted `output_format` (JPEG fallback).
- `size_unit` is `mb` or `kb` when `size_limit` is a positive number; ignored when the bound is empty. `size_unit` alone is not a parameter.
- Errors: `422` `invalidSizeLimit` — `size_limit must be a positive number with mb or kb or left empty.`; `422` `missingSizeUnit` — `size_limit requires size_unit mb or kb.`; `422` `invalidSizeUnit` — `size_unit must be mb or kb.`; `422` `missingParameters` — `Supply dimensions, an output format or a size limit.`
- Conversion: 0.5 mb = 524,288 bytes; 200 kb = 204,800 bytes.

— `contracts/openapi.yaml, operationId processImage, abridged` · full text: [openapi.yaml](../contracts/openapi.yaml)

## Acceptance criteria

### AC-01 — happy

> **Given** a selected Оригінал within the input limits,
> **When** Власник картинки leaves Ліміт ваги empty and processes,
> **Then** no result byte bound is applied and dimension and format behaviour matches the existing form.
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-03 — happy

> **Given** a selected Оригінал and no Максимальні розміри,
> **When** Власник картинки supplies only a Ліміт ваги and leaves output format at the initial JPEG,
> **Then** processing is allowed because a transformation parameter is supplied.
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — error

> **Given** a filled Ліміт ваги that is zero, negative or not a positive number,
> **When** processing is attempted,
> **Then** the system rejects the attempt, explains that Ліміт ваги must be a positive number with Mb or Kb or left empty, produces no Результат, and keeps the Оригінал.
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

### AC-12 — domain invariant

> **Given** a supplied Ліміт ваги,
> **When** the encoded Результат is compared with that bound,
> **Then** the bound in bytes equals the entered number multiplied by 1,048,576 for Mb or by 1,024 for Kb, comparison uses whole bytes of the encoded Результат, and 0.5 Mb equals 524,288 bytes.
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

This task owns the conversion. T1 owns comparing encoded bytes to that integer.

## Checklist

- [ ] In `backend/main.py`, allow text parts `size_limit` and `size_unit`. Raise `max_fields` from 3 to 5.
- [ ] Treat empty `size_limit` as no bound. Convert a positive decimal with `mb` or `kb`. Pass `size_limit_bytes` into `images.process_image`.
- [ ] Reject zero, negative or non-numeric `size_limit`, missing unit on a positive bound, and invalid unit with 422 and no result. Ignore `size_unit` when the bound is empty.
- [ ] Count a valid `size_limit` as a transformation parameter, including JPEG fallback with no maxima. Update the missing-parameter copy to mention a size limit.
- [ ] Extend `tests/test_images_api.py` for empty/omitted bound, size_limit-only JPEG, 0.5 mb / 200 kb conversion, and the 422 cases above.

## Edge cases

| Case | Behaviour |
|---|---|
| Omitted or empty `size_limit` | No bound; existing geometry; `size_unit` ignored |
| Positive `size_limit` without `size_unit` | 422, no result |
| `size_unit=gb` or other value | 422, no result |
| `size_limit=0` or `-1` | 422, no result |
| Huge valid bound | Accepted; simply met |

## Definition of Done

- [ ] tests/test_images_api.py accepts empty or omitted size_limit with existing geometry, accepts size_limit-only JPEG, converts 0.5 mb to 524288 and 200 kb to 204800, and returns 422 for zero, negative, non-numeric size_limit and missing/invalid size_unit without a result.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
