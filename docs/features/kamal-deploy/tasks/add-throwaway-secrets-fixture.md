---
id: T3
title: "Add a throwaway Secrets file fixture"
layer: "tests"
deps: ["T1"]
blocks: ["T4"]
acs: ["AC-03"]
files_hint: ["tests/fixtures/kamal/secrets"]
owner: "Tech Lead"
estimate: "S"
context_budget: "S"
status: "todo"
---

# T3 — Add a throwaway Secrets file fixture

## Place in the sequence

- **Blocked by:** T1 — Ignore the Secrets file in git · **Blocks:** T4 — Implement the offline Configuration check success path · **Wave:** 2, after T1 so a real `.kamal/secrets` cannot be committed by mistake.
- **Lane:** own lane (`tests/fixtures/kamal/secrets`). This is the throwaway fixture, not the owner's Secrets file.

## Why (user story)

> **As a** Project owner
> **I want** to run the Configuration check on my machine
> **So that** I know the recipe is readable and complete without contacting the production host or the container registry.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

This task supplies the throwaway registry-password fixture the success path of the Configuration check reads.

## Inlined context

> No new CI job. The existing pytest suite may cover the Configuration check with a throwaway secrets fixture that is not production secrets.
>
> — `sad.md §2, Organisational, abridged` · full text: [sad.md](../sad.md)

> Secrets file: `.kamal/secrets` (gitignored). Tests use a throwaway fixture that is not production secrets. Yes for success; missing password is a named failure.
>
> — `contracts/cli.md, configurationCheck inputs, abridged` · full text: [cli.md](../contracts/cli.md)

> Placeholder secret only. Throwaway Secrets file fixture (not production secrets, not committed as `.kamal/secrets`): `KAMAL_REGISTRY_PASSWORD=test-registry-password`. The environment-variable **name** may appear in `config/deploy.yml`; the value above must not.
>
> — `contracts/cli.md, Examples, abridged` · full text: [cli.md](../contracts/cli.md)

> **Hard rule:** Secret leakage: 0 secret values in committed files; environment-variable names are allowed. The throwaway fixture is not production secrets.
>
> — `spec.md §6 and §7, Secret leakage / KPI, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. The fixture is an input to `configurationCheck`, not a command.

## Acceptance criteria

### AC-03 — happy

> **Given** Deploy configuration is complete and the Secrets file is present with the required registry password,
> **When** the Project owner runs the Configuration check,
> **Then** the check reports success and does not contact the production host or the container registry.
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `tests/fixtures/kamal/secrets` with `KAMAL_REGISTRY_PASSWORD=test-registry-password` and nothing else
- [ ] Do not write this content to `.kamal/secrets`
- [ ] Do not use a production registry password

## Edge cases

| Case | Behaviour |
|---|---|
| Fixture uses a real registry password | Forbidden — use only `test-registry-password` |
| Fixture is placed at `.kamal/secrets` | Forbidden — that path is gitignored and is the owner's Secrets file |
| SSH private key in the fixture | Not required; do not add it |

## Definition of Done

- [ ] `tests/fixtures/kamal/secrets` exists and contains `KAMAL_REGISTRY_PASSWORD=test-registry-password`
- [ ] the fixture is not production secrets and is not `.kamal/secrets`
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
