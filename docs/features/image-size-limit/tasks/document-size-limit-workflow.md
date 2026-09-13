---
id: T8
title: "Document the optional size-limit workflow"
layer: "docs"
deps: ["T6", "T7"]
blocks: []
acs: ["AC-01", "AC-09"]
files_hint: ["README.md", "docs/architecture-map.md"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
dod: "README.md and docs/architecture-map.md describe optional Ліміт ваги, miss versus met-limit, and the current OpenAPI path; documented build, pytest and both lint commands pass."
file: "docs/features/image-size-limit/tasks/document-size-limit-workflow.md"
---

# T8 — Document the optional size-limit workflow

## Place in the sequence

- **Blocked by:** T6 — Extend smoke coverage for the size-limit contract, T7 — Verify browser acceptance of Size limit and miss · **Blocks:** none · **Wave:** 6, last.
- **Lane:** own lane (`README.md`, `docs/architecture-map.md`).

## Why (user story)

> **As a** Власник картинки
> **I want** to set an independently optional Ліміт ваги as a positive decimal with a unit choice of Mb or Kb to the left of the number, Mb initially selected, empty meaning no bound
> **So that** the Результат can target a file-size budget, and a supplied Ліміт ваги counts as a transformation parameter (processing may run with only that bound and the initial JPEG).
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task updates usage docs so the shipped bound and miss path match the code.

## Inlined context

> Let the image owner apply an optional result byte budget without losing the current one-form flow. Meet that budget when it is attainable, preferring the largest proportional result that still fits. Make an unattainable budget visible and retryable instead of a silent oversize file or a hard failure with no file.
>
> — `spec.md §2, Goals, abridged` · full text: [spec.md](../spec.md)

> Closest precedent: `frontend/src/App.tsx` owns the single form with independently optional dimension limits and JPEG/PNG/WebP selection. A new file-size control would extend this fieldset, not a second screen.
>
> — `docs/architecture-map.md, Frontend / UI foundation, abridged` · full text: [architecture-map.md](../../../architecture-map.md)

> The contract is [OpenAPI](docs/features/image-resize-convert/contracts/openapi.yaml). Implementation checks are recorded in the [task tracker](docs/features/image-resize-convert/tasks/tracker.md).
>
> — `README.md, Image workflow, abridged` · full text: [README.md](../../../../README.md)
>
> No datastore, queue, result ID or retrieval.
>
> — `sad.md §2, Technical constraints, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Showing result characteristics after a met-limit or omitted-limit success stays out of scope. Empty Ліміт ваги preserves existing geometry. Ліміт ваги is not the upload cap.
>
> — `spec.md §3, Non-goals` and `spec.md §1, Traceability, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [README.md](../../../../README.md)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. Docs cite `POST /api/v1/images/process` and the feature OpenAPI.

## Acceptance criteria

### AC-01 — happy

> **Given** a selected Оригінал within the input limits,
> **When** Власник картинки leaves Ліміт ваги empty and processes,
> **Then** no result byte bound is applied and dimension and format behaviour matches the existing form.
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-09 — authorization

> **Given** a Результат belongs to a different operation or is no longer available to the current page,
> **When** Власник картинки attempts to retrieve it,
> **Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Update `README.md` Image workflow: optional Size limit (Mb/Kb), empty means no bound, extra-shrink when supplied, miss still downloads and keeps the form, met/omitted bound still auto-downloads and resets. Keep upload/pixel caps distinct from Ліміт ваги.
- [ ] Point the contract link at `docs/features/image-size-limit/contracts/openapi.yaml`. Point implementation checks at this feature's tracker.
- [ ] Update `docs/architecture-map.md` so the frontend precedent names the shipped Size limit control and miss headers, not a hypothetical future field.
- [ ] Confirm documented `npm --prefix frontend run build`, `uv run pytest`, `uv run ruff check .` and `npm --prefix frontend run lint` still match README.

## Edge cases

| Case | Behaviour |
|---|---|
| Empty bound | Docs still describe today's geometry, no extra shrink |
| Miss | Docs say the file downloads and the form stays, with actual size shown |
| Lookup / history | Docs keep "no retrieval" |

## Definition of Done

- [ ] README.md and docs/architecture-map.md describe optional Ліміт ваги, miss versus met-limit, and the current OpenAPI path; documented build, pytest and both lint commands pass.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
