---
id: T6
title: "Extend smoke coverage for the size-limit contract"
layer: "tests"
deps: ["T3", "T4"]
blocks: ["T8"]
acs: ["AC-01", "AC-03", "AC-09"]
files_hint: ["tests/test_smoke.py"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
dod: "tests/test_smoke.py still covers health, assets, PNG to WebP without miss headers, and API 404s including no result lookup; it also posts size_limit-only JPEG and pins Size limit form copy."
file: "docs/features/image-size-limit/tasks/extend-smoke-for-size-limit.md"
---

# T6 — Extend smoke coverage for the size-limit contract

## Place in the sequence

- **Blocked by:** T3 — Signal miss versus met-limit with response headers, T4 — Add Size limit number and unit radios · **Blocks:** T8 — Document the optional size-limit workflow · **Wave:** 4, parallel with T5.
- **Lane:** own lane (`tests/test_smoke.py`).

## Why (user story)

> **As an** Image owner
> **I want** to set an independently optional Size limit as a positive decimal with a unit choice of Mb or Kb to the left of the number, Mb initially selected, empty meaning no bound
> **So that** the Result can target a file-size budget, and a supplied Size limit counts as a transformation parameter (processing may run with only that bound and the initial JPEG).
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task extends the existing smoke test for structural size-limit regressions.

## Inlined context

> Extend the existing smoke test for structural regressions; add feature tests only for specified behavior. Build the frontend before `uv run pytest`; the smoke test requires real emitted assets. Use `SMOKE_BASE_URL` to run the same smoke test against a container.
>
> — `Agents.md, project conventions, abridged` · full text: [Agents.md](../../../../Agents.md)

> `tests/` — Existing smoke coverage plus specified bound, miss and geometry behavior
>
> — `sad.md §5, building block view, abridged` · full text: [sad.md](../sad.md)

> There is no history, lookup or retrieve screen (AC-09). Retain no server original or result for later retrieval.
>
> — `screens.md, SCR-01 Entry` and `sad.md §2, Technical constraints, abridged` · full text: [screens.md](../screens.md)

> When `size_limit` was omitted or empty, omit `X-Result-Bytes` and `X-Size-Limit-Met`. A positive `size_limit` counts as a transformation parameter, including with omitted `output_format` (JPEG fallback).
>
> — `contracts/openapi.yaml, processImage, abridged` · full text: [openapi.yaml](../contracts/openapi.yaml)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [openapi.yaml](../contracts/openapi.yaml)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- Existing smoke `POST /api/v1/images/process` with `max_width` + `output_format=webp` stays 200 without miss headers.
- Add size_limit-only JPEG: `size_limit` + `size_unit=mb`, omitted format, 200 `image/jpeg`.
- Keep 404 for `/api/v1/images/result.webp` and other unknown `/api` paths.

— `contracts/openapi.yaml, operationId processImage, abridged` · full text: [openapi.yaml](../contracts/openapi.yaml)

## Acceptance criteria

### AC-01 — happy

> **Given** a selected Original within the input limits,
> **When** Image owner leaves Size limit empty and processes,
> **Then** no result byte bound is applied and dimension and format behaviour matches the existing form.
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-03 — happy

> **Given** a selected Original and no Maximum dimensions,
> **When** Image owner supplies only a Size limit and leaves output format at the initial JPEG,
> **Then** processing is allowed because a transformation parameter is supplied.
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-09 — authorization

> **Given** a Result belongs to a different operation or is no longer available to the current page,
> **When** Image owner attempts to retrieve it,
> **Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Keep the existing PNG→WebP smoke path. Assert miss headers are absent when `size_limit` is omitted.
- [ ] Post a size_limit-only JPEG (`size_limit` + `size_unit`, no maxima, no `output_format`) and assert 200 `image/jpeg` with an attachment filename.
- [ ] Pin Size limit form copy from `frontend/src/App.tsx` the same way HEIC notice copy is pinned.
- [ ] Keep 404 checks for unknown `/api` paths including `/api/v1/images/result.webp`.

## Edge cases

| Case | Behaviour |
|---|---|
| Omitted bound | No miss headers; existing geometry still holds |
| Unknown result path | 404 JSON and HTML Accept, no image body |
| Missing frontend build | Smoke still requires a real `frontend/dist` |

## Definition of Done

- [ ] tests/test_smoke.py still covers health, assets, PNG to WebP without miss headers, and API 404s including no result lookup; it also posts size_limit-only JPEG and pins Size limit form copy.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
