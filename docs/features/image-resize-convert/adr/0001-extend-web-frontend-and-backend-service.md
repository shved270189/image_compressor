---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-06"
feature_size: M
ticket: "N/A"
---

# 0001 — Extend the web frontend and backend service

- **Status:** Accepted
- **Date:** 2026-09-06
- **Deciders:** Project owner and Tech Lead

## Context

The foundation already provides a browser SPA and a FastAPI application. All five feature user stories occur on SCR-01, while trusted validation and transformation execute on the server. Downstream stages need an explicit target-surface contract.

## Decision drivers

- Implement the agreed local form and server-validated processing.
- Reuse the existing application unit, module boundaries and UI conventions.

## Considered options

1. Extend the existing web-frontend and backend-service together. This is the owner-approved surface set inherited from the foundation; no new competing platform was proposed.

## Decision outcome

Declare target_surfaces as [web-frontend, backend-service]. Draw Browser UI and Application as logical C4 containers inside the system boundary. Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in backend/main.py and image functions in backend/images.py.

## Consequences

**Positive.** The feature reuses the runnable foundation and gives downstream stages an unambiguous surface set.

**Negative.** The end-to-end feature must coordinate browser state with the server's processing and response lifecycle.

**Neutral.** Two logical C4 containers still ship as one application image plus the user's browser. This record captures a downstream contract, not a reconsideration of the foundation stack.

**ADR gate.** Surface gate: owner-confirmed multi-surface contract. No strawman alternative to the inherited foundation is introduced.

## Links

- [Spec](../spec.md), US-01–US-05.
- [SAD](../sad.md), §4 and §5.
- [Foundation ADR 0002](../../../adr/0002-single-service-and-kamal.md).
- [ADR 0004](./0004-return-results-within-the-current-operation.md), shared operation lifecycle.
