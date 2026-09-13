---
id: T4
title: "Add Size limit number and unit radios"
layer: "ui"
deps: []
blocks: ["T5", "T6"]
acs: ["AC-02", "AC-08"]
files_hint: ["frontend/src/App.tsx"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
dod: "SCR-01 default/ready/validation checks pass: native Size limit number with Mb/Kb radios left of the number, Mb initially selected, empty allowed; zero/negative rejected locally with the specified copy while the original remains; new file selection resets bound and unit to Mb."
file: "docs/features/image-size-limit/tasks/add-size-limit-controls.md"
---

# T4 — Add Size limit number and unit radios

## Place in the sequence

- **Blocked by:** none · **Blocks:** T5 — Download on miss or met-limit without stale work, T6 — Extend smoke coverage for the size-limit contract · **Wave:** 1, with T1.
- **Lane:** shares `frontend/src/App.tsx` with T5 — serialized. Do not wire miss/met completion here.

## Why (user story)

> **As a** Власник картинки
> **I want** to set an independently optional Ліміт ваги as a positive decimal with a unit choice of Mb or Kb to the left of the number, Mb initially selected, empty meaning no bound
> **So that** the Результат can target a file-size budget, and a supplied Ліміт ваги counts as a transformation parameter (processing may run with only that bound and the initial JPEG).
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task extends the existing parameter fieldset with the Size limit control.

## Inlined context

> Ліміт ваги extends the current parameter fieldset on SCR-01; there is no second screen. The web surface is the existing React SPA with local state, no client router and native controls.
>
> — `sad.md §4, Extend the existing process surfaces, abridged` · full text: [sad.md](../sad.md)

> Reuse: `frontend/src/App.tsx` is the closest screen. Extend its parameter fieldset; do not add a second page. Tokens: `canvas`, `ink`, `muted`, `accent`, `surface`, `line`, `danger` and reduced-motion in `frontend/src/index.css`. Native fallback: labeled optional number input for a positive decimal, native radio group `Mb` / `Kb` to the left of the number, `Mb` selected initially, empty allowed. No new React primitive.
>
> — `screens.md, Source and Native fallback inventory, abridged` · full text: [screens.md](../screens.md)

> **SCR-01 states this task builds:** default (empty bound, unit Mb, JPEG, only file selection enabled); ready (eligible file enables dimensions, Ліміт ваги, format and processing; empty bound means no result byte bound; a supplied positive bound with only the initial JPEG is enough); validation (local zero/negative/non-positive bound: `Ліміт ваги must be a positive number with Mb or Kb or left empty`; keep the Оригінал).
>
> — `screens.md, SCR-01 Image processing, abridged` · full text: [screens.md](../screens.md)

> **Hard rule:** Every interactive control including the Ліміт ваги number and unit is keyboard-usable with visible focus. Complete flow at 360 and 1280 CSS pixels with no horizontal page overflow, including the unit choice beside the number.
>
> — `spec.md §6, Accessibility and Responsive UI, abridged` · full text: [spec.md](../spec.md)

> **Decision:** Declare `target_surfaces` as `[backend-service, web-frontend]`. Reuse the React SPA, local state, native controls and existing FastAPI application.
>
> — `adr/0001-extend-existing-process-surfaces.md, Decision outcome, abridged` · full text: [adr/0001-extend-existing-process-surfaces.md](../adr/0001-extend-existing-process-surfaces.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [screens.md](../screens.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. Submit wiring of `size_limit` / `size_unit` is T5.

## Acceptance criteria

### AC-02 — happy

> **Given** a selected Оригінал,
> **When** Власник картинки sets Ліміт ваги,
> **Then** the control is a numeric field that accepts a positive decimal, with a unit choice to the left of the number whose options are Mb and Kb and with Mb selected initially; empty remains allowed and means no bound.
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — error

> **Given** a filled Ліміт ваги that is zero, negative or not a positive number,
> **When** processing is attempted,
> **Then** the system rejects the attempt, explains that Ліміт ваги must be a positive number with Mb or Kb or left empty, produces no Результат, and keeps the Оригінал.
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

This task owns the local rejection before submit. T2 owns the HTTP 422.

## Checklist

- [ ] In `frontend/src/App.tsx`, add Size limit inputs to the existing fieldset: visible label `Size limit` with optional, native `Mb`/`Kb` radios left of a number input, `Mb` initially selected, empty allowed. Reuse `.field` and existing tokens. No new component.
- [ ] Reject zero, negative or otherwise non-positive values locally before submit, matching existing dimension checks. Associate the message with Size limit inputs. Keep the selected file.
- [ ] Reset bound to empty and unit to Mb on new file selection, including invalid replacements, and on the existing pagehide/abandon path.
- [ ] Keep unit radios to the left of the number at 360 CSS pixels; wrap as one group with no horizontal page overflow. Keyboard and visible focus for the number and both radios.

## Edge cases

| Case | Behaviour |
|---|---|
| Empty number | Allowed; means no bound; unit ignored on submit (T5) |
| `0`, `-1`, or non-positive text | Local validation; no fetch; original kept |
| New file selection | Bound empty, unit Mb, errors cleared |
| No eligible file | Size limit stays disabled with other parameters |

## Definition of Done

- [ ] SCR-01 default/ready/validation checks pass: native Size limit number with Mb/Kb radios left of the number, Mb initially selected, empty allowed; zero/negative rejected locally with the specified copy while the original remains; new file selection resets bound and unit to Mb.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
