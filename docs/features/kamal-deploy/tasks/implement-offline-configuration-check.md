---
id: T4
title: "Implement the offline Configuration check success path"
layer: "ports"
deps: ["T2", "T3"]
blocks: ["T5", "T6"]
acs: ["AC-01", "AC-03", "AC-08"]
files_hint: ["tests/test_kamal_deploy.py"]
owner: "Tech Lead"
estimate: "M"
context_budget: "M"
status: "todo"
---

# T4 — Implement the offline Configuration check success path

## Place in the sequence

- **Blocked by:** T2 — Record Deploy configuration with locked host facts, T3 — Add a throwaway Secrets file fixture · **Blocks:** T5 — Fail the Configuration check with named missing fields and secrets, T6 — Reject committed secrets and production-target mismatch · **Wave:** 3, after the recipe and fixture exist.
- **Lane:** shares `tests/test_kamal_deploy.py` with T5 and T6 — serialized. This task owns the success path only.

## Why (user story)

> **As a** Project owner
> **I want** to run the Configuration check on my machine
> **So that** I know the recipe is readable and complete without contacting the production host or the container registry.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

This task is the owner-facing command: an offline pytest module that reports success when the recipe and throwaway fixture are complete.

## Inlined context

> **Chosen:** The Configuration check is an offline pytest module (planned path `tests/test_kamal_deploy.py`). The Project owner runs it with `uv run pytest`. README documents `bundle exec kamal deploy` only as the later publish command, not as the check.
>
> — `adr/0002-prove-recipe-with-offline-pytest-check.md, Decision outcome, verbatim` · full text: [adr/0002-prove-recipe-with-offline-pytest-check.md](../adr/0002-prove-recipe-with-offline-pytest-check.md)

> **Chosen:** Declare `target_surfaces: [cli]`. Draw one C4 container for the Configuration check. Do not declare `web-frontend` or `backend-service` for this increment.
>
> — `adr/0001-declare-cli-surface-for-configuration-check.md, Decision outcome, abridged` · full text: [adr/0001-declare-cli-surface-for-configuration-check.md](../adr/0001-declare-cli-surface-for-configuration-check.md)

> Rel(project_owner, check, "Runs the Configuration check", "uv run pytest"). The check reads local files only; it does not authenticate to the host or the registry.
>
> — `sad.md §5, C4 Container, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Host and registry contact during check: 0 connections to the production host and 0 connections to the container registry. Configuration check runtime ≤ 30 s. Must not invoke Kamal commands that can open those sockets (`bundle exec kamal config`, `bundle exec kamal deploy`, `bundle exec kamal setup`, registry login). No new CI job and no extra mise task.
>
> — `spec.md §6 NFR` and `sad.md §4 choice 3` and `contracts/cli.md, Network, abridged` · full text: [spec.md](../spec.md)

> A green Configuration check treated as proof that DNS, certificates or image pull will work — Check must not claim live readiness; spec accepts that first live publish may still fail.
>
> — `sad.md §11, green-check residual, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `configurationCheck` → invocation `uv run pytest` · module `tests/test_kamal_deploy.py` · flags: none owned by this feature (no mise wrapper).
- Success (exit 0): every required non-secret field is present with the locked value; the required registry password is present in the throwaway fixture; zero connections to `138.201.118.229` or the container registry.
- Inputs: `config/deploy.yml`; throwaway fixture (not production secrets); application image facts port `8000` and path `/api/health`.
- Mutating: No. Network: Forbidden.

— `contracts/cli.md, command configurationCheck, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-01 — happy

> **Given** the Project owner knows the production host address, both Public site names, image name and registry username,
> **When** they record Deploy configuration,
> **Then** the recipe names those facts, enables HTTPS for both Public site names, sets service name to `image_compressor`, sets image architecture to amd64, uses the application's existing listening port and existing health-check path, and the Project owner can see those values in the repository.
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-03 — happy

> **Given** Deploy configuration is complete and the Secrets file is present with the required registry password,
> **When** the Project owner runs the Configuration check,
> **Then** the check reports success and does not contact the production host or the container registry.
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — domain invariant

> **Given** the already-built application image uses its established listening port and health-check path,
> **When** Deploy configuration is recorded,
> **Then** the recipe's reverse-proxy target port and health-check path match that image; a different port or path violates the production-target invariant.
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `tests/test_kamal_deploy.py` with `test_configuration_check_succeeds_offline` that reads `config/deploy.yml` and `tests/fixtures/kamal/secrets`
- [ ] Assert every locked recipe field from the contract table, including `proxy.app_port: 8000` and `proxy.healthcheck.path: /api/health`
- [ ] Assert the throwaway fixture supplies the registry password
- [ ] Do not call `bundle exec kamal` or open sockets to `138.201.118.229` or the registry
- [ ] Do not add a CI job or a mise wrapper
- [ ] Do not claim the check proves live publish, DNS, or certificates

## Edge cases

| Case | Behaviour |
|---|---|
| Complete recipe and throwaway fixture | pytest exit 0; success reported |
| Check runtime | wall clock of `uv run pytest` on this module ≤ 30 s |
| Kamal-native `kamal config` as the check | Forbidden — ADR 0002 chose offline pytest |
| Success message claims the site is live | Forbidden — residual risk accepted |

## Definition of Done

- [ ] `uv run pytest tests/test_kamal_deploy.py::test_configuration_check_succeeds_offline` passes
- [ ] the test does not invoke Kamal and does not contact the host or registry
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
