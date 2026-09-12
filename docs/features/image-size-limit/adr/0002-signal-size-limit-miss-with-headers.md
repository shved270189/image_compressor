---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-12"
feature_size: S
ticket: "N/A"
---

# 0002 — Signal size-limit miss with headers

- **Status:** Accepted
- **Date:** 2026-09-12
- **Deciders:** Project owner and Tech Lead

## Context

`POST /api/v1/images/process` currently returns only the binary Результат and a Content-Disposition filename. A miss still downloads that file, keeps the form, and must show the actual size plus that Ліміт ваги was exceeded. A met or omitted bound must keep today's automatic download and clean form. The Browser UI and Application both need a shared miss contract.

## Decision drivers

- Miss is not a client error: AC-07 requires a file.
- Keep the existing binary attachment handoff used by the smoke test and browser download.
- Server owns Ліміт ваги arithmetic (1 Mb = 1,048,576 bytes; 1 Kb = 1,024 bytes) so the UI does not become a second source of truth.

## Considered options

1. **Infer miss from `blob.size`.** Keep the binary body unchanged. The Browser UI converts the entered bound and compares it with the received Blob. Rejected: duplicates AC-12 arithmetic on both sides.
2. **Keep the binary body and add miss headers.** When a bound was supplied, send `X-Result-Bytes` (whole encoded bytes) and `X-Size-Limit-Met` (`true` or `false`). Omit both when the bound is omitted.
3. **Wrap the file in JSON or multipart metadata.** Rejected for this S increment: it would replace `ImageResponse`, break the existing binary smoke path, and add a parsing layer the spec does not need.

## Decision outcome

**Chosen:** Option 2. The successful response remains the complete binary Результат. Miss versus met-limit is carried in headers so the Browser UI can start one download and then reset or keep the form. Optional request fields `size_limit` and `size_unit` carry the bound; the Application converts them to whole bytes.

## Consequences

**Positive**
- Existing binary download handoff stays intact.
- Bound arithmetic lives in one place.

**Negative**
- Custom headers are a new response contract. A future reverse proxy might strip them.

**Neutral**
- If headers are missing, the Browser UI may compare `blob.size` as a fallback. Same-origin requests today do not need CORS expose-headers. Switching to a JSON envelope later would be a breaking contract change.

## Links

- [Spec](../spec.md), AC-06, AC-07, AC-12
- [SAD](../sad.md) §4 and §8
- [ADR 0001](./0001-extend-existing-process-surfaces.md)
