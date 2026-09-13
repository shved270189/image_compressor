---
id: T7
title: "Verify browser acceptance of Size limit and miss"
layer: "tests"
deps: ["T5"]
blocks: ["T8"]
acs: ["AC-02", "AC-06", "AC-07", "AC-11"]
files_hint: ["docs/features/image-size-limit/_audit/browser-acceptance.md"]
owner: "Tech Lead"
estimate: "M"
context_budget: "M"
status: "todo"
dod: "docs/features/image-size-limit/_audit/browser-acceptance.md records passing keyboard/focus, 360 and 1280 layouts without page overflow, reduced motion, met-limit reset, miss keep-form, and owner contrast acceptance of the exceeded notice."
file: "docs/features/image-size-limit/tasks/verify-browser-acceptance.md"
---

# T7 — Verify browser acceptance of Size limit and miss

## Place in the sequence

- **Blocked by:** T5 — Download on miss or met-limit without stale work · **Blocks:** T8 — Document the optional size-limit workflow · **Wave:** 5, after T5.
- **Lane:** own lane (evidence file only). No new browser-test framework.

## Why (user story)

> **As a** Власник картинки
> **I want** the smallest Результат still downloaded when the Ліміт ваги cannot be met, the form kept, and the actual size plus that the bound was exceeded shown
> **So that** I can change settings and process again; a new file starts a new cycle.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task records the specified browser, keyboard and contrast checks on the implemented form.

## Inlined context

> Every interactive control including the Ліміт ваги number and unit is keyboard-usable with visible focus; labels, errors and the exceeded notice pass the project owner's manual readable-contrast review; reduced motion as on the existing form. Complete flow at viewport widths 360 and 1280 CSS pixels with no horizontal page overflow, including the unit choice beside the number. After an over-limit Результат, actual size and the exceeded notice remain until the next process, a new file selection or page close.
>
> — `spec.md §6, Accessibility, Responsive UI, Miss visibility, abridged` · full text: [spec.md](../spec.md)

> Review the implementation against every state, including empty bound, bound-plus-JPEG-only submit, invalid bound kept original, loading lock of Ліміт ваги, miss keep-form with actual bytes, met-limit reset that also clears bound and miss facts, new-file reset to Mb, stale completion suppression and clean reload. Check the keyboard journey for number and both unit radios, visible focus, owner-approved contrast for the exceeded notice, reduced motion and no horizontal overflow at 360 and 1280 CSS pixels.
>
> — `screens.md, Verification and readiness, abridged` · full text: [screens.md](../screens.md)

> **Hard rule:** A cancel control during processing remains a non-goal. Keep a truthful busy state without fabricated percentages.
>
> — `spec.md §3, Non-goals` and `sad.md §11, busy/no-cancel, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [screens.md](../screens.md) · [sad.md](../sad.md)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. Browser talks to the already-shipped `POST /api/v1/images/process` from T3.

## Acceptance criteria

### AC-02 — happy

> **Given** a selected Оригінал,
> **When** Власник картинки sets Ліміт ваги,
> **Then** the control is a numeric field that accepts a positive decimal, with a unit choice to the left of the number whose options are Mb and Kb and with Mb selected initially; empty remains allowed and means no bound.
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-06 — happy

> **Given** a Ліміт ваги that the Результат can meet, or an empty Ліміт ваги,
> **When** processing completes successfully,
> **Then** the page initiates exactly one automatic download of a Результат whose size in bytes is at most the Ліміт ваги when one was supplied, then resets the form to the initial empty state: the selected file, Preview, Результат, errors, miss facts, both dimension limits and Ліміт ваги are cleared and format returns to JPEG.
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — happy

> **Given** a Ліміт ваги that cannot be met even at one pixel and the smallest file the chosen format can produce,
> **When** processing completes,
> **Then** a Результат is still produced in the chosen format and one automatic download starts; the form is not reset; the page shows the actual Результат size and that the Ліміт ваги was exceeded; the Оригінал and parameters remain so the owner can change them and process again.
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

### AC-11 — cross-context

> **Given** processing is in progress,
> **When** Власник картинки waits, starts another process, processing fails or the page closes,
> **Then** file selection and all transformation controls including Ліміт ваги are disabled while processing, a truthful busy state is shown without fabricated percentages, a new process replaces previous miss facts, only the current operation may initiate a download, recoverable failure restores retry with the selected file and parameters, and closing or reloading the page restores neither input nor result. After a miss, those controls remain usable so the owner can change settings and process again.
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Exercise SCR-01 in the browser at 360 and 1280 CSS pixels: unit radios stay left of the number, no horizontal page overflow.
- [ ] Keyboard-reach the number and both unit radios with visible focus. Confirm reduced motion still leaves the flow usable.
- [ ] Record met-limit automatic download + clean form, miss keep-form with actual bytes, loading lock of Size limit, and owner contrast acceptance of the exceeded notice.
- [ ] Write `docs/features/image-size-limit/_audit/browser-acceptance.md` with those results. Do not add a new browser-test runner.

## Edge cases

| Case | Behaviour |
|---|---|
| 360 CSS pixels, wrapping radios | Group wraps together; no page overflow |
| Reduced motion | No decorative animation; controls still work |
| Reload during or after miss | Restore neither input nor result |

## Definition of Done

- [ ] docs/features/image-size-limit/_audit/browser-acceptance.md records passing keyboard/focus, 360 and 1280 layouts without page overflow, reduced motion, met-limit reset, miss keep-form, and owner contrast acceptance of the exceeded notice.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
