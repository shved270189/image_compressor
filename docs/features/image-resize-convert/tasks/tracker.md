# Tracker — image-resize-convert

> States: `todo` · `in_progress` · `blocked` · `review` · `done`. `implement` updates status after verified task completion.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | [Bound multipart parsing](./bound-multipart-parsing.md) | ports | Tech Lead | 6h | — | done |
| T2 | [Decode supported static images](./decode-supported-static-images.md) | domain | Tech Lead | 6h | — | done |
| T3 | [Classify HEIF presentation timelines](./classify-heif-presentation-timelines.md) | domain | Tech Lead | 6h | T2 | done |
| T4 | [Handle fragmented HEIF timelines](./handle-fragmented-heif-timelines.md) | domain | Tech Lead | 6h | T3 | done |
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

## Implementation evidence

- T1: RED missing `parse_image_request`; GREEN 41 parser/smoke tests. Frontend build/typecheck, Ruff and ESLint passed; application image build and live-container smoke passed. Mixed-case media type regression added after independent review. Parser diagnostic confidentiality remains assigned to T8/T12 before route exposure.
- T2: RED decoding absent; GREEN 61 tests. Actual PNG pixel equality/overflow and post-decode limit failures covered; explicit Pillow core cleanup regression passed. Build/typecheck, Ruff, ESLint and Linux application-image primary HEIC decode passed. HEIF presentation rejection remains T3/T4 before route exposure.
- T3: RED timeline classifier absent; GREEN 83 tests, build/typecheck, Ruff and ESLint passed. Linux real static/sequence controls passed. Independent review added reverse-edit and repeated-edit end-bound regressions. Fragmented timing remains T4.
- T4: GOOD RED fragmented sequence accepted; GREEN 91 tests, build/typecheck, Ruff and ESLint. Independent FFmpeg HEVC-track decoding and Pillow primary decoding passed. Linux application image distinguishes sequence/gallery and decodes gallery primary. Production handles duration defaults, signed composition and fragment continuation; no diagnostic fallback. T3 follow-up commits fixed reordered-end and fractional-rate regressions.
