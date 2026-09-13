---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-13"
feature_size: S
ticket: "N/A"
---

# 0002 — Prove the recipe with an offline pytest Configuration check

- **Status:** Accepted
- **Date:** 2026-09-13
- **Deciders:** Project owner and Tech Lead

## Context

The Configuration check must prove Deploy configuration is readable and complete without contacting the production host or the container registry. Spec allows the existing pytest suite to cover that check with a throwaway secrets fixture. Kamal can print resolved configuration, but that path may open network connections.

## Decision drivers

- Spec §6 NFR: 0 connections to the production host and 0 connections to the container registry while the check runs; wall clock ≤ 30 s; success only when 100% of required fields and the required registry password are present.
- Spec §3: no new CI job. Existing CI already runs `uv run pytest`.
- Spec §7 KPI: one passing suite run with a throwaway secrets fixture and one failing run that names the gap when the Secrets file is absent.

## Considered options

1. **Offline pytest** — a test in `tests/` reads `config/deploy.yml` and a throwaway Secrets file fixture; it does not invoke Kamal.
2. **Kamal config as the check** — `bundle exec kamal config` (or equivalent) is the owner-facing command; pytest only asserts exit 0.
3. **Separate mise task wrapping a YAML validator** — `mise run config-check` as a second entry point besides pytest.

## Decision outcome

**Chosen:** Option 1. The Configuration check is an offline pytest module (planned path `tests/test_kamal_deploy.py`). The Project owner runs it with `uv run pytest`. README documents `bundle exec kamal deploy` only as the later publish command, not as the check.

## Consequences

**Positive**
- Zero host and registry connections are guaranteed because the check never starts Kamal or opens sockets.
- Fits the existing CI job and the ≤ 30 s budget.
- Failures can name missing fields in glossary terms without parsing Kamal stderr.

**Negative**
- The check does not prove Kamal itself will accept the YAML. First live publish may still fail. Spec already accepts that residual.

**Neutral**
- No extra mise task. Switching to a Kamal-native check later is a small test change, not a data migration.

## Links

- Spec: [spec.md](../spec.md) US-03, US-04, AC-03, AC-04, §6 NFR
- SAD: [sad.md](../sad.md) §4, §6 and §10
- Related: [0001-declare-cli-surface-for-configuration-check.md](./0001-declare-cli-surface-for-configuration-check.md)
