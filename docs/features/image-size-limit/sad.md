---
status: Draft
owner: "Tech Lead"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-12"
feature_size: S
target_surfaces: [backend-service, web-frontend]
---

# Software Architecture Document — image-size-limit

**Design review — 2026-09-12.** All twelve sections were approved through the easy-depth design walk (route quick, size S). An independent clean-context critic reviewed the written SAD and two ADRs and returned `NO_CONTESTED_DECISIONS`. All three Mermaid blocks rendered with `mmdc`. Structural checks confirmed the section count, declared surfaces, Accepted ADRs, closed ADR index and absence of template placeholders. NFR targets in §10 match spec §6 verbatim.

## 1. Introduction and goals

**Intent.** Let Image owner apply an independently optional Size limit on the existing one-form workflow. When the bound is attainable, produce the largest proportional Result that still fits. When it is not, still produce the smallest chosen-format file, start one automatic download, keep the form, and show the actual size plus that the bound was exceeded. Canonical requirements: [spec.md](./spec.md) and [ux-flows.md](./ux-flows.md).

**Top-3 quality goals (1-liners; full scenarios in §10):**

1. Bound arithmetic: 1 Mb = 1,000,000 bytes and 1 Kb = 1,000 bytes, compared after encoding in whole bytes.
2. Miss visibility: after an over-limit Result, actual size and the exceeded notice remain until the next process, a new file selection or page close.
3. Accessible Size limit: keyboard-usable number and unit, visible focus, and a complete flow at 360 and 1280 CSS pixels with no horizontal page overflow.

**Stakeholders.**

| Role | Interest | Sign-off owner? |
|---|---|---|
| Image owner | Optional result byte budget, retryable miss, accessible form | Yes, product and manual contrast acceptance |
| Tech Lead | SAD approval, miss-header contract, extra-shrink in image functions | Yes |
| Security Lead | Residual risk only; no new authz boundary | Yes, residual review if decoding or resource ownership changes |

The owner approved depth easy, size S and route quick. Documents remain English, matching this feature folder. Domain terms follow [CONTEXT.md](./CONTEXT.md).

## 2. Constraints

**Technical.** Reuse Python 3.14, FastAPI, Uvicorn, Pillow 12.3.0 and pillow-heif 1.6.0 from the foundation and Python lockfile. Reuse React, Vite, TypeScript and Tailwind with the existing npm lockfile. HTTP validation belongs in `backend/main.py`; extra-shrink and encoding belong in `backend/images.py`. Uploads stay request-scoped. Input limits stay at most 20,000,000 bytes and 40,000,000 decoded pixels of the selected static image, equality allowed. Size limit is not an upload cap. No datastore, queue, result ID or retrieval.

**Organisational.** Size S, about one week. No launch deadline, public-hosting requirement, throughput target or latency measurement. The owner runs setup. Tech Lead owns this SAD.

**Conventions.** Follow [AGENTS.md](../../../AGENTS.md), the [architecture map](../../architecture-map.md) and [foundation ADRs](../../adr/). React uses local state, native accessible controls, relative `/api` fetches and theme tokens in `frontend/src/index.css`. Preserve API 404s and backend startup before the first frontend build. Use root mise tasks and existing uv, npm and Bundler lockfiles. Extend `POST /api/v1/images/process` rather than adding an endpoint.

**Privacy / external constraints.** Originals are confidential. No accounts, identity fields or lookup. AuthZ/AuthN impact is none. Security review is N/A for this increment: no new authz boundary and no new PII (spec §6.1). Residual risk is owner-induced long encoding search and misread units. No additional regulatory regime is asserted.

## 3. Context and scope

Image owner already resizes and converts one Original on a local single page. This increment adds Size limit to that same form. Preview remains frontend-only. The server treats uploaded content and parameters as untrusted.

<!-- brownfield: architecture map reflects 86ac0c5 (image-resize-convert shipped); HEAD af40862 is the survey commit. Module layout, layering and datastores are unchanged. -->

**External systems (in / out):**

| Actor or system | Type | Interaction |
|---|---|---|
| Image owner | Person | Selects an Original, sets optional maxima, Size limit and format, receives a Result |
| Native browser facilities | Client platform | File selection, optional Preview, download handoff |
| External application services | None | No third-party processing, identity provider or remote storage |

**Trust boundary.** Browser checks are usability controls. The Application enforces file presence, supplied parameters, Size limit arithmetic, actual file bytes, supported content and decoded pixel limits. A result belongs only to its active response. There is no lookup that could expose another operation.

**C4 Context (L1):**

```mermaid
C4Context
    title image-size-limit - System Context
    Person(owner, "Image owner", "Selects one original and optional maxima, Size limit and format")
    System(compressor, "Image compressor", "Single-image resize, convert and optional result byte budget")
    Rel(owner, compressor, "Opens the application and processes one image", "HTTP locally; HTTPS after deployment")
```

One local application. No external application services.

## 4. Solution strategy

1. **Extend the existing process surfaces.** Declare `target_surfaces: [backend-service, web-frontend]`. The web surface is the existing React SPA with local state, no client router and native controls. Size limit extends the current parameter fieldset on SCR-01; there is no second screen. The backend surface is the existing FastAPI application. These are logical C4 containers, not two deployed services. [ADR 0001](./adr/0001-extend-existing-process-surfaces.md) records the surface contract and inherits [foundation ADR 0002](../../adr/0002-single-service-and-kamal.md).

2. **Keep the existing SPA delivery.** UI architecture stays the current client-rendered React page, React local state, relative fetch and no router. This does not cross the ADR gate: [foundation ADR 0002](../../adr/0002-single-service-and-kamal.md) already forbids a separate production frontend server and a client-side router for a single page.

3. **Apply bound-driven extra shrink in image functions.** Empty Size limit keeps the current geometry rule in `output_size`: largest proportional fit to supplied maxima, no extra reduction. A supplied bound is the primary constraint: after that ceiling, `backend/images.py` may reduce pixels below maxima and below the Original, without cropping, stretching, enlargement or a silent format change, and stop at the largest proportional size and highest encoding quality that already meets the bound. One pixel and the smallest file of the chosen format that still exceed the bound are a miss, not a rejection without a file. The exact search procedure is task-level provided AC-05 holds.

4. **Signal a miss on the binary response.** Keep the complete binary Result and attachment filename. When a bound was supplied, also send miss facts on the response so the Browser UI can start one download and then either reset (met) or keep the form (miss). Do not use a client-error status for an unattainable bound. Do not wrap the file in JSON or multipart metadata. [ADR 0002](./adr/0002-signal-size-limit-miss-with-headers.md) records this choice.

A supplied Size limit counts as a transformation parameter, including with only the initial JPEG and no maxima. Invalid zero, negative or non-positive values are rejected with no Result and the Original kept. Paths, error schema and status codes belong to `sdd:api`.

## 5. Building block view

Reuse the existing split: browser form, HTTP boundary, ordinary image functions. No new package, repository, worker or datastore. The backend calls image functions directly.

| Location | Responsibility |
|---|---|
| `frontend/src/App.tsx` | SCR-01, Size limit number and unit, current operation, download, miss notice, reset |
| `frontend/src/index.css` | Existing theme tokens and reduced-motion rules |
| `backend/main.py` | Multipart validation including Size limit, byte conversion, response headers, resource ownership |
| `backend/images.py` | Existing decode/orient/encode plus extra-shrink search when a bound is supplied |
| `tests/` | Existing smoke coverage plus specified bound, miss and geometry behavior |

Native encoding must not block the asynchronous HTTP event loop. At most one submitted processing operation; file selection and all transformation controls including Size limit are disabled while processing.

**C4 Container (L2):**

```mermaid
C4Container
    title image-size-limit - Containers
    Person(owner, "Image owner", "Uses the local application")
    Container_Boundary(compressor, "Image compressor") {
        Container(web, "Browser UI", "React, TypeScript, Tailwind", "Form, local Preview, Size limit, download and miss notice")
        Container(app, "Application", "FastAPI, Pillow, pillow-heif", "Validation, extra-shrink, binary result and miss headers")
    }
    Rel(owner, web, "Selects an Original and requests a Result")
    Rel(web, app, "Submits one processing operation and receives its result", "Relative API request")
    Rel(app, web, "Serves built frontend assets", "HTTP")
```

Development uses the existing Vite proxy. The built application serves frontend assets directly. No ContainerDb.

## 6. Runtime view

**Critical flow: process with optional Size limit, then met-limit reset or miss keep-form.**

```mermaid
sequenceDiagram
    actor Owner as "Image owner"
    participant Web as Browser UI
    participant App as Application
    Owner->>Web: Set optional Size limit and process
    Web->>Web: Lock controls and mark current operation
    Web->>App: Send Original and transformation parameters
    App->>App: Validate bound, content and input limits
    alt Bound omitted
        App->>App: Fit maxima only, no extra shrink
        App-->>Web: Complete binary Result
        Web->>Web: Check current operation and initiate one download
        Web-->>Owner: Clean form after browser handoff
    else Bound supplied and encoded bytes meet it
        App->>App: Extra-shrink to largest proportional fit that meets the bound
        App-->>Web: Complete binary Result with met-limit facts
        Web->>Web: Check current operation and initiate one download
        Web-->>Owner: Clean form after browser handoff
    else Bound supplied and even one pixel exceeds it
        App->>App: Encode smallest chosen-format file
        App-->>Web: Complete binary Result with miss facts
        Web->>Web: Check current operation and initiate one download
        Web-->>Owner: Keep form, show actual size and exceeded notice
    else Recoverable failure
        App-->>Web: Explain rejection or processing failure
        Web-->>Owner: Restore controls with current file and parameters
    end
    App->>App: Release remaining owned operation resources
```

The seed above stays as the collapsed overview from design. The five flows below expand it to every spec §4 user story and §5 acceptance criterion. Participants are generic (`<user>`, `<ui>`, `<service>`). There is no `<data-store>`: §5 declared none, and no flow persists an entity.

### Set optional Size limit

```mermaid
sequenceDiagram
    autonumber
    actor U as <user>
    participant UI as <ui>
    participant S as <service>

    Note over U,UI: Precondition: Original selected on SCR-01, JPEG default, empty Size limit
    UI-->>U: Offer Size limit number with unit Mb or Kb, Mb selected initially
    U->>UI: Leave empty or enter a positive decimal
    alt Bound empty
        UI-->>U: Apply no result byte bound, keep existing dimension and format rules
        U->>UI: Submit processing
        UI->>UI: Lock file selection and transformation controls including Size limit
        Note over U,UI: Continues on SCR-01 through US-02 then US-03
    else Bound is a positive number
        UI-->>U: Accept bound as a transformation parameter, including JPEG only and no maxima
        U->>UI: Submit processing
        UI->>S: Request processing with bound and chosen format
        S-->>UI: Accept, a transformation parameter is supplied
        UI->>UI: Lock file selection and transformation controls including Size limit
        Note over U,S: Continues on SCR-01 through US-02 then US-03 or US-04
    else Bound is zero, negative, or not a positive number
        UI-->>U: Reject through US-05, keep Original
    else User selects another file
        UI->>UI: Reset bound, unit to Mb, JPEG and miss facts
        UI-->>U: Show initial form with the new Original
    end
    Note over U,UI: Postcondition: empty means no bound, a supplied positive bound is enough to process, invalid values never start processing
```

### Shrink below dimension ceiling

```mermaid
sequenceDiagram
    autonumber
    actor U as <user>
    participant UI as <ui>
    participant S as <service>

    Note over U,S: Precondition: current operation in progress on SCR-01, controls locked, Original plus optional maxima, bound and format already submitted
    UI->>S: Process Original with optional maxima, bound and chosen format
    alt Bound omitted
        S->>S: Fit largest proportional scale to supplied maxima, no extra shrink
        Note over S: Oriented 2400 by 1200 with only max width 1200 yields 1200 by 600
        S-->>UI: Return encoded Result
        Note over U,UI: Continues on SCR-01 through US-03
    else Bound supplied and encoded bytes meet it
        Note over S: Bound bytes equal entered number times 1000000 for Mb or 1000 for Kb. 0.5 Mb equals 500000 bytes
        S->>S: Encode in the chosen format and compare whole result bytes to the bound
        S->>S: Reduce proportionally and encoding quality only while the file is larger than the bound
        S->>S: Stop at the largest proportional size and highest quality that already meets the bound
        Note over S: Never exceed maxima or original, never enlarge, crop, stretch, or change format. Halves round up, minimum one pixel
        S-->>UI: Return encoded Result that meets the bound
        Note over U,UI: Continues on SCR-01 through US-03
    else Bound supplied and even one pixel exceeds it
        S->>S: Encode the smallest file of the chosen format
        S-->>UI: Return encoded Result that still exceeds the bound
        Note over U,UI: Continues on SCR-01 through US-04, not a rejection without a file
    end
    Note over U,S: Postcondition: Result never exceeds maxima or original, keeps the chosen format, extra shrink only while over the bound
```

### Download when within limit

```mermaid
sequenceDiagram
    autonumber
    actor U as <user>
    participant UI as <ui>
    participant S as <service>

    Note over U,S: Precondition: processing completed on SCR-01 after US-02
    S-->>UI: Deliver encoded Result and whether the bound was omitted or met
    alt Completion is not the current operation
        UI->>UI: Ignore stale completion
        UI-->>U: No download and no form change
    else Bound omitted or encoded bytes at most the bound
        UI->>UI: Initiate exactly one automatic download
        UI-->>U: Browser starts the download
        UI->>UI: After handoff clear file, Preview, result, errors, miss facts, maxima and Size limit, reset JPEG
        UI-->>U: Show the initial empty form
    else Bound supplied and encoded bytes exceed it
        Note over U,UI: Continues on SCR-01 through US-04
    end
    opt User closes or reloads
        UI-->>U: Restore neither input nor result
        Note over U,UI: No history, lookup or retrieval exists for this or another result
    end
    Note over U,UI: Postcondition: a met or omitted bound leaves a clean form with no result characteristics
```

### Retry after a miss

```mermaid
sequenceDiagram
    autonumber
    actor U as <user>
    participant UI as <ui>
    participant S as <service>

    Note over U,S: Precondition: processing in progress on SCR-01, file selection and all transformation controls including Size limit locked, truthful busy state, no cancel
    S-->>UI: Deliver smallest chosen-format Result that still exceeds the bound
    Note over S: Release remaining owned operation resources. Nothing is persisted
    alt Completion is not the current operation
        UI->>UI: Ignore stale completion
        UI-->>U: No download and no miss facts from the old operation
    else Bound is met
        Note over U,UI: Continues on SCR-01 through US-03
    else Bound still exceeded
        UI->>UI: Initiate exactly one automatic download
        UI-->>U: Browser starts the download
        UI-->>U: Keep the form, show actual Result size and that Size limit was exceeded
        UI-->>U: Unlock controls with Original and parameters still present
    else Recoverable failure
        S-->>UI: Explain processing failure
        UI-->>U: Restore retry with the current file and parameters
    end
    alt User changes settings and processes again
        UI->>UI: Replace previous miss facts
        UI->>UI: Lock controls and mark a new current operation
        Note over U,UI: Continues on SCR-01 through US-02
    else User selects a new file
        UI->>UI: Reset Preview, miss facts, errors, maxima, format and Size limit
        UI-->>U: Show initial form with the new Original
    else User closes or reloads
        UI-->>U: Restore neither input nor result
    end
    Note over U,UI: Postcondition: after a miss the owner can change settings and process again. A new file starts a new cycle. Nothing is stored for later retrieval
```

### Correct an invalid Size limit

```mermaid
sequenceDiagram
    autonumber
    actor U as <user>
    participant UI as <ui>
    participant S as <service>

    Note over U,S: Precondition: Original selected on SCR-01, Size limit filled
    U->>UI: Attempt processing with the filled bound
    UI->>S: Request processing with bound and unit
    alt Bound is zero, negative, or not a positive number
        S-->>UI: Reject, bound must be a positive number with Mb or Kb or left empty
        UI-->>U: Show the reason, produce no Result, keep Original
        U->>UI: Correct or clear Size limit
        Note over U,UI: Continues on SCR-01 through US-01
    else Bound is empty or a positive number with Mb or Kb
        Note over U,S: Continues on SCR-01 through US-01 submit
    end
    Note over U,UI: Postcondition: invalid bound never produces a Result. Original remains so the owner can fix the field without choosing a new file
```

### Coverage

| User story | Flow |
|---|---|
| US-01 Set optional Size limit | Set optional Size limit |
| US-02 Shrink below dimension ceiling | Shrink below dimension ceiling |
| US-03 Download when within limit | Download when within limit |
| US-04 Retry after a miss | Retry after a miss |
| US-05 Correct an invalid Size limit | Correct an invalid Size limit |

| AC | Shown by |
|---|---|
| AC-01 | Set optional Size limit — `alt` Bound empty |
| AC-02 | Set optional Size limit — happy path, Mb or Kb with Mb initially selected |
| AC-03 | Set optional Size limit — `else` Bound is a positive number, JPEG only accepted |
| AC-04 | Shrink below dimension ceiling — `alt` Bound omitted, 2400 by 1200 with max width 1200 yields 1200 by 600 |
| AC-05 | Shrink below dimension ceiling — extra-shrink happy path and `else` one-pixel miss continues through US-04 |
| AC-06 | Download when within limit — one automatic download then clean form |
| AC-07 | Retry after a miss — download smallest file, keep form, show actual size and exceeded notice |
| AC-08 | Correct an invalid Size limit — reject, no Result, Original kept |
| AC-09 | Non-runtime N/A: no history, lookup or retrieve participant or step. Stated as a note on Download when within limit close/reload |
| AC-10 | Set optional Size limit and Retry after a miss — `alt` User selects another file |
| AC-11 | Retry after a miss — lock/busy precondition, stale ignore, failure restore, close/reload. Download when within limit — stale ignore |
| AC-12 | Shrink below dimension ceiling — bound-bytes note (1 Mb = 1000000, 1 Kb = 1000, 0.5 Mb = 500000) |

### Runtime flags

- No flow uses `<data-store>`, `<message-bus>` or `<external-system>`. §5 declared none. Nothing is persisted. `data-model` is N/A: no new entity, column or index.
- All five flows are synchronous. No idempotency key, retry or dead-letter branch is required.
- The design-stage seed diagram above is unchanged.
- No new ADR. Miss headers and extra-shrink rules stay in [ADR 0002](./adr/0002-signal-size-limit-miss-with-headers.md) and §4.

## 7. Deployment view

<!-- N/A: reuses existing deployment unit, no infra change -->

Same multi-stage Docker image and Uvicorn process as the shipped foundation. No new replica, worker, volume or health path.

## 8. Crosscutting concepts

| Concept | Convention | Where defined |
|---|---|---|
| Logging | No image bytes, original filenames or identifying metadata | Foundation ADR 0003, architecture map |
| Authentication | None; local owner-operated application | spec §6.1 |
| Error handling | Manual HTTP-boundary validation, safe FastAPI errors | `backend/main.py`, foundation ADR 0002 |
| ID strategy | N/A — no stored entities or result IDs | Foundation ADR 0003 |
| Internationalisation | N/A, single language | — |
| Observability | Stdout/stderr only; no latency KPI | spec §6 |
| Events | N/A — synchronous in-process call | §4, §5 |
| Bound transport | Optional multipart fields `size_limit` (positive decimal) and `size_unit` (`mb` or `kb`); empty omits the bound; server converts with 1 Mb = 1,000,000 and 1 Kb = 1,000 | This section, ADR 0002 |
| Miss facts | When a bound was supplied, response headers `X-Result-Bytes` (whole encoded bytes) and `X-Size-Limit-Met` (`true` or `false`); omit both when the bound is omitted | This section, ADR 0002 |
| Current operation | One AbortController; stale completions never download or restore miss facts | Existing Browser UI, spec AC-10 and AC-11 |

## 9. Architecture decisions

| # | Title | Status | Section |
|---|---|---|---|
| 0001 | Extend existing process surfaces | Accepted | §4 |
| 0002 | Signal size-limit miss with headers | Accepted | §4 |

ADR files live under `docs/features/image-size-limit/adr/`.

## 10. Quality requirements

Each top-3 goal from §1 expanded into a full scenario. Numbers are from spec §6 NFR verbatim.

**QG-1. Bound arithmetic**
- **When:** Image owner supplies Size limit and processing encodes a Result
- **Then:** the bound in bytes equals the entered number multiplied by 1,000,000 for Mb or by 1,000 for Kb; comparison uses whole bytes of the encoded Result; 0.5 Mb equals 500,000 bytes; 200 Kb equals 200,000 bytes
- **How verify:** fixture tests for those two conversions and whole-byte comparison after encoding

**QG-2. Miss visibility**
- **When:** an over-limit Result is produced
- **Then:** actual size and the exceeded notice remain until the next process, a new file selection or page close
- **How verify:** browser check of the kept form

**QG-3. Accessible, responsive Size limit**
- **When:** Image owner uses the Size limit number and unit
- **Then:** every interactive control including that number and unit is keyboard-usable with visible focus; labels, errors and the exceeded notice pass the project owner's manual readable-contrast review; reduced motion as on the existing form; complete flow at viewport widths 360 and 1280 CSS pixels with no horizontal page overflow, including the unit choice beside the number
- **How verify:** keyboard flow, visible-focus review, owner contrast acceptance, reduced-motion check, browser visual review at both widths

Preserve existing input limits (at most 20,000,000 bytes and 40,000,000 decoded pixels) and form concurrency (at most one submitted processing operation; controls including Size limit disabled while processing). Performance latency, throughput and public-service uptime are N/A per spec §6.

## 11. Risks and technical debt

| Risk / debt | Severity | Mitigation | Owner |
|---|---|---|---|
| A tight bound on a large original can hold the only screen in a busy state with no cancel | Medium | Keep a truthful busy state without fabricated percentages; cancel remains a non-goal | Project owner |
| A one-pixel or lowest-quality file that still meets the bound follows the success reset and can be used as if it were a useful result | Low | Specified success path; no extra warning this increment | Project owner |
| A future reverse proxy may strip custom miss headers | Low | Same-origin today; if headers are missing, compare `blob.size` to the bound | Tech Lead |

**Accepted debt (acceptable in v1, plan to fix later):**
- Extra-shrink search procedure is not locked. The implementer chooses the search in `backend/images.py` as long as AC-05 holds (largest proportional size and highest encoding quality that already meets the bound; nearest-pixel rounding, halves up, minimum one pixel).

## 12. Glossary

| Term | Meaning |
|---|---|
| Image owner | The person processing their selected image. NOT an application account or permission role. |
| Size limit | Independently optional upper bound on Result file size, entered as a positive float with unit Mb (default) or Kb (1 Mb = 1,000,000 bytes, 1 Kb = 1,000 bytes). NOT the 20,000,000-byte upload cap on Original. |
| Maximum dimensions | Independently optional upper width and height bounds in pixels. NOT exact dimensions, cropping or stretching. |
| Original | The image file selected for the current operation. NOT a file overwritten by processing. |
| Preview | An optional frontend-only representation of the selected original above the form when the browser can display it. NOT the processed result or a server-generated image. |
| Result | The processed file ready to download for the current operation. NOT the original or a persistent server file. |
| miss | An unattainable Size limit: even one pixel and the smallest file of the chosen format still exceed the bound. A Result is still produced and downloaded. |
