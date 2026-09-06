---
id: "T9"
title: "Build selection and local preview"
layer: "ui"
deps: []
blocks: ["T10"]
acs: ["AC-01", "AC-02", "AC-03", "AC-07", "AC-08", "AC-09", "AC-10", "AC-11", "AC-12", "AC-16"]
files_hint: ["frontend/src/App.tsx", "frontend/src/index.css", "docs/features/image-resize-convert/_audit/implementation-selection.md"]
owner: "Tech Lead"
estimate: "6h"
context_budget: "M"
status: "todo"
dod: "Recorded SCR-01 selection checks pass for default/empty/ready/local-validation states, byte boundaries, reset/stale Preview, zero upload requests and native controls; frontend build and lint pass."
file: "docs/features/image-resize-convert/tasks/build-selection-and-local-preview.md"
---

# T9 — Build selection and local preview

## Place in the sequence

- **Blocked by:** None. **Blocks:** T10 — Submit and download the current result. **Wave:** 1 (after its prerequisites).
- **Lane:** Shares files with T10; serialize overlapping edits in task-number order after dependencies are ready.
- **Context:** 89 non-empty lines from Why through Acceptance criteria; open implementation/test files as needed. Recheck the size before editing; if the focused slice exceeds one day or about 500 changed lines, split it before implementation rather than omit requirements.

## Why (user story)

> **As a** Власник картинки
> **I want** to select an Оригінал and see its Preview above the form when my browser can display it
> **So that** I can verify the selected picture before processing.

— `spec.md §4, US-01, verbatim` · [Full text](../spec.md)

Build selection and local preview delivers the slice defined in the checklist; shared ACs below are completed jointly with the other tasks listed in the epic.

## Inlined context

> The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and an automatic result download followed by a clean form for the next conversion.

— `spec.md §1, committed approach, abridged` · [Full text](../spec.md)

> Use the existing division between the browser, the HTTP boundary and ordinary image functions. The backend calls image functions directly; it does not introduce repository, adapter, service-class or worker layers. Image functions do not depend on FastAPI request or response objects.

— `sad.md §5, module boundaries, verbatim` · [Full text](../sad.md)

> **Selection.** Every new selection clears the old Preview and resets format and bounds, including invalid selections. Reject empty files and files above the byte limit before preparing Preview. A current native-image load failure silently omits Preview. Delayed work cannot restore a prior selection. Preview availability never gates an otherwise eligible submission.

— `sad.md §6, Selection, verbatim` · [Full text](../sad.md)

> | Preview locality | Zero file-upload requests caused by selection, parameter editing or Preview preparation | Browser network checks; native image display using a local object URL, without an added decoder dependency or a server preview operation |

— `spec.md §6, Preview locality, verbatim` · [Full text](../spec.md)

> | Accessibility | Every interactive control is keyboard-usable with visible focus; every label, error and action passes the project owner's manual readable-contrast review; with reduced motion, zero decorative animations and zero loss of functionality | Full keyboard flow, visible-focus review, manual contrast acceptance by the project owner without numeric contrast thresholds, and reduced-motion browser check |

— `spec.md §6, Accessibility, verbatim` · [Full text](../spec.md)

> Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in backend/main.py and image functions in backend/images.py.

— `adr/0001-extend-web-frontend-and-backend-service.md §Decision outcome, ADR-0001, abridged` · [Full text](../adr/0001-extend-web-frontend-and-backend-service.md)

> Use one processing request with a complete binary response and no result ID, lookup or second retrieval request. Lock file selection, parameters and repeated submission while it is pending. On complete success, verify currentness and consume the operation once, initiate a native download with the matching filename extension, and reset the form. A separate handoff owner releases the result Blob URL when safe; resetting form state must not revoke it prematurely. Retain current input after recoverable errors. Invalidate page work on teardown and release server resources on success, failure and interruption, allowing already-running native decoding to finish before its resources are released.

— `adr/0004-return-results-within-the-current-operation.md §Decision outcome, ADR-0004, verbatim` · [Full text](../adr/0004-return-results-within-the-current-operation.md)

> Full browser failure/retry/closure coverage belongs to implemented-flow acceptance.

— `sad.md §11, Required implementation carry-forward, abridged` · [Full text](../sad.md)

> | default | Initial entry or reload. No file or Preview; empty bounds and JPEG selected. Only file selection is enabled. No restoration. AC-01, AC-15–AC-16; SAD §6 US-01/US-04. | Shell, File input, Dimension inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form) |

— `screens.md §Screens, SCR-01 default, verbatim` · [Full text](../screens.md)

> | empty | Same visible form as default, including after successful handoff. Parameters remain visible but disabled; processing disabled. AC-01, AC-13. | Shell, File input, Dimension inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form) |

— `screens.md §Screens, SCR-01 empty, verbatim` · [Full text](../screens.md)

> | ready | Non-empty file at most 20,000,000 bytes selected. Enable parameters and processing immediately; new selections reset bounds and JPEG. Preview may be visible, pending or unavailable; pending and failed Preview render no placeholder and never block submission. AC-01–AC-03, AC-07–AC-10; SAD §6 US-01/US-03. | Shell, File input, Dimension inputs, Format select, Process button, Preview (only when available), Notices | [WF-02](#wf-02--ready-form) |

— `screens.md §Screens, SCR-01 ready, verbatim` · [Full text](../screens.md)

> | validation | Local selection or dimension rejection, or HTTP 413/415/422. Explain the reason using the mapping below. Local empty/oversized files have no Preview and cannot submit. Retain current input after server rejection and restore controls for correction or retry. AC-01, AC-11–AC-12, AC-15; SAD §6 US-02/US-05; contract 413/415/422. | Shell, File input, Dimension inputs, Format select, Process button, Preview (current eligible selection only), Notices, Validation text | [WF-03](#wf-03--validation) |

— `screens.md §Screens, SCR-01 validation, verbatim` · [Full text](../screens.md)

Reuse: existing Shell in `frontend/src/App.tsx`, native labeled controls/Preview/Notices, and `canvas`, `ink`, `muted`, `accent`, font and reduced-motion rules in `frontend/src/index.css`. No design-system inventory exists; use the approved native fallback, not a new component library.

— `screens.md §Source, native fallback inventory, abridged` · [Full text](../screens.md)

**Fallback:** if a slice is insufficient, ambiguous or contradicted by code, open its named source and follow it; do not invent missing behavior. SAD §11 and the dated feasibility audit close the pre-tasks gates; older open-gate notes in screens/data-model do not reopen them. Implementation acceptance remains required.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-01 (US-01) — happy

> **Given** no Оригінал has been selected,
> **When** Власник картинки opens the form,
> **Then** the file-selection control remains available, transformation parameter controls are disabled or hidden and processing is disabled; selecting a non-empty file of at most 20,000,000 bytes reveals or enables the transformation controls with JPEG selected and empty dimension limits, and enables processing without waiting for content validation. Selecting an empty file or a file above that byte limit immediately shows an understandable error, omits Preview and keeps processing disabled.

— `spec.md §5, AC-01, verbatim` · [Full text](../spec.md)

### AC-02 (US-01) — happy

> **Given** a supported Оригінал within the input limits,
> **When** Власник картинки selects it,
> **Then** a supported Preview appears above the form, preserves the complete image and correct orientation and is prepared entirely on the owner's device without sending the file for preview generation; when the browser cannot display the file, no Preview or broken-image placeholder is shown, and this absence does not block processing, including for HEIC.

— `spec.md §5, AC-02, verbatim` · [Full text](../spec.md)

### AC-03 (US-01, US-04) — cross-context

> **Given** an Оригінал has been selected,
> **When** Власник картинки makes a new file selection,
> **Then** the previous Preview disappears, dimensions reset to empty and format resets to JPEG, including when the newly selected file is empty or above the byte limit; delayed work for an old selection or completed operation must never replace the current Preview, repopulate a reset form or trigger another download. An unavailable or failed Preview is omitted rather than displaying the old picture, a broken-image placeholder or a processing error.

— `spec.md §5, AC-03, verbatim` · [Full text](../spec.md)

### AC-07 (US-03) — happy

> **Given** a supported static JPEG, PNG, WebP or HEIC Оригінал,
> **When** Власник картинки chooses JPEG, PNG or WebP and processes it,
> **Then** a decodable Результат is produced in the chosen format; JPEG is the initial output choice for every input, including JPEG itself, and there is no guarantee of smaller file size or byte-identical output.

— `spec.md §5, AC-07, verbatim` · [Full text](../spec.md)

### AC-08 (US-03) — domain invariant

> **Given** a selected Оригінал, whether or not its transparency is known or Preview is available,
> **When** Власник картинки chooses JPEG,
> **Then** the form always shows a conditional warning before processing: if the image has transparency, it will become white; this also applies when JPEG is selected by default and requires no advance transparency detection. The JPEG Результат uses white behind partial and full transparency; PNG and WebP output retain transparency.

— `spec.md §5, AC-08, verbatim` · [Full text](../spec.md)

### AC-09 (US-01, US-03) — domain invariant

> **Given** an Оригінал with orientation information or service metadata,
> **When** Власник картинки processes it,
> **Then** the Результат and any available Preview have the correct visible orientation, and dimension limits apply to that orientation; the Результат omits GPS, camera and textual metadata while retaining information required for correct color interpretation.

— `spec.md §5, AC-09, verbatim` · [Full text](../spec.md)

### AC-10 (US-01, US-03) — happy

> **Given** a HEIC Оригінал with additional images or high-dynamic-range content,
> **When** Власник картинки processes it,
> **Then** only the designated primary static image is used; the form explains the general HEIC rules before submission: extra images are omitted and high-dynamic-range content becomes ordinary 8-bit output, with no promise of retaining the original high-dynamic-range appearance; this notice requires no advance server inspection.

— `spec.md §5, AC-10, verbatim` · [Full text](../spec.md)

### AC-11 (US-05) — error

> **Given** no file, no supplied transformation parameter, an invalid dimension or an unsupported output choice,
> **When** processing is attempted,
> **Then** the system rejects the attempt and explains the reason even when form restrictions are bypassed; dimensions must be positive whole pixel counts, empty dimensions impose no bound, and a supplied output format including the form's default JPEG counts as a parameter. Valid supplied dimensions with no output format produce JPEG; omitting both dimensions and output format remains an error.

— `spec.md §5, AC-11, verbatim` · [Full text](../spec.md)

### AC-12 (US-05) — error

> **Given** an empty, corrupted, unsupported or animated Оригінал, or an input above 20 million bytes or 40 million decoded pixels,
> **When** processing is attempted,
> **Then** the system rejects it with an understandable reason and produces no successful Результат; exact limits are allowed, support is determined from actual content, and additional HEIC images are subject to the primary-image rule rather than treated as animation. The form checks only whether the selected file is empty or exceeds the byte limit before preparing Preview; the server checks content, animation and decoded pixel count when processing is submitted, and enforces all input limits even when form restrictions are bypassed.

— `spec.md §5, AC-12, verbatim` · [Full text](../spec.md)

### AC-16 (US-01, US-04, US-05) — cross-context

> **Given** processing has completed, failed or been interrupted,
> **When** that operation's lifecycle ends,
> **Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its selected file, parameters and Preview through a recoverable error, until a new file selection, successful download handoff or page closure. Successful handoff clears the form and immediately releases obsolete Preview resources. Result resources exist only for handing the download to the browser and must be released as soon as they are no longer needed by that handoff, without interrupting the initiated download; no result remains available for another application download. Failure and interruption release operation resources without restoring a prior result. Closing or reloading the page restores neither input nor result.

— `spec.md §5, AC-16, verbatim` · [Full text](../spec.md)

## Checklist

- [ ] Compose SCR-01 in frontend/src/App.tsx using the existing Shell, labeled native file/number/select/button controls and notices; reuse canvas/ink/muted/accent and reduced-motion rules in frontend/src/index.css. No component library or new reusable components.
- [ ] Implement default/empty/ready/local-validation states: visible disabled parameters before eligible selection, independent dimension strings, JPEG reset on every replacement, immediate byte eligibility and conditional JPEG/general HEIC notices from screens.md.
- [ ] Prepare optional whole oriented native-img Preview from a local object URL; omit pending/failed Preview, suppress stale callbacks and revoke obsolete resources on replacement/reset/teardown. Selection and editing never fetch.
- [ ] Record browser selection checks in _audit/implementation-selection.md using existing browser tooling, including exact/over byte limit, invalid replacement, unavailable Preview, huge positive dimension text, labels/focus and zero uploads. Submission integration belongs to T10; do not add a placeholder endpoint.

## Edge cases

| Case | Required behavior |
|---|---|
| New selection is empty or too large | Clear previous Preview/bounds, restore JPEG, show file error and disable processing. |
| HEIC Preview unavailable | Silently omit Preview while allowing eligible processing. |
| Old image load callback fires | Ignore it and release obsolete URL; never show the previous picture. |

— `spec.md §5, AC-01, AC-02, AC-03, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12, AC-16, abridged` · [Full text](../spec.md); `sad.md §6 and §11, runtime errors and carry-forward, abridged` · [Full text](../sad.md)

## Definition of Done

- [ ] Recorded SCR-01 selection checks pass for default/empty/ready/local-validation states, byte boundaries, reset/stale Preview, zero upload requests and native controls; frontend build and lint pass.
- [ ] Every inlined hard rule remains satisfied; shared AC coverage is limited to this task's stated slice, with no claim that unfinished downstream behavior already works.
- [ ] After code changes: `npm --prefix frontend run build` before `uv run pytest`; `uv run ruff check .` and `npm --prefix frontend run lint` pass. Use focused pytest cases during development; retain existing smoke coverage.
- [ ] Only listed files change; no debug code, scratch artifacts, new test framework or unrequested abstraction remains. Record commands and actual results, including any unverified runtime behavior.
