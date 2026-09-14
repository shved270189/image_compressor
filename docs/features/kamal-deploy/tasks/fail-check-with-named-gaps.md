---
id: T5
title: "Fail the Configuration check with named missing fields and secrets"
layer: "tests"
deps: ["T4"]
blocks: []
acs: ["AC-04"]
files_hint: ["tests/test_kamal_deploy.py"]
owner: "Tech Lead"
estimate: "M"
context_budget: "S"
status: "todo"
---

# T5 — Fail the Configuration check with named missing fields and secrets

## Place in the sequence

- **Blocked by:** T4 — Implement the offline Configuration check success path · **Blocks:** none · **Wave:** 4, after the success path exists.
- **Lane:** shares `tests/test_kamal_deploy.py` with T4 and T6 — serialized. Do not change the success-path assertions.

## Why (user story)

> **As a** Project owner
> **I want** the Configuration check to fail and name each missing required field or secret in glossary terms
> **So that** I never treat an incomplete recipe as ready.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task adds the missing-field and missing-secret failure cases of the Configuration check.

## Inlined context

> S->>D: read required non-secret recipe fields. S->>D: read required registry password from Secrets file. Note over S,X: does not contact production host or container registry. alt recipe complete and registry password present → success. else required field or secret missing → fail, name each missing field or secret in glossary terms.
>
> — `sad.md §6, Run configuration check, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Missing required recipe field or secret fails the check and names each gap in glossary terms. Several gaps in one run are listed together. It does not report success.
>
> — `sad.md §8, Error handling` and `contracts/cli.md, Failure, abridged` · full text: [sad.md](../sad.md)

> User-visible failure text uses glossary terms, not the `kamal_deploy.*` tokens. Glossary terms: Configuration check, Deploy configuration, Public site name, Secrets file, host address, image name, registry username, service name, image architecture, listening port, health-check path, registry password.
>
> — `contracts/cli.md, Failure and Error codes, abridged` · full text: [cli.md](../contracts/cli.md)

> Not required this step (do not fail the check for their absence): SSH user, SSH private key in the Secrets file, DNS pointing, certificates, `kamal setup`, a second environment, accessories.
>
> — `contracts/cli.md, Recipe fields, abridged` · full text: [cli.md](../contracts/cli.md)

> Configuration check missing-secrets failure — target: 1 failing run in that suite that names the gap when the Secrets file is absent.
>
> — `spec.md §7, KPI, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `configurationCheck` failure (exit 1): pytest reports failure. The failure names **each** missing required field or secret in glossary terms. Not success.
- Required gaps: host address, either Public site name, image name, registry username, HTTPS enabled, service name `image_compressor`, image architecture amd64, listening port, health-check path, or the required registry password from the Secrets file.
- Example assertion: `Configuration check failed: missing registry password from Secrets file`. Example multi-gap: `missing host address, missing Public site name`.
- Other pytest exits 2–5 are not success and not a substitute for a named missing-field failure.

— `contracts/cli.md, configurationCheck Failure / Examples / Error codes, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-04 — error

> **Given** a required recipe field is missing (host address, either Public site name, image name, registry username, HTTPS enabled, service name `image_compressor`, image architecture amd64, listening port, or health-check path) or the required registry password is missing from the Secrets file,
> **When** the Project owner runs the Configuration check,
> **Then** the check fails and names each missing required field or secret in glossary terms; it does not report success.
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `test_configuration_check_names_missing_secrets` in `tests/test_kamal_deploy.py` that omits the throwaway fixture and asserts a glossary-term failure for registry password / Secrets file
- [ ] Add `test_configuration_check_names_missing_fields` that omits required recipe fields on a temp copy and names each gap in glossary terms
- [ ] Cover both Public site names: either missing is a named `Public site name` gap
- [ ] Do not fail for absent SSH user, SSH private key, DNS, or certificates
- [ ] Do not contact the host or registry; do not invoke Kamal

## Edge cases

| Case | Behaviour |
|---|---|
| Secrets file absent | Fail; name registry password and Secrets file; not success |
| Either Public site name missing | Fail; name Public site name |
| Several fields missing in one run | List each gap together |
| SSH user unset | Not a check failure (spec §8 open question) |
| pytest exits 2–5 | Not success; not a named-gap failure |

## Definition of Done

- [ ] `uv run pytest tests/test_kamal_deploy.py::test_configuration_check_names_missing_secrets tests/test_kamal_deploy.py::test_configuration_check_names_missing_fields` — the cases fail the check (as assertions of named gaps) and do not report Configuration check success
- [ ] failure text uses glossary terms, not only `kamal_deploy.*` tokens
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
