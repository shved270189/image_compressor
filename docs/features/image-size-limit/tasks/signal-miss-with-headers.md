---
id: T3
title: "Signal miss versus met-limit with response headers"
layer: "ports"
deps: ["T2"]
blocks: ["T5", "T6"]
acs: ["AC-06", "AC-07"]
files_hint: ["backend/main.py", "tests/test_images_api.py"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
dod: "tests/test_images_api.py 200 responses omit X-Result-Bytes and X-Size-Limit-Met when the bound is omitted; a met bound sends both with X-Size-Limit-Met true and bytes at most the bound; an unattainable bound still returns 200 with X-Size-Limit-Met false and the encoded size."
file: "docs/features/image-size-limit/tasks/signal-miss-with-headers.md"
---

# T3 — Signal miss versus met-limit with response headers

## Place in the sequence

- **Blocked by:** T2 — Parse and convert optional size_limit fields · **Blocks:** T5 — Download on miss or met-limit without stale work, T6 — Extend smoke coverage for the size-limit contract · **Wave:** 3, after T2.
- **Lane:** shares `backend/main.py` and `tests/test_images_api.py` with T2 — serialized.

## Why (user story)

> **As an** Image owner
> **I want** a Result that meets the Size limit, or processing with an empty Size limit, to download automatically and the form to reset
> **So that** success stays the same as today's flow and no result characteristics remain on the page.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

> **As an** Image owner
> **I want** the smallest Result still downloaded when the Size limit cannot be met, the form kept, and the actual size plus that the bound was exceeded shown
> **So that** I can change settings and process again; a new file starts a new cycle.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task puts miss versus met-limit on the existing binary 200 so the UI can reset or keep the form.

## Inlined context

> Keep the complete binary Result and attachment filename. When a bound was supplied, also send miss facts on the response so the Browser UI can start one download and then either reset (met) or keep the form (miss). Do not use a client-error status for an unattainable bound. Do not wrap the file in JSON or multipart metadata.
>
> — `sad.md §4, Signal a miss on the binary response, abridged` · full text: [sad.md](../sad.md)

> When a bound was supplied, response headers `X-Result-Bytes` (whole encoded bytes) and `X-Size-Limit-Met` (`true` or `false`); omit both when the bound is omitted.
>
> — `sad.md §8, Miss facts, verbatim` · full text: [sad.md](../sad.md)

> **Chosen:** Option 2. The successful response remains the complete binary Result. Miss versus met-limit is carried in headers so the Browser UI can start one download and then reset or keep the form.
>
> — `adr/0002-signal-size-limit-miss-with-headers.md, Decision outcome, abridged` · full text: [adr/0002-signal-size-limit-miss-with-headers.md](../adr/0002-signal-size-limit-miss-with-headers.md)

> Bound omitted: complete binary Result, then clean form. Bound supplied and encoded bytes meet it: complete binary with met-limit facts, then clean form. Bound supplied and even one pixel exceeds it: complete binary with miss facts; keep form, show actual size and exceeded notice. Recoverable failure: restore controls with current file and parameters.
>
> — `sad.md §6, process with optional Size limit, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** A miss is not a client error: AC-07 requires a file. Keep the existing binary attachment handoff.
>
> — `adr/0002-signal-size-limit-miss-with-headers.md, Decision drivers, abridged` · full text: [adr/0002-signal-size-limit-miss-with-headers.md](../adr/0002-signal-size-limit-miss-with-headers.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [openapi.yaml](../contracts/openapi.yaml) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `POST /api/v1/images/process` → `200` binary `Result` with required `Content-Disposition` `attachment; filename="result.jpg|png|webp"`.
- Omit `X-Result-Bytes` and `X-Size-Limit-Met` when `size_limit` was omitted or empty.
- When `size_limit` was supplied, both headers are required: `X-Size-Limit-Met` is `true` when encoded bytes are at most the bound, otherwise `false`; `X-Result-Bytes` is the whole encoded size (integer, minimum 1).
- A miss is this 200, not 4xx. Do not wrap the file in JSON or multipart metadata.

— `contracts/openapi.yaml, operationId processImage 200, abridged` · full text: [openapi.yaml](../contracts/openapi.yaml)

## Acceptance criteria

### AC-06 — happy

> **Given** a Size limit that the Result can meet, or an empty Size limit,
> **When** processing completes successfully,
> **Then** the page initiates exactly one automatic download of a Result whose size in bytes is at most the Size limit when one was supplied, then resets the form to the initial empty state: the selected file, Preview, Result, errors, miss facts, both dimension limits and Size limit are cleared and format returns to JPEG.
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

This task owns the server facts for omitted/met 200. T5 owns the download and reset.

### AC-07 — happy

> **Given** a Size limit that cannot be met even at one pixel and the smallest file the chosen format can produce,
> **When** processing completes,
> **Then** a Result is still produced in the chosen format and one automatic download starts; the form is not reset; the page shows the actual Result size and that the Size limit was exceeded; the Original and parameters remain so the owner can change them and process again.
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

This task owns the 200 miss headers. T5 owns keep-form and the notice.

## Checklist

- [ ] In `backend/main.py`, after a successful `process_image`, keep the binary body and attachment filename.
- [ ] When `size_limit_bytes` is set, add `X-Result-Bytes` (whole encoded length) and `X-Size-Limit-Met` (`true` if `len(output) <= size_limit_bytes`, else `false`).
- [ ] Omit both headers when the bound was omitted or empty. Never use 4xx for an unattainable bound.
- [ ] Extend `tests/test_images_api.py` for omitted headers, met-limit `true` with bytes at most the bound, and miss `false` still 200 with the encoded size.

## Edge cases

| Case | Behaviour |
|---|---|
| Bound omitted | 200, no miss headers |
| Encoded bytes equal the bound | `X-Size-Limit-Met: true` |
| Encoded bytes exceed the bound | 200, `X-Size-Limit-Met: false`, file still attached |
| Recoverable processing failure | Existing 4xx/500; no miss headers |

## Definition of Done

- [ ] tests/test_images_api.py 200 responses omit X-Result-Bytes and X-Size-Limit-Met when the bound is omitted; a met bound sends both with X-Size-Limit-Met true and bytes at most the bound; an unattainable bound still returns 200 with X-Size-Limit-Met false and the encoded size.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
