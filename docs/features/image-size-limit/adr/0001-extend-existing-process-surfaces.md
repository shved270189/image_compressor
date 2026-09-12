---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-12"
feature_size: S
ticket: "N/A"
---

# 0001 — Extend existing process surfaces

- **Status:** Accepted
- **Date:** 2026-09-12
- **Deciders:** Project owner and Tech Lead

## Context

The foundation already provides a browser SPA and a FastAPI application. All five image-size-limit user stories occur on SCR-01. Trusted validation and extra-shrink execute on the server. Downstream stages need an explicit target-surface contract.

## Decision drivers

- Implement the agreed local form and server-validated bound.
- Reuse the existing application unit, module boundaries and UI conventions.
- Avoid a second screen, service or client.

## Considered options

1. **Extend the existing web-frontend and backend-service together.** Owner-approved surface set inherited from the foundation and the shipped resize/convert form.
2. **Encode only in the browser.** Would skip the Application for this increment. Rejected because HEIC, decoded-pixel caps and Pillow encoding already live in `backend/images.py`.

## Decision outcome

**Chosen:** Option 1. Declare `target_surfaces` as `[backend-service, web-frontend]`. Draw Browser UI and Application as logical C4 containers inside the system boundary. Reuse the React SPA, local state, native controls and existing FastAPI application. Keep HTTP validation in `backend/main.py` and extra-shrink in `backend/images.py`.

## Consequences

**Positive**
- Downstream stages receive an unambiguous surface set.
- The feature reuses the runnable shipped form and process endpoint.

**Negative**
- Browser state and server processing must stay coordinated for miss versus met-limit outcomes.

**Neutral**
- Two logical C4 containers still ship as one application image plus the user's browser. This record captures a downstream contract, not a reconsideration of the foundation stack.

## Links

- [Spec](../spec.md), US-01–US-05
- [SAD](../sad.md) §4 and §5
- [Foundation ADR 0002](../../../adr/0002-single-service-and-kamal.md)
- [ADR 0002](./0002-signal-size-limit-miss-with-headers.md)
