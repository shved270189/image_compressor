---
status: Draft
owner: "Backend Lead"
reviewers: []
updated_at: "2026-09-06"
feature_size: M
---

# Data model — image-resize-convert

This feature has no persistent data model or schema change. Size M and route
standard apply; the explicit no-schema outcome requires zero migrations.

Sources: [spec §5](./spec.md#5-acceptance-criteria),
[SAD §5–§8](./sad.md#5-building-block-view),
[architecture map](../../architecture-map.md#datastores),
[foundation ADR 0003](../../adr/0003-transient-image-processing.md) and
[feature ADR 0004](./adr/0004-return-results-within-the-current-operation.md).

## ER diagram

N/A: there are no persistent entities or relationships. No `erDiagram` is emitted;
representing temporary files or buffers as tables would contradict the accepted
architecture.

## Entities

No existing or new persisted entities, aggregate roots, columns, primary keys,
foreign keys, audit columns, database constraints or delete strategy apply.
The current operation owns transient resources, not a database aggregate.

The following is the planned lifecycle from SAD §8, not an implemented schema or
an API field contract. The current source still implements only the foundation.

| Transient data | Owner and lifetime | Requirement |
|---|---|---|
| Selected file, optional Preview and transformation parameters | Current browser selection; replaced on new selection, cleared after successful handoff or page teardown; retained on recoverable failure. Failed Preview resources are released. | AC-01–AC-03, AC-15–AC-16 |
| Currentness and consumed-operation state | Current page; suppress stale or duplicate completion without a persistent result ID or lookup capability. Closing or reloading restores nothing. | AC-03, AC-13–AC-15 |
| Uploaded original | Current server request; request-scoped `UploadFile` may spool to a temporary file. Close partial uploads on parse failure/interruption and completed uploads once processing no longer needs them. | AC-12, AC-16 |
| Decoded image, color information and intermediate images | Image-processing function; structured cleanup on success or failure. Retain ownership until native work finishes even after interruption. Remove identifying metadata while preserving correct color interpretation. | AC-09–AC-10, AC-16 |
| Encoded result and download Blob URL | Server output belongs to the current response until completion/failure. Browser result resources belong only to the one download handoff; release when no longer needed without form reset interrupting download. | AC-13–AC-16 |

The input boundary allows at most 20,000,000 bytes and 40,000,000 decoded pixels,
including equality. Dimensions are independently optional positive whole pixel
bounds. Supported static inputs are JPEG, PNG, WebP and HEIC; output choices are
JPEG, PNG and WebP. The form defaults to JPEG. Supplied dimensions with omitted
format use JPEG, but omission of all transformation parameters is rejected.
These are request and processing rules, not database constraints.

No image content, original filenames or identifying metadata belongs in logs.
There is no history, result repository, saved preset, account, queue or persistent
browser image state. A file saved by the browser is the user's downloaded output,
not application-managed result persistence.

## Indexes

| Index | Columns | Query it serves |
|---|---|---|
| None | N/A | SAD §6 contains no datastore query; result delivery uses the current response without retrieval. |

## Test fixtures

No database seeds or fixture factories are generated. The existing
`tests/test_smoke.py` covers the foundation, not image processing. Feature image
and lifecycle fixtures belong to the existing pytest setup when the specified
behavior is implemented; no test infrastructure is added at this stage.

## Migrations and readiness

Zero staged migrations; no live migration files or migration directories are
created. The architecture declares `migration_tool: ""` as N/A. There is no
promote-time naming or sequence number to reserve, and no drift-fix SQL is needed.

Next: `/sdd:api image-resize-convert` defines the new processing contract. The
HEIC/color and resource/download feasibility gates in SAD §11 remain open before
`sdd:tasks`; this document does not provide runtime evidence for them.
