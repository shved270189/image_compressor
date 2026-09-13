---
id: T5
title: "Download on miss or met-limit without stale work"
layer: "ui"
deps: ["T3", "T4"]
blocks: ["T7"]
acs: ["AC-06", "AC-07", "AC-09", "AC-10", "AC-11"]
files_hint: ["frontend/src/App.tsx"]
owner: "Tech Lead"
estimate: "M"
context_budget: "M"
status: "todo"
dod: "SCR-01 loading/success/miss/error checks pass: one download then reset when omitted or X-Size-Limit-Met true; miss keeps the form and shows actual bytes; controls including Size limit lock while busy; new file and stale completions never restore old miss facts or extra downloads."
file: "docs/features/image-size-limit/tasks/handle-miss-and-met-limit.md"
---

# T5 — Download on miss or met-limit without stale work

## Place in the sequence

- **Blocked by:** T3 — Signal miss versus met-limit with response headers, T4 — Add Size limit number and unit radios · **Blocks:** T7 — Verify browser acceptance of Size limit and miss · **Wave:** 4, after T3 and T4. Parallel with T6.
- **Lane:** shares `frontend/src/App.tsx` with T4 — serialized.

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

This task starts one download, then resets or keeps the form from the miss headers.

## Inlined context

> **SCR-01 states this task builds:** loading (disable file selection and all transformation controls including Size limit; `Processing…` without percentages or Cancel; a new process replaces previous miss facts); success (complete 200 of the current operation and omitted bound or `X-Size-Limit-Met: true`: one download, then reset to empty); miss (complete 200 and `X-Size-Limit-Met: false`: one download, do not reset, show `The result is {N} bytes. The size limit was exceeded.` from `X-Result-Bytes`, controls usable); error (400/500/transfer failure: no download, retain file and parameters, restore controls).
>
> — `screens.md, SCR-01 Image processing, abridged` · full text: [screens.md](../screens.md)

> One AbortController; stale completions never download or restore miss facts. Miss notice is native status text, not Error text. Announce miss with a polite live region, not `role="alert"`. Associate `loc` of `size_limit` / `size_unit` with Size limit inputs.
>
> — `sad.md §8, Current operation, abridged` and `screens.md, Controls and validation, abridged` · full text: [sad.md](../sad.md)

> If headers are missing, the Browser UI may compare `blob.size` as a fallback.
>
> — `adr/0002-signal-size-limit-miss-with-headers.md, Neutral consequences, abridged` · full text: [adr/0002-signal-size-limit-miss-with-headers.md](../adr/0002-signal-size-limit-miss-with-headers.md)

> **Hard rule:** At most one submitted processing operation; file selection and all transformation controls including Size limit disabled while processing. A tight bound can hold the only screen in a busy state with no cancel — keep a truthful busy state without fabricated percentages.
>
> — `spec.md §6, Form concurrency` and `sad.md §11, RISK busy/no-cancel, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [screens.md](../screens.md) · [openapi.yaml](../contracts/openapi.yaml) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `POST /api/v1/images/process` · this task sends `size_limit` and `size_unit` (`mb` or `kb`) when the number is filled; omits `size_limit` when empty.
- Reads 200 headers `X-Result-Bytes` and `X-Size-Limit-Met`. Met (`true`) or omitted headers after an omitted bound → reset. Miss (`false`) → keep form.
- Errors: associate 422 `loc` `size_limit` / `size_unit`; 400/500 stay recoverable with retained input.

— `contracts/openapi.yaml, operationId processImage, abridged` · full text: [openapi.yaml](../contracts/openapi.yaml)

## Acceptance criteria

### AC-06 — happy

> **Given** a Size limit that the Result can meet, or an empty Size limit,
> **When** processing completes successfully,
> **Then** the page initiates exactly one automatic download of a Result whose size in bytes is at most the Size limit when one was supplied, then resets the form to the initial empty state: the selected file, Preview, Result, errors, miss facts, both dimension limits and Size limit are cleared and format returns to JPEG.
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — happy

> **Given** a Size limit that cannot be met even at one pixel and the smallest file the chosen format can produce,
> **When** processing completes,
> **Then** a Result is still produced in the chosen format and one automatic download starts; the form is not reset; the page shows the actual Result size and that the Size limit was exceeded; the Original and parameters remain so the owner can change them and process again.
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

### AC-09 — authorization

> **Given** a Result belongs to a different operation or is no longer available to the current page,
> **When** Image owner attempts to retrieve it,
> **Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

### AC-10 — cross-context

> **Given** an Original has been selected, including after a miss,
> **When** Image owner makes a new file selection,
> **Then** the previous Preview, miss facts, errors, dimensions, format and Size limit reset (empty bound, JPEG); delayed work for an old selection or completed operation must never replace the current Preview, show an old miss or trigger another download.
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

### AC-11 — cross-context

> **Given** processing is in progress,
> **When** Image owner waits, starts another process, processing fails or the page closes,
> **Then** file selection and all transformation controls including Size limit are disabled while processing, a truthful busy state is shown without fabricated percentages, a new process replaces previous miss facts, only the current operation may initiate a download, recoverable failure restores retry with the selected file and parameters, and closing or reloading the page restores neither input nor result. After a miss, those controls remain usable so the owner can change settings and process again.
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] In `frontend/src/App.tsx`, append `size_limit` and `size_unit` when the number is filled. Keep one AbortController. Disable file selection and every transformation control including Size limit while busy.
- [ ] On complete 200 of the current operation: one download using the contract filename. Omitted bound or `X-Size-Limit-Met: true` → reset including bound, unit Mb, JPEG and miss facts, focus file selection. `false` → keep form, show miss notice with whole `X-Result-Bytes`. If headers are missing after a supplied bound, compare `blob.size`.
- [ ] Ignore stale completions: no download, no form change, no old miss. New process clears previous miss facts. Recoverable failure retains file, bound and unit.
- [ ] Associate `size_limit` / `size_unit` `loc` with Size limit inputs. Miss uses a polite live region, not `role="alert"`.

## Edge cases

| Case | Behaviour |
|---|---|
| Stale completion | No download, no miss facts, no reset |
| New file after miss | Clear miss facts, bound, unit Mb, JPEG |
| Headers missing after a supplied bound | Fallback `blob.size` comparison |
| Page close or reload | Restore neither input nor result |
| Incomplete transfer | No download of partial output; retain input |

## Definition of Done

- [ ] SCR-01 loading/success/miss/error checks pass: one download then reset when omitted or X-Size-Limit-Met true; miss keeps the form and shows actual bytes; controls including Size limit lock while busy; new file and stale completions never restore old miss facts or extra downloads.
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
