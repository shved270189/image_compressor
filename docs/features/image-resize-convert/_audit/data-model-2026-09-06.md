# Data model audit — image-resize-convert

Date: 2026-09-06. Size: M. Route: standard. Mode: greenfield, no schema change.

## Artifacts and conventions

- Design: [data-model.md](../data-model.md).
- Staged migration files under `docs/features/image-resize-convert/migrations/`: none.
- Live migration changes: none. No migration or `_drift` directory is created.
- Promote-time convention hint: N/A. The architecture has no database or migration
  tool (`migration_tool: ""`); there is no next sequence number.
- Convention deviations, breaking changes, backfills, seeds and unresolved
  `TBD` markers: none.

Migration staging policy: migrations are staged, not yet in the live
`migrations/` tree; `implement` promotes them. This run generates zero migrations,
so there is nothing to promote or roll back.

The no-storage decision comes from the architecture map's Datastores section,
Accepted foundation ADR 0003 and feature ADR 0004, and SAD §4/§5/§8. It is an
explicit convention, not an undecided greenfield database choice. PK, naming,
audit-column, deletion, string/JSON and constraint choices are therefore N/A.

## Drift detection

Read-only inspection covers the actual source and dependency/configuration
files, corroborating the architecture rather than treating planned image data as
already implemented domain fields.

| Evidence | Finding |
|---|---|
| `backend/main.py` | Health response and conditional frontend serving only; no persistent domain model or database access. |
| `frontend/src/App.tsx` | Static React shell; no persisted selection, result or application storage. |
| `pyproject.toml`, `frontend/package.json` | No database, ORM or migration dependency declared. |
| Repository source and SQL/schema/migration inventory | No application schema, SQL migrations or persistence layer to map. |
| `tests/test_smoke.py` | Foundation HTTP/assets/API-404 checks; no database fixtures. |

`field-without-column`, `column-without-field`, `type-mismatch` and
`nullability-mismatch`: N/A because neither persistent fields nor columns exist.
No persistence drift or architecture/repository divergence was found. Missing
feature processing is planned work, not schema drift. No live database was queried.

## Structural self-check

| Mandatory check | Result | Evidence |
|---|---|---|
| Naming matches repository conventions | PASS (N/A for SQL identifiers) | No table, column or migration names introduced. |
| Down reversibility | PASS (empty migration set) | Zero up files and zero down files; no DDL to reverse. |
| FK indexes | PASS (no foreign keys) | No `REFERENCES` clauses or database queries requiring indexes. |
| Convention adherence | PASS | No datastore, persistent IDs, migration tooling or alternate retrieval path introduced. |

Structural self-check: 4/4 pass with the explicit N/A cases above. ER validation
is N/A: no persistent entities and no Mermaid block are emitted. Document links,
required headings, frontmatter and absence of template placeholders are checked
from the written files. `rtk git diff --check` checks tracked whitespace; an inline
Python check covers both newly created files, including links and whitespace.

Only documentation is changed by this stage. Build, pytest, runtime/browser
checks and code lint are not run; this audit does not claim feature behavior works.
The pre-existing working-tree changes in `sad.md` are preserved.

## Handoff

Next: `/sdd:api image-resize-convert`. The no-contract-change skip does not apply:
the feature introduces a processing request and binary response beyond the
existing health endpoint. The HEIC/color and resource/download evidence required
by SAD §11 remains open before tasks. No new persistence decision is deferred.

Proposed commit: `docs: record transient image resize data model`.
