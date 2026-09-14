# API sync report — kamal-deploy

Date: 2026-09-13. Size: S. Route: quick, from `.size` and `.route`.
Contract: [cli.md](./cli.md) (CLI — commands, flags, exit codes). No `openapi.yaml`.
No `events.md`: every sad.md §6 flow is synchronous; `<external-system>` is isolation-only (zero host and registry connections), not an enqueue/retry actor.

## Gate and inputs

`data-model.md` is absent — legal fast-lane skip (no schema change). sad.md §5 names no new building blocks or entities (repository-root files plus a pytest module), no staged `docs/features/kamal-deploy/migrations/`, and spec.md introduces no new entity. `<data-store>` in §6 is local files, not a database. Fields are derived from the **existing schema**: Kamal 2.12.0 `config/deploy.yml` keys plus `.kamal/secrets`, [architecture-map.md](../../../architecture-map.md) §Conventions / Container and CI (`proxy.app_port: 8000`, `proxy.healthcheck.path: /api/health`), foundation [ADR 0002](../../../adr/0002-single-service-and-kamal.md), this feature's spec §4/§5, sad.md §5/§6, and feature ADRs 0001–0002.

Found: `spec.md`, `sad.md` (`target_surfaces: [cli]`), all three §6 sequences, feature [CONTEXT.md](../CONTEXT.md), `.size` S, `.route` quick, feature ADRs 0001 and 0002.
Missing: `data-model.md` (legal skip), root `CONTEXT.md` (feature glossary used), live `migrations/` (N/A — no datastore), existing `contracts/` (first write).
Interface kind: **CLI** from declared `cli`. Not HTTP. ADR 0001: this feature does not add `backend-service` or `web-frontend`.

English identifiers stay English. Glossary terms in failure text stay the feature glossary: Configuration check, Deploy configuration, Public site name, Secrets file, Project owner, Image owner.

## A. Field origins

| Schema path | Origin | Confidence |
|---|---|---|
| `configurationCheck.invocation` | feature ADR 0002; sad.md §4/§5 Rel `uv run pytest`; architecture-map `test_cmd` | high |
| `configurationCheck.module` | sad.md §5 `tests/test_kamal_deploy.py`; feature ADR 0002 planned path | high |
| `configurationCheck.flags` | feature ADR 0002 — no mise wrapper, no Kamal-native check flags | high |
| `configurationCheck.exit.0` | spec AC-03; sad.md §6 success branch; pytest success | high |
| `configurationCheck.exit.1` | spec AC-04; sad.md §6 missing-field branch; pytest test failure | high |
| `configurationCheck.network.isolation` | spec §6 NFR; sad.md §6 Note over S,X; QG-2 | high |
| `configurationCheck.runtime_s` | spec §6 ≤ 30 s | high |
| `laterPublish.invocation` | spec US-05, AC-05; sad.md glossary Later publish command | high |
| `laterPublish.executed_this_step` | spec §3 / AC-05 — must not run | high |
| `recipe.service` | spec AC-01 service name `image_compressor`; Kamal 2.12 required `service` | high |
| `recipe.image` | spec AC-01 image `shved270189/image_compressor`; Kamal 2.12 required `image` | high |
| `recipe.servers.web` | spec AC-01 host address `138.201.118.229`; Kamal 2.12 `servers` / primary role `web` | medium |
| `recipe.proxy.hosts` | spec AC-01 both Public site names; Kamal 2.12 `proxy.hosts` (plural when more than one) | high |
| `recipe.proxy.ssl` | spec AC-01 HTTPS enabled; Kamal 2.12 `proxy.ssl` | high |
| `recipe.proxy.app_port` | spec AC-08; foundation ADR 0002; architecture-map; Kamal 2.12 `proxy.app_port` = 8000 | high |
| `recipe.proxy.healthcheck.path` | spec AC-08; foundation ADR 0002; architecture-map; Kamal 2.12 `proxy.healthcheck.path` = `/api/health` | high |
| `recipe.registry.username` | spec AC-01 `shved270189`; Kamal 2.12 `registry.username` | high |
| `recipe.registry.password` (name only) | spec AC-02 env-var names allowed; Kamal 2.12 `registry.password` list of names | high |
| `recipe.registry.password` token `KAMAL_REGISTRY_PASSWORD` | Kamal 2.12 default name in docs; spec does not lock the token, only that a name (not a value) may appear | medium |
| `recipe.builder.arch` | spec AC-01 amd64; sad.md §11 `builder.arch: amd64`; Kamal 2.12 required `builder.arch` | high |
| `secrets.registry_password` | spec AC-03/AC-04; CONTEXT.md Secrets file `.kamal/secrets` | high |
| `secrets.gitignored` | spec AC-02; sad.md §5 `.gitignore` must ignore `.kamal/secrets` | high |
| `errors.*.code` | contract proposal — no repo error registry; user-visible text is glossary terms (AC-04) | medium |

No field was invented without an origin. `servers.web` is the Kamal 2.12 primary-role host list for a single web role (sad.md §7: one host, no accessory). If implementation uses an equivalent Kamal 2 host list that still records `138.201.118.229`, that is the same field. The example Secrets name `KAMAL_REGISTRY_PASSWORD` is Kamal's usual name, not a spec-locked token.

## B. Drift findings

### Four-point structural check

| Check | Result | Evidence |
|---|---|---|
| Endpoint ↔ data model (core) | PASS with persistent-entity check N/A | No entities, IDs, columns or migrations. `configurationCheck` reads Deploy configuration and the Secrets file (existing Kamal 2.12 files). `laterPublish` is documented only. Record-configuration is a file write, not a binary. |
| Error code ↔ repository (core) | PASS with domain-code registry N/A | No error registry in the repo. User-visible failures name glossary terms (AC-04). `kamal_deploy.*` codes are the contract's proposal for test ids; reconcile if the repo later defines a registry. |
| Validation ↔ constraints (core) | PASS | Locked values, both Public site names, exact service name, amd64, port 8000, path `/api/health`, secret values absent from git, password present for success — match AC-01, AC-02, AC-04, AC-08 and foundation ADR 0002. Stricter: both Public site names required (AC-04 "either" missing fails). |
| OpenAPI ↔ sequences (supporting) | PASS as CLI ↔ sequences | Methods/paths N/A. Command and outcome branches map below. No Idempotency-Key: all flows sync. `<external-system>` is a zero-connection guard, not an async producer. |

Defaults not used (CLI, not HTTP): OpenAPI 3.1, BearerAuth, cursor pagination, URL versioning, JSON `{code, message, details?}`. Deviation by surface (ADR 0001), not by a silent HTTP contract. pytest exit codes replace HTTP status. Assertion messages replace the JSON envelope; they must still name each gap in glossary terms.

No unresolved core finding. Two medium-confidence rows (`servers.web` role key; example password env-var token) are declared incompleteness, not a pause. Zero flags requiring Accept / Fix / Save-as-OQ / Drop.

### Operation and branch coverage

| SAD section 6 branch | Command / outcome |
|---|---|
| Record deploy configuration — required facts present, secrets stay local, port and path match | File write of `config/deploy.yml` + Secrets file + README later command; `configurationCheck` exit 0 |
| Record — secret value in committed recipe | `kamal_deploy.secret_in_committed_tree`; `.kamal/secrets` gitignored; not success |
| Record — port or health-check path does not match the application image | `kamal_deploy.production_target_invariant_violated`; not success |
| Run configuration check — recipe complete and registry password present | `configurationCheck` exit 0; no host/registry contact |
| Run configuration check — required field or secret missing | `configurationCheck` exit 1; each gap named in glossary terms |
| Form — Image owner processes one image | Out of this surface; existing process path unchanged (AC-07) |
| Form — anyone looks for a publish or Configuration check action on the form | No command, flag, or HTTP path added (AC-06) |

Sequence gap: none. Record-configuration is not a CLI binary; its `else` branches are enforced by the same check and gitignore, which is what the sequences persist and then the check reads. Not filed as an upstream OQ.

Orphan command: none. `laterPublish` maps to US-05 / the README write in the record flow and is explicitly not executed.

### Acceptance-criteria back-feed

Every AC maps to ≥1 command, file invariant, or explicit out-of-surface boundary. Every command maps to a §4 user story.

| AC | Contract coverage / explicit boundary |
|---|---|
| AC-01 | Recipe field table: host, both Public site names, image, registry username, HTTPS, service name, amd64, port, health-check path |
| AC-02 | Secret values only in gitignored Secrets file; recipe may hold env-var names; `kamal_deploy.secret_in_committed_tree` |
| AC-03 | `configurationCheck` exit 0; zero host/registry connections; must not invoke Kamal network commands |
| AC-04 | `configurationCheck` exit 1; each missing required field or secret named in glossary terms |
| AC-05 | `laterPublish` = exactly `bundle exec kamal deploy` in README; not executed this step |
| AC-06 | Compression form out of surface — no publish or Configuration check action |
| AC-07 | No change to process/selection/limits/download/cleanup; no persistent image store |
| AC-08 | `proxy.app_port` 8000 and `proxy.healthcheck.path` `/api/health`; mismatch is `kamal_deploy.production_target_invariant_violated` |

## Validation evidence

CLI contract (markdown), not OpenAPI. Spectral lint is N/A — no `openapi.yaml` to lint; no Spectral dependency added.

Structural checks on the written files:

- `docs/features/kamal-deploy/contracts/cli.md` present; `openapi.yaml` absent; `events.md` absent.
- Owner-facing check command is `uv run pytest`; later command is `bundle exec kamal deploy`.
- Exit 0 / 1 match the two Run-configuration-check `alt` branches.
- Required glossary fields from AC-04 all appear in the recipe table.
- Locked interview values appear once each: host `138.201.118.229`, Public site names `image.bondev.eu` and `www.image.bondev.eu`, image `shved270189/image_compressor`, registry username `shved270189`, service `image_compressor`, arch `amd64`, port `8000`, path `/api/health`.
- Examples use a throwaway password `test-registry-password`, not a production secret.

Reproduce from the repository root:

```sh
test -f docs/features/kamal-deploy/contracts/cli.md
test ! -f docs/features/kamal-deploy/contracts/openapi.yaml
test ! -f docs/features/kamal-deploy/contracts/events.md
rg -n "uv run pytest|bundle exec kamal deploy|image_compressor|138.201.118.229" docs/features/kamal-deploy/contracts/cli.md
```

Full pytest, Ruff, ESLint, Kamal, and container runtime verification are not claimed by this documentation stage.

## Handoff

Review [cli.md](./cli.md) and this report. Proposed commit: `api: kamal-deploy contract`.

Next on route `quick`: auto-skip `screens` (no UI surface in `target_surfaces: [cli]`). Forward is `/sdd:tasks kamal-deploy`.
