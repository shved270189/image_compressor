---
id: "T10"
title: "Submit and download the current result"
layer: "ui"
deps: ["T8", "T9"]
blocks: ["T11"]
acs: ["AC-03", "AC-11", "AC-13", "AC-14", "AC-15", "AC-16"]
files_hint: ["frontend/src/App.tsx", "frontend/src/index.css", "docs/features/image-resize-convert/_audit/implementation-download.md"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "Recorded SCR-01 loading/validation/error/success checks pass: one complete download per current operation, safe URL release, clean reset/focus, same-file reselection and retained-input retry without stale or duplicate downloads."
file: "docs/features/image-resize-convert/tasks/submit-and-download-the-current-result.md"
---

# T10 — Submit and download the current result

## Place in the sequence

- **Blocked by:** T8 — Serve request-scoped image results, T9 — Build selection and local preview. **Blocks:** T11 — Verify browser acceptance. **Wave:** 8 (after its prerequisites).
- **Lane:** Shares files with T9; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 73 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As an** Image owner
> **I want** the Result to download automatically after successful processing and the form to reset
> **So that** I can use the completed file without overwriting the Original and immediately select the next image.

— `spec.md §4, US-04, verbatim` · [Full text](../spec.md)

Submit and download the current result delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Completion.** Wait for the whole successful response before attempting a download. Recheck that the operation is current and not consumed. Hand the Blob URL to a native download action once, with the requested format and matching filename extension, then return to the initial form. Reset clears the native file input too, allowing the same file to be selected again. No result panel, repeat-download control or result object remains in application state.

— `sad.md §6, Completion, verbatim` · [Full text](../sad.md)

> | Form concurrency | At most one submitted processing operation from the current form; file selection and all transformation parameter controls disabled while processing | Duplicate-submit and disabled-control checks, including clean-form reset after successful download handoff and retained input after recoverable failure |

— `spec.md §6, Form concurrency, verbatim` · [Full text](../spec.md)

> | Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |

— `spec.md §6, Transient resources, verbatim` · [Full text](../spec.md)

> Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in backend/main.py and image functions in backend/images.py.

— `adr/0001-extend-web-frontend-and-backend-service.md §Decision outcome, ADR-0001, abridged` · [Full text](../adr/0001-extend-web-frontend-and-backend-service.md)

> Use one processing request with a complete binary response and no result ID, lookup or second retrieval request. Lock file selection, parameters and repeated submission while it is pending. On complete success, verify currentness and consume the operation once, initiate a native download with the matching filename extension, and reset the form. A separate handoff owner releases the result Blob URL when safe; resetting form state must not revoke it prematurely. Retain current input after recoverable errors. Invalidate page work on teardown and release server resources on success, failure and interruption, allowing already-running native decoding to finish before its resources are released.

— `adr/0004-return-results-within-the-current-operation.md §Decision outcome, ADR-0004, verbatim` · [Full text](../adr/0004-return-results-within-the-current-operation.md)

> Full browser failure/retry/closure coverage belongs to implemented-flow acceptance.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

> Browser handoff is verified with immediate Blob URL revocation after native link click and form reset: complete PNGs on desktop Chrome, Safari and Firefox; owner-reported downloads in all three modes on iOS Safari, Chrome and Firefox. Chrome additionally passes 55 assertions including active-URL cleanup and a completed download after actual page closure. Android is deferred by the owner. This establishes the release boundary for tested environments, not a universal browser/version guarantee.

— `sad.md §11, verified mechanism, verbatim` · [Full text](../sad.md)

> | validation | Local selection or dimension rejection, or HTTP 413/415/422. Explain the reason using the mapping below. Local empty/oversized files have no Preview and cannot submit. Retain current input after server rejection and restore controls for correction or retry. AC-01, AC-11–AC-12, AC-15; SAD §6 US-02/US-05; contract 413/415/422. | Shell, File input, Dimension inputs, Format select, Process button, Preview (current eligible selection only), Notices, Validation text | [WF-03](#wf-03--validation) |

— `screens.md §Screens, SCR-01 validation, verbatim` · [Full text](../screens.md)

> | loading | Processing submitted; upload, server work and receiving the complete response are one busy state. Disable file selection, both dimensions, format and repeat submission. Display Processing… without fabricated percentages or Cancel. AC-15; SAD §6 US-02–US-05. | Shell, File input, Dimension inputs, Format select, Process button, Preview (if available), Notices, Status text | [WF-04](#wf-04--processing) |

— `screens.md §Screens, SCR-01 loading, verbatim` · [Full text](../screens.md)

> | error | HTTP 400/500, request failure or incomplete/failed response transfer. No download; show a safe readable explanation, retain current file, parameters and available Preview, restore controls. A user retry is a new submission. AC-15–AC-16; SAD §6 US-04/US-05; contract 400/500 and interruption description. | Shell, File input, Dimension inputs, Format select, Process button, Preview (if available), Notices, Error text | [WF-05](#wf-05--recoverable-error) |

— `screens.md §Screens, SCR-01 error, verbatim` · [Full text](../screens.md)

> | success | Complete successful response belongs to the current unconsumed operation. Initiate one native download, then reset to empty after handoff. N/A: separate success layout, result panel and repeat-download action are explicitly excluded. AC-13–AC-16; SAD §6 US-04; contract 200. | Shell, File input, Dimension inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form), after handoff |

— `screens.md §Screens, SCR-01 success, verbatim` · [Full text](../screens.md)

Reuse: existing Shell in `frontend/src/App.tsx`, native labeled controls/Preview/Notices, and `canvas`, `ink`, `muted`, `accent`, font and reduced-motion rules in `frontend/src/index.css`. No design-system inventory exists; use the approved native fallback, not a new component library.

— `screens.md §Source, native fallback inventory, abridged` · [Full text](../screens.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

`POST /api/v1/images/process` (`processImage`), multipart `file`, optional `max_width` / `max_height`, and `output_format` (`jpeg`, `png`, `webp`). Empty dimensions impose no bound; dimensions with omitted format use JPEG, but no supplied parameter is 422. Explicit empty format is invalid. No product upper dimension bound.

200: complete binary `image/jpeg`, `image/png` or `image/webp`, with required `Content-Disposition: attachment; filename="result.jpg"` (or `result.png` / `result.webp`). No result ID, JSON wrapper or retrieval endpoint. Errors: 400 malformed multipart, 413 excess file bytes/pixels, 415 unsupported request/content, 422 missing/invalid parameters or empty/corrupt/animated input, 500 safe internal failure. `detail` is a readable string or a 422 validation array with `loc`, `msg`, `type`; wording/order is not a machine contract. Never expose image data, filenames or internal exception details. An interrupted response may have no error body.

— `contracts/openapi.yaml §paths, operationId processImage and schemas, abridged` · [Full text](../contracts/openapi.yaml)

## Acceptance criteria

### AC-03 (US-01, US-04) — cross-context

> **Given** an Original has been selected,
> **When** Image owner makes a new file selection,
> **Then** the previous Preview disappears, dimensions reset to empty and format resets to JPEG, including when the newly selected file is empty or above the byte limit; delayed work for an old selection or completed operation must never replace the current Preview, repopulate a reset form or trigger another download. An unavailable or failed Preview is omitted rather than displaying the old picture, a broken-image placeholder or a processing error.

— `spec.md §5, AC-03, verbatim` · [Full text](../spec.md)

### AC-11 (US-05) — error

> **Given** no file, no supplied transformation parameter, an invalid dimension or an unsupported output choice,
> **When** processing is attempted,
> **Then** the system rejects the attempt and explains the reason even when form restrictions are bypassed; dimensions must be positive whole pixel counts, empty dimensions impose no bound, and a supplied output format including the form's default JPEG counts as a parameter. Valid supplied dimensions with no output format produce JPEG; omitting both dimensions and output format remains an error.

— `spec.md §5, AC-11, verbatim` · [Full text](../spec.md)

### AC-13 (US-04) — cross-context

> **Given** successful processing for the current selection,
> **When** the current operation's complete Result is ready,
> **Then** the page initiates exactly one automatic browser download without a separate download action; the file has the requested output format and matching filename extension, and the Original remains untouched. After handing the file to the browser for download, the page returns to the initial form without reloading: the selected file, Preview, Result and errors are removed, both dimension limits become empty and format resets to JPEG. File selection is available, transformation controls are disabled or hidden and processing is disabled until another eligible file is selected. No result characteristics or repeat-download action remain on the page. Reset must not interrupt the initiated download and does not wait for confirmation that the browser saved the file to disk. The next selected file starts an independent conversion, including when it is the same file as before.

— `spec.md §5, AC-13, verbatim` · [Full text](../spec.md)

### AC-14 (US-04) — authorization

> **Given** a Result belongs to a different operation or is no longer available to the current page,
> **When** Image owner attempts to retrieve it,
> **Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.

— `spec.md §5, AC-14, verbatim` · [Full text](../spec.md)

### AC-15 (US-05) — error

> **Given** processing is in progress,
> **When** Image owner waits, processing fails or the page closes,
> **Then** the form disables file selection, all transformation parameter controls and repeat submission while processing, shows a truthful busy state without fabricated percentages, restores the controls and retry with the selected file and parameters after a recoverable error, and offers no result restoration after closing or reloading the page. Successful completion initiates the automatic download and resets the form as specified in AC-13; only the current operation may initiate that download, and no stale or duplicate completion may initiate it again.

— `spec.md §5, AC-15, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] In frontend/src/App.tsx, submit relative /api/v1/images/process with FormData and output_format; preserve dimension text without precision-losing Number coercion. Lock all controls and guard repeated submission through complete response receipt.
- [ ] Render SCR-01 validation/error/loading states with native field associations, aria-invalid, aria-busy and a polite busy announcement. Read safe detail/msg/loc only; never branch on message wording or display raw input/ctx/JSON.
- [ ] On current unconsumed complete success, initiate one matching-filename native download, reset state and native input, return focus to file selection, and release Preview. Use the verified immediate post-click result-URL release independently of reset, with cleanup on failures; no timeout or disk-save event.
- [ ] Record _audit/implementation-download.md checks for every HTTP status, failed/incomplete transfer, retained-input retry, duplicate/stale completion, same-file reselection, page closure and result/Preview URL cleanup using existing browser tooling.

## Edge cases

| Case | Required behavior |
|---|---|
| HTTP 200 body fails mid-transfer | Do not download partial bytes; retain input and permit retry. |
| Stale or repeated completion | Never download or repopulate the form. |
| Reset after native click | Clear input immediately; release download URL at verified handoff without interrupting download. |

— `spec.md §5, AC-03, AC-11, AC-13, AC-14, AC-15, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] Recorded SCR-01 loading/validation/error/success checks pass: one complete download per current operation, safe URL release, clean reset/focus, same-file reselection and retained-input retry without stale or duplicate downloads.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
