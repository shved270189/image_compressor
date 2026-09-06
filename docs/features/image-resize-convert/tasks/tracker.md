# Tracker — image-resize-convert

> States: `todo` · `in_progress` · `blocked` · `review` · `done`. `implement` updates status after verified task completion.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | [Bound multipart parsing](./bound-multipart-parsing.md) | ports | Tech Lead | 6h | — | done |
| T2 | [Decode supported static images](./decode-supported-static-images.md) | domain | Tech Lead | 6h | — | done |
| T3 | [Classify HEIF presentation timelines](./classify-heif-presentation-timelines.md) | domain | Tech Lead | 6h | T2 | done |
| T4 | [Handle fragmented HEIF timelines](./handle-fragmented-heif-timelines.md) | domain | Tech Lead | 6h | T3 | done |
| T5 | [Resize and normalize output](./resize-and-normalize-output.md) | domain | Tech Lead | 6h | T4 | done |
| T6 | [Preserve compatible color profiles](./preserve-compatible-color-profiles.md) | domain | Tech Lead | 8h | T5 | done |
| T7 | [Convert HDR to ordinary SDR output](./convert-hdr-to-ordinary-sdr-output.md) | domain | Tech Lead | 6h | T6 | done |
| T8 | [Serve request-scoped image results](./serve-request-scoped-image-results.md) | ports | Tech Lead | 8h | T1, T7 | done |
| T9 | [Build selection and local preview](./build-selection-and-local-preview.md) | ui | Tech Lead | 6h | — | done |
| T10 | [Submit and download the current result](./submit-and-download-the-current-result.md) | ui | Tech Lead | 6h | T8, T9 | done |
| T11 | [Verify browser acceptance](./verify-browser-acceptance.md) | tests | Tech Lead | 6h | T10 | review |
| T12 | [Verify security and container behavior](./verify-security-and-container-behavior.md) | tests | Tech Lead | 6h | T8 | done |
| T13 | [Document the completed workflow](./document-the-completed-workflow.md) | docs | Tech Lead | 2h | T11, T12 | review |

**Total:** 13 tasks, 78 hours, 9.75 person-days at 8 hours/day. Estimates exclude waiting for device access and owner/security sign-off.

Tech Lead owns delivery; Security Lead accepts T12 security review and Project owner accepts T11 readable contrast. Tests and review are part of each estimate.

## Implementation evidence

Chronological log: later entries supersede earlier pending/blocker statements.
The task table above records current status.

- T1: RED missing `parse_image_request`; GREEN 41 parser/smoke tests. Frontend build/typecheck, Ruff and ESLint passed; application image build and live-container smoke passed. Mixed-case media type regression added after independent review. Parser diagnostic confidentiality remains assigned to T8/T12 before route exposure.
- T2: RED decoding absent; GREEN 61 tests. Actual PNG pixel equality/overflow and post-decode limit failures covered; explicit Pillow core cleanup regression passed. Build/typecheck, Ruff, ESLint and Linux application-image primary HEIC decode passed. HEIF presentation rejection remains T3/T4 before route exposure.
- T3: RED timeline classifier absent; GREEN 83 tests, build/typecheck, Ruff and ESLint passed. Linux real static/sequence controls passed. Independent review added reverse-edit and repeated-edit end-bound regressions. Fragmented timing remains T4.
- T4: GOOD RED fragmented sequence accepted; GREEN 91 tests, build/typecheck, Ruff and ESLint. Independent FFmpeg HEVC-track decoding and Pillow primary decoding passed. Linux application image distinguishes sequence/gallery and decodes gallery primary. Production handles duration defaults, signed composition and fragment continuation; no diagnostic fallback. T3 follow-up commits fixed reordered-end and fractional-rate regressions.
- T5: GOOD RED transformation absent; GREEN 120 tests, build/typecheck, Ruff and ESLint. All twelve format pairs, exact rounding/bounds, alpha and metadata/orientation checks passed. Linux HEIC resize/PNG encode passed. Color-model conversion remains T6/T7.
- T6: GOOD RED lost PNG gamma; GREEN 136 host tests and 95 Linux image tests. Build/typecheck, Ruff and ESLint passed. Gray/CMYK nontrivial color anchors, P3, NCLX and PNG gamma tests pass with matching RGB ICC. Bundled LittleCMS exercised on both platforms.
- T7: GOOD RED missing HDR profile; GREEN 141 host tests and 100 Linux image tests. Build/typecheck, Ruff and ESLint passed. Real HLG and independent HLG/PQ neutral anchors verify ordinary 8-bit output, alpha and matching source-gamut profiles. No photographed PQ fixture is claimed.
- T8: implementation and regressions remain uncommitted because the acceptance gate is RED. The ordinary route, raw cancellation/socket ownership and safe encoder-failure/16-bit-gray regressions passed (168 tests before adding the contract-conflict cases); frontend build/typecheck, Ruff and ESLint passed. Two explicit AC-07 regressions now fail: valid 16,384x1 PNG to WebP and valid 65,501x1 PNG to JPEG return 500 instead of the promised successful result. These inputs satisfy the byte/pixel limits, while native output limits prevent encoding and AC-05 prohibits extra reduction. Owner decision required: explicit recoverable output-limit rejection, or permission to reduce to encoder bounds. Do not weaken these tests or mark T8 complete without reconciling the spec/contract. T9 remains todo (browser RED: file selection absent); T10–T13 remain pending. No full implementation/browser/security acceptance is claimed.
- T8 resumed: owner approved actionable 422 for output encoder dimension limits without extra reduction. Spec, contract and test plan reconciled. GREEN 174 host and 174 Linux container tests, including real HTTP format matrix, exact output bounds/retry, raw cancellation, socket interruption and cleared response bodies. Build/typecheck, Ruff and ESLint passed. Previous RED blocker is resolved; T8 committed.

- T9: browser RED missing file selection; GREEN Chrome selection, byte boundaries, preview ownership, replacement/reset, no upload before submission, responsive overflow and reduced motion checks. Build/typecheck, ESLint, Ruff and 174 host tests passed. Native text inputs with numeric input mode preserve arbitrarily large dimension strings without numeric coercion.

- T10: RED absent processing POST; GREEN complete download/reset/focus, single submission, safe structured errors, retained retry, full-body wait, interruption and stale completion suppression. Browser evidence in `_audit/implementation-download.md`. Build/typecheck, ESLint, Ruff and 180 host tests passed.

- T11: Chrome implemented-flow checks pass, including full-body interruption, stale work, actual pending-page closure, HEIC output formats, keyboard and both widths. Native Safari/Firefox complete downloads pass. Full native-engine matrices, real iPhone Safari and owner contrast review remain open; see `_audit/browser-acceptance.md`.
- T12: 180 host and 180 Linux tests plus live non-root container smoke pass. Independent review defects fixed in `08698b0`. Security Lead acceptance remains open; see `_audit/security-container-acceptance.md`.
- T13: README and architecture map prepared against actual implementation/evidence, explicitly documenting pending acceptance. Final acceptance depends on T11/T12; no completed browser/security sign-off is claimed.

- T11 owner update (2026-09-06): download/reset confirmed on iOS and desktop Safari/Firefox; owner accepted phone/desktop label, field and button readability. The stuck-processing report was explicitly withdrawn. Remaining native-engine failure/retry/interruption matrix stays in review; no regression fix was needed.

- T11 owner follow-up (2026-09-06): the same image was processed twice consecutively; both downloads and both form resets explicitly confirmed. Exact browser unspecified; remaining matrix and T11 review status unchanged.

- T11 owner reload check (2026-09-06): immediate reload after submission opens an empty form. Exact browser and in-flight timing unspecified; full interruption coverage is not inferred.

- T11 owner validation check (2026-09-06): width 0 rejected visibly; correcting to 100 produces a download. Local validation recovery confirmed; server-error recovery and remaining browser matrix are not inferred.

- T12 final: independent agent acting as Security Lead accepted the technical scope; 179 feature tests independently rerun, no confirmed blocking defects. T12/SAD do not require a human signature; prior unsupported signature wording corrected. T12 done.
- T11 final follow-up: Firefox 155.0 and WebKit 26.5 pass download, retry, ownership, interruption, closure, keyboard/reduced-motion and responsive checks. Native Safari real 422 correction/retry also passes with independently decoded output. Real iPhone network-failure/retry result pending; engine/native evidence distinguished in audit.
