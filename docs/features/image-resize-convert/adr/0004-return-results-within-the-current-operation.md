---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-06"
feature_size: M
ticket: "N/A"
---

# 0004 — Return results within the current operation

- **Status:** Accepted
- **Date:** 2026-09-06
- **Deciders:** Project owner and Tech Lead

## Context

The owner replaced manual result inspection and download with one automatic browser download followed by a clean form. The foundation already requires request-scoped UploadFile storage, in-memory encoded output and no result repository. Form reset and download handoff have different resource-release boundaries.

## Decision drivers

- Initiate exactly one download for the current operation and then reset the form.
- Retain current input on recoverable failure and suppress stale or duplicate completions.
- Release server and browser resources without interrupting the initiated download.

## Considered options

1. Return the complete binary result in the current processing response, then perform a browser Blob-URL download and separate handoff cleanup. This is the owner-approved lifecycle.

## Decision outcome

Use one processing request with a complete binary response and no result ID, lookup or second retrieval request. Lock file selection, parameters and repeated submission while it is pending. On complete success, verify currentness and consume the operation once, initiate a native download with the matching filename extension, and reset the form. A separate handoff owner releases the result Blob URL when safe; resetting form state must not revoke it prematurely. Retain current input after recoverable errors. Invalidate page work on teardown and release server resources on success, failure and interruption, allowing already-running native decoding to finish before its resources are released.

## Consequences

**Positive.** There is no persistent result to leak or restore, and successive conversions are independent.

**Negative.** The complete encoded result exists temporarily in server response memory and browser memory. Safe Blob-URL release and mobile download behavior require browser evidence. Browser cancellation does not promise immediate native-decoder termination.

**Neutral.** No alternate manual download, result page or lookup design is listed because the accepted spec excludes them. The owner chose one cohesive lifecycle ADR rather than separate server and browser records. This decision does not claim a disk-save confirmation event or prescribe an unverified cleanup delay.

**ADR gate.** Cross-module operation contract and a delivery/lifecycle boundary costly to reverse after implementation. Alternatives already excluded by the spec are not presented as genuine options.

## Links

- [Spec](../spec.md), AC-03 and AC-13–AC-16, UX amendment.
- [SAD](../sad.md), §4, §6, §8 and §11.
- [ADR 0001](./0001-extend-web-frontend-and-backend-service.md).
- [Foundation ADR 0003](../../../adr/0003-transient-image-processing.md).
- [Object-URL lifecycle](https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static).
- [Browser downloading algorithm](https://html.spec.whatwg.org/multipage/links.html#downloading-resources).
