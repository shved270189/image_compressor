# Tracker — image-resize-convert

> States: `todo` · `in_progress` · `blocked` · `review` · `done`. `implement` updates status after verified task completion.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | [Bound multipart parsing](./bound-multipart-parsing.md) | ports | Tech Lead | 6h | — | todo |
| T2 | [Decode supported static images](./decode-supported-static-images.md) | domain | Tech Lead | 6h | — | todo |
| T3 | [Classify HEIF presentation timelines](./classify-heif-presentation-timelines.md) | domain | Tech Lead | 6h | T2 | todo |
| T4 | [Handle fragmented HEIF timelines](./handle-fragmented-heif-timelines.md) | domain | Tech Lead | 6h | T3 | todo |
| T5 | [Resize and normalize output](./resize-and-normalize-output.md) | domain | Tech Lead | 6h | T4 | todo |
| T6 | [Preserve compatible color profiles](./preserve-compatible-color-profiles.md) | domain | Tech Lead | 8h | T5 | todo |
| T7 | [Convert HDR to ordinary SDR output](./convert-hdr-to-ordinary-sdr-output.md) | domain | Tech Lead | 6h | T6 | todo |
| T8 | [Serve request-scoped image results](./serve-request-scoped-image-results.md) | ports | Tech Lead | 8h | T1, T7 | todo |
| T9 | [Build selection and local preview](./build-selection-and-local-preview.md) | ui | Tech Lead | 6h | — | todo |
| T10 | [Submit and download the current result](./submit-and-download-the-current-result.md) | ui | Tech Lead | 6h | T8, T9 | todo |
| T11 | [Verify browser acceptance](./verify-browser-acceptance.md) | tests | Tech Lead | 6h | T10 | todo |
| T12 | [Verify security and container behavior](./verify-security-and-container-behavior.md) | tests | Tech Lead | 6h | T8 | todo |
| T13 | [Document the completed workflow](./document-the-completed-workflow.md) | docs | Tech Lead | 2h | T11, T12 | todo |

**Total:** 13 tasks, 78 hours, 9.75 person-days at 8 hours/day. Estimates exclude waiting for device access and owner/security sign-off.

Tech Lead owns delivery; Security Lead accepts T12 security review and Project owner accepts T11 readable contrast. Tests and review are part of each estimate.
