---
status: Approved
owner: "Project owner"
reviewers: ["Implementing engineer", "Tech Lead", "Security Lead"]
updated_at: "2026-09-06"
feature_size: M
---

# Test plan — image-resize-convert

Verify one local image selection, optional Preview, bounded resize and format conversion, followed by exactly one complete download and a clean form. Size M and route standard come from `.size` and `.route`; the owner accepted the AC levels and strategy in the planning conversation. This approval covers the plan, not implementation or security acceptance.

Sources: [spec §5–6](./spec.md), [runtime flows and resource ownership](./sad.md), [UI flows](./ux-flows.md), [SCR-01 states](./screens.md), [transient data](./data-model.md), [processing contract](./contracts/openapi.yaml), and [implementation tasks](./tasks.json). The later feasibility closure in SAD §11 supersedes older open-gate notes in the data model, screen manifest and contract prose; feasibility probes do not prove the implemented feature.

## Levels

| Level | Scope | Strategy |
|---|---|---|
| unit | Pure geometry and rounding rules without I/O | Use exact expected dimensions and independently calculated boundary cases. |
| integration | Real image codecs, processing and request-scoped resource ownership | Use real fixtures and isolated temporary resources in a disposable application runtime; verify supported native behavior locally and in the application image. |
| contract | Real processing request/response boundary | Compare actual requests, binary responses, attachment headers and safe error envelopes with the agreed contract. |
| e2e-through-UI | Full browser journeys and SCR-01 state transitions | Drive the real form against the application, inspect network activity and complete downloaded files, and record manual browser/device evidence where automation is unavailable. |

No separate component or visual-regression suite is commissioned: no such harness exists, and the accepted design does not authorize new browser test infrastructure. Exercise all screen states through the UI instead. No separate API-only e2e suite duplicates these journeys. Test levels do not prescribe tools; implementation reuses the existing setup and browser probe capabilities.

## AC coverage

Each row is a named scenario with one agreed level. Parameterized cases listed in a row must all execute; they are not alternative coverage choices. Error cases are separated below from successful cases, including errors embedded in otherwise happy-path ACs.

| AC (spec.md §5) | Test name | Level | Expected outcome |
|---|---|---|---|
| AC-01 | Initial form enables only file selection | e2e-through-UI | No Preview or selected file; empty bounds and JPEG; parameter controls visible but disabled and processing disabled. |
| AC-01 | Eligible selection enables processing before preview completes | e2e-through-UI | Non-empty input up to the inclusive byte limit immediately enables parameters and processing with empty bounds and JPEG, without server content validation. |
| AC-02 | Preview stays local and displays the complete oriented original | e2e-through-UI | Available Preview appears above the form, uncropped and correctly oriented; selection and parameter edits upload nothing. |
| AC-02 | Unsupported native preview does not block conversion | e2e-through-UI | Native-unsupported input, including HEIC where applicable, has no Preview or broken placeholder and can still produce a download. |
| AC-03 | Every replacement resets selection state | e2e-through-UI | Valid, empty and oversized replacement files remove the old Preview, clear dimensions and reset JPEG. |
| AC-03 | Delayed selection and operation work cannot restore old state | e2e-through-UI | Old Preview callbacks and stale or duplicate completions cannot replace the current image, repopulate a reset form or download again. |
| AC-04 | Independent bounds match exact geometry examples | unit | For 2400 by 1200, width 1200 gives 1200 by 600; height 300 gives 600 by 300; both bounds give 600 by 300. |
| AC-04 | Encoded results honor independent bounds | integration | Real decoded outputs have each of the AC-04 expected sizes after orientation. |
| AC-05 | Largest fitting scale rounds halves up | unit | No extra reduction or enlargement; 1000 by 333 with width 500 gives 500 by 167; scaled dimensions use nearest-pixel rounding, halves up and minimum one. |
| AC-05 | Extreme aspect ratios and inactive bounds preserve geometry invariants | unit | Portrait, landscape, one-pixel, very thin and already-fitting cases remain inside all supplied bounds and original oriented dimensions. |
| AC-05 | Resizing retains the complete image | integration | Decoded output preserves marked image edges and proportions subject only to agreed pixel rounding and minimum; no crop, stretch or enlargement. |
| AC-06 | Ineffective bounds and same-format requests still normalize | integration | An 800 by 600 input with width 1600 stays 800 by 600; same-format input remains accepted and undergoes agreed orientation and metadata normalization. |
| AC-07 | All twelve format combinations decode successfully | integration | Each static JPEG, PNG, WebP and HEIC input produces each JPEG, PNG and WebP output with the chosen actual format; do not assert smaller size or byte identity. |
| AC-07 | Every input defaults to JPEG and all output choices work | e2e-through-UI | Each supported input initially selects JPEG; format selection reaches a complete download in the chosen format. |
| AC-08 | JPEG always explains conditional transparency loss | e2e-through-UI | Warning appears before submission whenever JPEG is selected, including its default and unavailable Preview; choosing PNG or WebP removes the JPEG warning. |
| AC-08 | Output alpha follows the selected format | integration | Fully and partly transparent regions composite onto white for JPEG; PNG and WebP retain alpha. |
| AC-09 | Orientation is applied once before bounds | integration | Fixtures with rotation and mirroring metadata produce the correct visible orientation and dimensions without double transformation. |
| AC-09 | Service metadata is removed without mislabeling colors | integration | GPS, camera, textual and other service metadata are absent; required compatible color information survives, including pixel-model changes and supported non-profile color descriptions. |
| AC-09 | Preview and downloaded image agree on visible orientation | e2e-through-UI | Any available Preview and decoded download show the same correct orientation; bounds apply to that orientation. |
| AC-10 | Non-first HEIC primary image is the sole output image | integration | Designated primary image is selected even when not first; static extra images are omitted rather than classified as animation. |
| AC-10 | HEIC high-dynamic-range content becomes ordinary eight-bit output | integration | Output is decodable ordinary eight-bit content with compatible color interpretation; no source high-dynamic-range appearance guarantee is asserted. |
| AC-10 | General HEIC notice precedes submission without inspection | e2e-through-UI | Form explains primary-only output, omitted extra images and eight-bit conversion before any upload, without inspecting server content first. |
| AC-11 | Supplied dimensions with omitted format use JPEG | contract | Width-only, height-only or both valid dimensions suffice; omitted format falls back to JPEG only after supplied-parameter validation. |
| AC-11 | Empty bounds impose no constraint with an explicit format | contract | Omitted or empty dimensions plus an explicit valid format are accepted; valid large bounds do not introduce a product dimension maximum or enlarge input. |
| AC-13 | Successful response contains only the current binary result | contract | Actual format, media type and attachment filename agree: result.jpg, result.png or result.webp; no result identifier, lookup URL or result wrapper is returned. |
| AC-13 | Complete current result downloads once and resets | e2e-through-UI | Full downloaded bytes decode correctly with matching extension; original bytes stay unchanged; reset clears file, Preview, errors and result, empties bounds, selects JPEG and returns focus to file selection without reloading. |
| AC-13 | Reset preserves download and permits another conversion | e2e-through-UI | Download completes despite immediate cleanup/reset, without waiting for disk-save confirmation; a second conversion, including the same file, downloads once independently. No result characteristics or repeat-download action remain. |
| AC-16 | Successful lifecycle releases owned resources | integration | Upload handles, decoded images, intermediates and response output are released at their lifecycle boundaries, leaving no server image for later retrieval. |
| AC-16 | Selection and handoff release obsolete browser resources | e2e-through-UI | Replacement and success release obsolete Preview resources; result resources are released after safe handoff without interrupting download or retaining a repeat-download capability. |

## Edge cases / error paths

Expected outcomes here are semantic; response statuses and envelope shapes are asserted from the linked contract, without treating message wording or validation order as stable identifiers.

| AC (spec.md §5) | Test name | Level | Expected outcome |
|---|---|---|---|
| AC-01 | Empty selection is rejected before preview | e2e-through-UI | Understandable file error, no Preview preparation, disabled processing and available file selection. |
| AC-01 | Oversized selection is rejected before preview | e2e-through-UI | More than 20,000,000 bytes is rejected locally without Preview preparation or upload; parameters and processing remain disabled. |
| AC-02 | Native preview failure is silently omitted | e2e-through-UI | No old picture, broken placeholder or processing error; eligible input remains processable. |
| AC-03 | Failed replacement preview never restores the old picture | e2e-through-UI | Both failed current callbacks and delayed previous callbacks leave only the valid current selection state. |
| AC-11 | Missing file is rejected at the boundary | contract | Direct request bypassing form restrictions receives an understandable rejection and no successful result. |
| AC-11 | Missing all transformation parameters is rejected | contract | Omitted or empty bounds with omitted format are rejected; fallback JPEG does not count as a supplied parameter. |
| AC-11 | Invalid dimensions are rejected at the boundary | contract | Zero, negative, fractional and nonnumeric supplied bounds are rejected, with no successful result. |
| AC-11 | Explicit empty or unsupported output format is rejected | contract | Explicit invalid format is not treated as omission or replaced by JPEG fallback. |
| AC-11 | Invalid dimensions can be corrected without reselection | e2e-through-UI | Local errors are associated with controls; current file and entered values remain available for correction. |
| AC-11 | Server parameter rejection is readable and recoverable | e2e-through-UI | Known field locations map to controls; other explanations appear at form level; current input is retained and restrictions can be corrected. |
| AC-12 | Empty upload is rejected independently of the form | contract | Server refuses an empty file even when browser checks are bypassed. |
| AC-12 | Corrupted content produces no successful image | integration | Truncated or malformed image data is rejected safely and all opened resources are released. |
| AC-12 | Unsupported actual image content is rejected | integration | An unsupported format remains unsupported despite a supported-looking extension or declared media type. |
| AC-12 | Boundary trusts actual content rather than file labels | contract | Corrupted and unsupported uploads are rejected; valid supported content with misleading filename or media type is handled according to its actual format. |
| AC-12 | Real animation is rejected while static collections remain allowed | integration | Animated supported-container inputs and HEIF presentation timelines are rejected; static extra images and non-timed galleries are allowed. Cover edit lists, composition offsets, fragmented timelines and misleading brands; do not classify solely by image count. |
| AC-12 | Animated upload is rejected at the boundary | contract | Actual animation produces an understandable failure and no successful result. |
| AC-12 | File byte boundary is inclusive and independent of multipart overhead | contract | Valid files immediately below and at 20,000,000 bytes are accepted; one byte above is rejected even without a trustworthy declared length. Envelope bytes do not consume the file allowance. |
| AC-12 | Selected image pixel boundary is inclusive | integration | Valid selected images below and at 40,000,000 pixels are allowed; images above are rejected before expensive decode and dimensions are rechecked after decode where necessary. |
| AC-12 | Excessive pixel input is rejected through the API | contract | Direct oversized-pixel input yields an understandable limit rejection and no successful result. |
| AC-12 | Server content rejection preserves correction and retry | e2e-through-UI | Corrupt, unsupported, animated and over-pixel inputs receive readable errors; current input survives recoverable rejection and controls are restored. |
| AC-14 | Application exposes no result history or retrieval contract | contract | Route/contract inspection and representative lookup requests find no image retrieval capability, including after another operation; unknown API paths disclose no image. No authentication system is invented. |
| AC-14 | Independent operations never exchange result data | integration | Distinguishable inputs from independent callers produce only their corresponding results, including when one operation fails or is interrupted. |
| AC-15 | Busy state locks every input and repeat submission | e2e-through-UI | One pending operation, disabled file/dimension/format controls and repeat submission, truthful busy announcement without fabricated percentages or a cancel action. |
| AC-15 | Processing failure preserves current input for explicit retry | e2e-through-UI | Safe readable error restores controls and retains file, bounds, format and available Preview; retry creates one new submission, never an automatic replay. |
| AC-15 | Request failure or incomplete response never downloads | e2e-through-UI | Network failure and truncated result after initially successful headers remain errors with retained input and retry; partial bytes never trigger download. |
| AC-15 | Unreadable error bodies use a safe explanation | e2e-through-UI | String and structured validation bodies are understandable; missing or malformed bodies use a general failure message. Raw rejected input, context, exception objects and JSON dumps are not rendered. |
| AC-15 | Stale or duplicate completion cannot trigger another download | e2e-through-UI | An obsolete or consumed operation changes no current form state and cannot download, including after failure or success reset. |
| AC-15 | Reload or reopening restores no previous operation | e2e-through-UI | Reload/closure during processing, after recovery and after success returns to the initial form without input or result restoration. |
| AC-16 | Malformed or interrupted multipart releases partial uploads | integration | Parser failure, premature end and actual client disconnect close partial handles, including before a completed upload object exists. |
| AC-16 | Decode transformation and encoding failures release resources | integration | Controlled failures at each processing phase release uploads, images and intermediates; no previous result is restored. |
| AC-16 | Native work keeps ownership until it actually finishes | integration | Actual disconnect during native processing does not prematurely close resources still in use; cleanup completes after native work ends. |
| AC-16 | Interrupted response releases response-owned output | integration | Failed result transfer releases its output resources without retaining a server result for retrieval. |
| AC-16 | Success and failure logs disclose no identifying image data | integration | Captured logs and safe errors contain no image bytes, original filenames, identifying metadata or internal exception details. |
| AC-16 | Browser error and closure cleanup preserves only permitted state | e2e-through-UI | Recoverable failure may retain current input/Preview but releases failed operation resources; replacement, handoff and teardown release obsolete resources. Closure after handoff does not break an initiated download. |

## Test data and integration strategy

| Data or dependency | Construction and oracle | Cleanup boundary |
|---|---|---|
| Geometry and ordinary format fixtures | Generate synthetic images with known sizes, edge markers, asymmetric orientation markers and transparent patches. Assert decoded properties rather than encoded byte identity; allow encoding-appropriate pixel tolerance without weakening alpha, geometry or white-background requirements. | Per test: close images, streams and generated files. |
| Byte and pixel limits | Construct valid decodable fixtures at exact byte/pixel boundaries and neighboring values. Use controlled dimensions rather than assuming compressed size predicts decoded pixels. Positive boundary cases must remain genuinely decodable. | Per test: delete fixture copies and multipart spools after closing handles. |
| HEIC, animation and color controls | Reuse verified synthetic feasibility fixtures and record known primary image, timing, bit depth, orientation and color expectations. Include non-first primary, non-timed galleries, real and fragmented timelines, compatible profiles and supported profile-free color descriptions. Use independent expected properties; no personal photographs. | Per test: isolate mutable copies and close native resources. Immutable fixtures remain repository test data. |
| Request and codec integration | Use real codecs, parsing, temporary storage and the application runtime, including an ephemeral instance of the existing application image for platform/socket checks. No database, queue or cache exists; do not add a throwaway datastore. Controlled phase failures may be injected for cleanup, but do not replace real codec and transport acceptance. | Per test: assert explicit handle/reference cleanup. Per suite: stop created processes and remove its temporary directory/container. Allocator-reserved memory alone is not a retained image. |
| Browser journeys | Use isolated browser state, synthetic selections and a dedicated download directory. Compare the selected original before/after and decode completed downloads. Reuse available browser probes against the implemented form; retain manual evidence for unsupported automation surfaces. | Per test: close pages, clear test-owned downloads and check obsolete URLs. Do not delete user files. |

Run real native decoding/color cases on macOS and Linux. Version-sensitive native bindings and safety protections remain implementation acceptance obligations from SAD §11. A feasibility probe pass does not replace the corresponding production-path test. Isolation instrumentation observes lifecycle events and live ownership, not a target resident-memory value or a timing benchmark.

## UI flow and state coverage

| Source | Script and acceptance |
|---|---|
| US-01 | Initial selection, exact byte eligibility, available/unavailable/failed Preview, replacement including invalid input, and stale callbacks. Observe zero uploads before submission. |
| US-02 | Width-only, height-only, both and blank bounds; invalid dimensions and correction; inspect downloaded geometry after a real submission. |
| US-03 | Default JPEG, each output choice, notices, alpha/orientation/color properties and HEIC behavior; finish through automatic download. |
| US-04 | One complete download, clean reset, second conversion including same-file reselection, stale/duplicate completion and reload/closure. |
| US-05 | Local rejection, real server rejection, processing/transfer failure, retained-input retry and interruption without restoration. |

Cover SCR-01 default, empty, ready, validation, loading, error and success-as-reset, including all Preview and field/form error variants. At 360 and 1280 CSS pixels, run the complete keyboard flow with visible focus, accessible labels/errors and busy announcements, focus return after reset, long filenames/errors and no horizontal overflow. Reduced motion removes decorative animation without loss of function. Ordinary state-change motion must not delay interaction/download, fabricate progress or cause layout jumps. Readable contrast requires the owner's manual acceptance, not an invented numeric threshold or screenshot baseline.

Browser acceptance covers desktop Chrome, Safari and Firefox plus real iPhone Safari. Viewport emulation proves layout, not mobile download handoff. Android remains explicitly deferred by the owner; earlier reported mobile download probes are supporting evidence, not complete implemented-flow acceptance. Record browser/device and outcome for the agreed journeys; do not add another browser harness or claim unexecuted coverage.

## NFR validation (load)

**N/A by explicit owner decision: no performance, latency, throughput or timing benchmarks.** Spec §6 contains numeric functional/resource requirements, so the generic template's `no numeric NFR` marker would be false. The accepted plan overrides the skill's numeric-NFR-to-load rule: no target rate, duration or performance threshold is invented.

| NFR | Functional verification | Threshold |
|---|---|---|
| Input limits | AC-01 and AC-12 boundary scenarios, including direct requests | At most 20,000,000 file bytes and 40,000,000 decoded selected-image pixels; equality allowed. |
| Preview locality | AC-02 network observation during selection, editing and Preview | Zero file-upload requests before submission. |
| Form concurrency | AC-15 locked controls and duplicate-submit attempts | At most one submitted operation from the current form; no global concurrency promise. |
| Transient resources and privacy | AC-16 success, failure and interruption ownership checks plus logs | Zero retained upload handles, decoded images or result buffers after their lifecycle; zero image content in logs. |
| Accessibility and responsive UI | Full UI flow and state review above | Keyboard operation and visible focus; owner-approved contrast; zero decorative animation under reduced motion; no horizontal overflow at 360 and 1280 CSS pixels. |

## CI placement

| When | Checks |
|---|---|
| Every PR | Run unit, contract and bounded integration scenarios in the existing test setup; preserve foundation health/assets/unknown-API smoke checks and existing static checks. Build actual frontend assets before backend smoke execution. |
| Before implementation acceptance or release | Complete real macOS/Linux codec/color and interruption cases, the agreed browser/device journeys, owner contrast acceptance and security review of decoding, resource limits, cleanup and confidential errors/logs. Repeat the shared smoke checks against the application image. |
| After relevant changes | Repeat affected browser/platform evidence when processing, form state, download handoff or runtime dependencies change; preserve the complete acceptance gate. No performance schedule is introduced. |

This is test placement advice, not a pipeline change. Browser scenarios may be agent-driven or manual with recorded evidence using available capabilities; they are not claimed as existing unattended CI suites. Concrete commands are resolved from the repository during implementation. Extend relevant existing tests first; new feature test files are justified only by this map and the existing task breakdown.

## Decisions and verification

The owner accepted all proposed per-AC levels and the strategy without edits, drops or deferred decisions. Edits-log: empty. Performance exclusion is an explicit accepted exception, not an unresolved product question. No public API, dependency, test infrastructure or implementation changes are part of this document.

Structural verification must re-read this file and check: all sixteen ACs appear; error/authorization criteria have dedicated rows; each level is in the fixed vocabulary; no concrete test-tool names appear; the load decision is explicit and consistent with spec §6; and this separate file is correct for M/standard. Report the load item as an approved exception to the unmodified skill checklist, never as an unqualified six-of-six pass. Test execution and security acceptance remain pending implementation.

## Approved output limit amendment — 2026-09-06

AC-07/AC-15 contract coverage: a valid input whose computed result exceeds 16,383 pixels on either side for WebP or 65,500 for JPEG returns actionable 422; equality passes. Supplying a sufficient bound succeeds without extra reduction, and the UI retains input/parameters after rejection. The owner explicitly approved this exception to unconditional conversion success.
