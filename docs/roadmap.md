---
status: living
updated_at: "2026-09-05"
---

# Roadmap — image-compressor

> **A decomposition, not a promise.** Steps describe incremental outcomes, not delivery dates or scores; their order is the priority, and solution details belong in each feature specification.

## Destination

The owner can use a modern local single-page form to resize, convert and compress one image under independently optional dimension and file-size limits, then download the result with its actual dimensions and file size.

## Steps

| # | Step | Source | Size | Status |
|---|---|---|:---:|---|
| 1 | Application foundation — [`_scaffold`](features/_scaffold/) | [architecture-map.md §Module inventory](architecture-map.md#module-inventory) | M | shipped |
| 2 | Resize and convert an image — [`image-resize-convert`](features/image-resize-convert/) | [spec.md §1. Context](features/image-resize-convert/spec.md#1-context) | M | spec'd |
| 3 | Compress an image to a file-size limit — `image-size-limit` | [idea-brief.md §2. Problem](idea-brief.md#2-problem), [§7. Recommendation](idea-brief.md#7-recommendation) | S | idea |

**Resize and convert an image** delivers the complete selection-to-download flow, independently optional maximum width and height, aspect-ratio preservation, format selection with JPEG as the default and actual result dimensions and file size. An optional frontend-only preview appears above the form when the browser can display the selected file; it never uploads the file or blocks processing when unavailable. It includes the responsive visual design, accessible controls, clear errors and motion required by the brief, with mobile, desktop and reduced-motion verification. Upload limits and cleanup apply from this first processing increment. File-size targeting belongs to the following increment. The [feature specification](features/image-resize-convert/spec.md) records the agreed behavior.

**Compress an image to a file-size limit** extends the same form and processing path with an independently optional MB limit, automatic dimension reduction when needed and clear handling of unattainable limits. Omitting any constraint leaves that constraint unset; all three may be omitted.

Size M reflects the foundation's module and API setup, and the first feature's new processing module, HTTP interface and complete UI flow. Size S reflects the bounded extension of that existing flow for file-size targeting; its acceptance rules must be settled before implementation.

## Not yet specified

None. Fog count: 0. Remaining questions are precise enough to record as open decisions rather than unformulated areas.

## Out of scope

- Public hosting and Kamal deployment — the owner chose a local-only roadmap; existing deployment tooling stays unchanged.
- Batch processing — the brief limits each operation to one image.
- Cropping and stretching — preserve the image's aspect ratio.
- History and later server retrieval — uploads and results exist only for the current request.
- Saved parameter presets — the brief selects one ordinary form.

## Open decisions

| # | Question | Type | Owner | Blocks |
|---|---|:---:|:---:|:---:|
| D2 | What minimum quality and dimensions are acceptable, and what should the user receive when the requested file-size limit cannot be met? See [idea-brief.md §6. Risks](idea-brief.md#6-risks) and [§8. Open questions](idea-brief.md#8-open-questions). | grilling | human | 3 |
| D3 | How will the request lifecycle enforce resource limits and release upload handles, decoded images and result buffers after success, errors and interrupted transfer? Verify the existing stack's lifecycle behavior before implementing processing, following [ADR 0003 §Decision](adr/0003-transient-image-processing.md#decision). | research | agent | 2 |

D2 closes during the file-size-limit specification. D3 requires design verification before planning processing implementation, followed by lifecycle tests during implementation. The resize-and-convert specification is recorded; the file-size-limit feature remains an idea.

## Decisions so far

- Use the established Python and React stack and root development commands — [ADR 0001 §Decision](adr/0001-stack-and-development-tools.md#decision).
- Use one form, native controls, local React state and a single application service — [ADR 0002 §Decision](adr/0002-single-service-and-kamal.md#decision) and [§Interfaces and conventions](adr/0002-single-service-and-kamal.md#interfaces-and-conventions).
- Preserve aspect ratio and treat width, height and file size as independently optional constraints — [idea-brief.md §7. Recommendation](idea-brief.md#7-recommendation).
- Keep images request-scoped without persistent storage — [ADR 0003 §Decision](adr/0003-transient-image-processing.md#decision).
- Limit this roadmap to local use — [Out of scope](#out-of-scope), as selected by the owner during roadmap review.

Input/output formats and upload limits (D1) are resolved in [spec.md §5. Acceptance criteria](features/image-resize-convert/spec.md#5-acceptance-criteria) and [§6. Non-functional requirements](features/image-resize-convert/spec.md#6-non-functional-requirements).

## Dependency graph

```mermaid
flowchart LR
  s1["1 · Application foundation"] -->|Provides the runnable application and verification setup| s2["2 · Resize and convert an image"]
  s2 -->|Provides the form and processing path extended by file-size targeting| s3["3 · Compress an image to a file-size limit"]
```

## Execution path

| Wave | Steps | Zone per step (why parallel-safe) | Unlocks |
|:---:|---|---|---|
| 0 (complete) | 1 | `backend/`, `frontend/`, `tests/`, `.github/workflows/`, repository root `.`; historical foundation, no work to repeat | Existing runnable application |
| 1 | 2 | `backend/`, `frontend/src/`, `tests/`; one lane for the complete image-to-result flow | Local resizing and format conversion |
| 2 | 3 | `backend/`, `frontend/src/`, `tests/`; sequential because both feature increments modify the same form and processing path | Optional file-size targeting |

No parallel implementation lanes are planned. Open decisions must be closed before their affected step is implemented. UI polish, accessibility, resource limits and cleanup are acceptance work within the relevant step, not separate later layers.

## Shipped

| Step | Shipped | Link |
|---|---|---|
| Application foundation | 2026-09-05 | Commit `1837854` (`scaffold: materialize skeleton`); [completed tasks and local verification evidence](features/_scaffold/tasks.json) |

The foundation is complete locally. Hosted CI and public deployment were not verified and are not prerequisites for this local roadmap.
