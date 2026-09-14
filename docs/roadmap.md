---
status: living
updated_at: "2026-09-14"
---

# Roadmap — image-compressor

> **A decomposition, not a promise.** Steps describe incremental outcomes, not delivery dates or scores; their order is the priority, and solution details belong in each feature specification.

## Destination

The owner can use a modern local single-page form to resize, convert and compress one image under independently optional dimension and file-size limits, then download the result with its actual dimensions and file size. The repository holds a complete publish recipe so the owner can later put that form on their own host with one command.

## Steps

| # | Step | Source | Size | Status |
|---|---|---|:---:|---|
| 1 | Application foundation — [`_scaffold`](features/_scaffold/) | [architecture-map.md §Module inventory](architecture-map.md#module-inventory) | M | shipped |
| 2 | Resize and convert an image — [`image-resize-convert`](features/image-resize-convert/) | [spec.md §1. Context](features/image-resize-convert/spec.md#1-context) | M | shipped |
| 3 | Compress an image to a file-size limit — [`image-size-limit`](features/image-size-limit/) | [spec.md §1. Context](features/image-size-limit/spec.md#1-context) | S | spec'd |
| 4 | Record deploy configuration — [`kamal-deploy`](features/kamal-deploy/) | [spec.md §1. Context](features/kamal-deploy/spec.md#1-context) | S | shipped |

**Resize and convert an image** delivers the complete selection-to-download flow, independently optional maximum width and height, aspect-ratio preservation, format selection with JPEG as the default and actual result dimensions and file size. An optional frontend-only preview appears above the form when the browser can display the selected file; it never uploads the file or blocks processing when unavailable. It includes the responsive visual design, accessible controls, clear errors and motion required by the brief, with mobile, desktop and reduced-motion verification. Upload limits and cleanup apply from this first processing increment. File-size targeting belongs to the following increment. The [feature specification](features/image-resize-convert/spec.md) records the agreed behavior.

**Compress an image to a file-size limit** extends the same form and processing path with an independently optional Size limit, automatic dimension reduction when needed and visible handling when the bound cannot be met. Omitting any constraint leaves that constraint unset; all three may be omitted. The [feature specification](features/image-size-limit/spec.md) records the agreed behavior.

**Record deploy configuration** adds a complete self-host publish recipe and a local configuration check without contacting the production host. Live publish, host provisioning, DNS, certificates and CI auto-publish stay out of this step. The [feature specification](features/kamal-deploy/spec.md) records the agreed behavior.

Size M reflects the foundation's module and API setup, and the first feature's new processing module, HTTP interface and complete UI flow. Size S reflects the bounded extension of that existing flow for file-size targeting, and the deploy-configuration increment (no new processing API).

## Not yet specified

None. Fog count: 0. Remaining questions are precise enough to record as open decisions rather than unformulated areas.

## Out of scope

- Live public hosting and the first publish against the server — this increment only records deploy configuration; DNS, certificates, host hardening and CI auto-publish stay later.
- Batch processing — the brief limits each operation to one image.
- Cropping and stretching — preserve the image's aspect ratio.
- History and later server retrieval — uploads and results exist only for the current request.
- Saved parameter presets — the brief selects one ordinary form.

## Open decisions

None. Fog count: 0.

D2 is resolved in [image-size-limit spec.md](features/image-size-limit/spec.md): there is no quality or dimension floor beyond one pixel and the smallest file of the chosen format; an unattainable bound still returns that smallest result with an exceeded notice and a kept form.

## Decisions so far

- Use the established Python and React stack and root development commands — [ADR 0001 §Decision](adr/0001-stack-and-development-tools.md#decision).
- Use one form, native controls, local React state and a single application service — [ADR 0002 §Decision](adr/0002-single-service-and-kamal.md#decision) and [§Interfaces and conventions](adr/0002-single-service-and-kamal.md#interfaces-and-conventions).
- Preserve aspect ratio and treat width, height and file size as independently optional constraints — [idea-brief.md §7. Recommendation](idea-brief.md#7-recommendation).
- Keep images request-scoped without persistent storage — [ADR 0003 §Decision](adr/0003-transient-image-processing.md#decision).
- Limit image processing to local use until a later live publish — [Out of scope](#out-of-scope); deploy configuration is specified in [kamal-deploy](features/kamal-deploy/spec.md).
- Enforce request-scoped image limits and cleanup without later retrieval — [ADR 0004](features/image-resize-convert/adr/0004-return-results-within-the-current-operation.md) (closes D3).

Input/output formats and upload limits (D1) are resolved in [spec.md §5. Acceptance criteria](features/image-resize-convert/spec.md#5-acceptance-criteria) and [§6. Non-functional requirements](features/image-resize-convert/spec.md#6-non-functional-requirements). Minimum quality, unattainable file-size limits and extra shrink when a Size limit is supplied (D2) are resolved in [image-size-limit spec.md](features/image-size-limit/spec.md).

## Dependency graph

```mermaid
flowchart LR
  s1["1 · Application foundation"] -->|Provides the runnable application and verification setup| s2["2 · Resize and convert an image"]
  s2 -->|Provides the form and processing path extended by file-size targeting| s3["3 · Compress an image to a file-size limit"]
  s1 -->|Provides the application image and deploy-tool lockfile| s4["4 · Record deploy configuration"]
```

## Execution path

| Wave | Steps | Zone per step (why parallel-safe) | Unlocks |
|:---:|---|---|---|
| 0 (complete) | 1 | `backend/`, `frontend/`, `tests/`, `.github/workflows/`, repository root `.`; historical foundation, no work to repeat | Existing runnable application |
| 1 (complete) | 2 | `backend/`, `frontend/src/`, `tests/`; one lane for the complete image-to-result flow | Local resizing and format conversion |
| 2 | 3 | `backend/`, `frontend/src/`, `tests/`; sequential because both feature increments modify the same form and processing path | Optional file-size targeting |
| 3 | 4 | deploy configuration and documentation at repository root; does not modify the form or processing path | Publish-ready recipe and local configuration check |

No parallel implementation lanes are planned. Open decisions must be closed before their affected step is implemented. UI polish, accessibility, resource limits and cleanup are acceptance work within the relevant step, not separate later layers.

## Shipped

| Step | Shipped | Link |
|---|---|---|
| Application foundation | 2026-09-05 | Commit `1837854` (`scaffold: materialize skeleton`); [completed tasks and local verification evidence](features/_scaffold/tasks.json) |
| Resize and convert an image | 2026-09-06 | [CHANGELOG](features/image-resize-convert/CHANGELOG.md); review [PASS](features/image-resize-convert/_review/review-2026-09-06-2.md) |
| Record deploy configuration | 2026-09-14 | [CHANGELOG](features/kamal-deploy/CHANGELOG.md); review [PASS](features/kamal-deploy/_review/review-2026-09-14.md) |

The foundation, the resize-and-convert workflow, and the self-host publish recipe are complete locally. Hosted CI and the first live publish were not verified and are not prerequisites for this local roadmap.
