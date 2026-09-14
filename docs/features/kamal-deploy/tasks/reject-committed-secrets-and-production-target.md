---
id: T6
title: "Reject committed secrets and production-target mismatch"
layer: "tests"
deps: ["T1", "T4"]
blocks: []
acs: ["AC-02", "AC-08"]
files_hint: ["tests/test_kamal_deploy.py"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
---

# T6 — Reject committed secrets and production-target mismatch

## Place in the sequence

- **Blocked by:** T1 — Ignore the Secrets file in git, T4 — Implement the offline Configuration check success path · **Blocks:** none · **Wave:** 4, after gitignore and the check module exist.
- **Lane:** shares `tests/test_kamal_deploy.py` with T4 and T5 — serialized.

## Why (user story)

> **As a** Project owner
> **I want** registry password, SSH private key and other secret values kept only in the Secrets file, while the committed recipe may contain environment-variable names
> **So that** the committed repository never contains those values.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task asserts the committed tree has no secret values and that a wrong port or health-check path is not accepted as the production target.

## Inlined context

> alt required facts present, secrets stay local, port and path match the application image → write non-secret recipe fields; write secret values to Secrets file (gitignored). else secret value in committed recipe → reject, secret values belong only in Secrets file. else port or health-check path does not match the application image → reject, production-target invariant violated.
>
> — `sad.md §6, Record deploy configuration, abridged` · full text: [sad.md](../sad.md)

> Sequence branch `secret value in committed recipe` → `kamal_deploy.secret_in_committed_tree` — pytest failure; `.kamal/secrets` is gitignored. Sequence branch `port or health-check path does not match` → `kamal_deploy.production_target_invariant_violated` — pytest failure; not success.
>
> — `contracts/cli.md, Record Deploy configuration, abridged` · full text: [cli.md](../contracts/cli.md)

> listening port `proxy.app_port` must match the application image: `8000`. health-check path `proxy.healthcheck.path` must match: `/api/health`.
>
> — `contracts/cli.md, Recipe fields, abridged` · full text: [cli.md](../contracts/cli.md)

> **Hard rule:** Secret leakage: 0 secret values in committed files; environment-variable names are allowed. The throwaway fixture uses `test-registry-password` and is not production secrets.
>
> — `spec.md §6, Secret leakage` and `contracts/cli.md, Examples, abridged` · full text: [spec.md](../spec.md)

> Foundation ADR 0002: the future `config/deploy.yml` sets `proxy.app_port: 8000` and `proxy.healthcheck.path: /api/health`.
>
> — `docs/adr/0002-single-service-and-kamal.md, Decision, abridged` · full text: [ADR 0002](../../../adr/0002-single-service-and-kamal.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `kamal_deploy.secret_in_committed_tree` — a secret value is present in git; pytest failure; user-visible text uses glossary terms.
- `kamal_deploy.production_target_invariant_violated` — reverse-proxy target port is not 8000 or health-check path is not `/api/health`; not success.
- Environment-variable names in the recipe are allowed. SSH private key is not required in the Secrets file.

— `contracts/cli.md, Error codes and Record Deploy configuration, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-02 — domain invariant

> **Given** Deploy configuration is recorded,
> **When** anyone inspects the committed repository,
> **Then** no registry password value, SSH private key or other secret value is present; environment-variable names may appear; secret values exist only in the Project owner's Secrets file, which git ignores.
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — domain invariant

> **Given** the already-built application image uses its established listening port and health-check path,
> **When** Deploy configuration is recorded,
> **Then** the recipe's reverse-proxy target port and health-check path match that image; a different port or path violates the production-target invariant.
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add a test in `tests/test_kamal_deploy.py` that `.kamal/secrets` is gitignored and the committed tree has no password values or private-key material
- [ ] Allow the throwaway fixture value `test-registry-password` and environment-variable names in `config/deploy.yml`
- [ ] Assert committed `proxy.app_port` is `8000` and `proxy.healthcheck.path` is `/api/health`
- [ ] Add a case that a temp recipe with a different port or path is `kamal_deploy.production_target_invariant_violated` and not success

## Edge cases

| Case | Behaviour |
|---|---|
| Environment-variable name in `config/deploy.yml` | Allowed |
| Throwaway fixture `test-registry-password` under `tests/fixtures/` | Allowed; not production secrets |
| Production password or SSH private key in git | Fail: `secret_in_committed_tree` |
| `proxy.app_port: 3000` or health path `/` | Fail: production-target invariant violated |

## Definition of Done

- [ ] `uv run pytest tests/test_kamal_deploy.py` includes passing assertions that `.kamal/secrets` is gitignored, committed files have no secret values, and the recipe port/path match 8000 and `/api/health`
- [ ] a mismatched port or path is not accepted as the production target
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
