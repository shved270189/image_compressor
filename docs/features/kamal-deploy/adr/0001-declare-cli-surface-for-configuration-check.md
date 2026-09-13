---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-13"
feature_size: S
ticket: "N/A"
---

# 0001 — Declare a CLI surface for the Configuration check

- **Status:** Accepted
- **Date:** 2026-09-13
- **Deciders:** Project owner and Tech Lead

## Context

kamal-deploy gives the Project owner a committed publish recipe and a local Configuration check. The Image owner form and the FastAPI processing path must stay unchanged. Downstream stages need an explicit target-surface contract so they do not invent an HTTP API or UI layer.

## Decision drivers

- Spec goals: complete Deploy configuration and a local Configuration check; no live publish in this step.
- Spec AC-06 and AC-07: the compression form gains no publish action and processing behaviour stays the same.
- No new application HTTP interface. Foundation ADR 0002 already chose one application service.

## Considered options

1. **CLI only** — Configuration check is the sole surface this feature owns.
2. **CLI and backend-service** — also declare the existing FastAPI application as a surface of this feature.

## Decision outcome

**Chosen:** Option 1. Declare `target_surfaces: [cli]`. Draw one C4 container for the Configuration check. Do not declare `web-frontend` or `backend-service` for this increment. The existing application image remains the later production target of the recipe, not a surface this feature introduces.

## Consequences

**Positive**
- `api` authors a command contract (`contracts/cli.md`), not OpenAPI for endpoints that do not change.
- `screens` is N/A. No UI task layer. Form and processing stay out of scope.

**Negative**
- The SAD does not treat the existing FastAPI service as a feature-owned container, so readers must follow foundation ADR 0002 for the production target.

**Neutral**
- Adding a publish control to the form later is a new feature and a new surface, not a revision of this ADR.

## Links

- Spec: [spec.md](../spec.md) US-03, US-06, AC-06, AC-07
- SAD: [sad.md](../sad.md) §4 and §5
- Related: [0002-prove-recipe-with-offline-pytest-check.md](./0002-prove-recipe-with-offline-pytest-check.md)
- Foundation: [ADR 0002](../../../adr/0002-single-service-and-kamal.md)
