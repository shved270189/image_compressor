---
status: Draft
owner: "Project owner"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-06"
feature_size: M
---

# Spec — image-resize-convert

> **Glossary:** [CONTEXT.md](./CONTEXT.md)
> **Sources:** [Idea brief](../../idea-brief.md), [roadmap](../../roadmap.md), [architecture map](../../architecture-map.md), [ADR 0003](../../adr/0003-transient-image-processing.md), and the confirmed interview.
> **Route:** standard.

## 1. Context

The project owner needs a personal local single-page tool to prepare one image under optional maximum width and height constraints and convert its format. The running foundation has no image-processing behavior.

The trigger is the owner's existing personal need. There is no launch deadline, usage-frequency commitment or public-hosting requirement.

The committed approach is one responsive form with an optional original preview above it when the browser can display the selected file, optional dimension limits, an output-format choice, a clear processing action and a downloadable result with actual dimensions and file size. Existing adjacent tools already cover much of this need; the reason to build remains the owner's own workflow, not an asserted market advantage.

Processing requires a file and at least one supplied transformation parameter. The form supplies JPEG by default for every input, so choosing a non-empty file within the byte limit enables processing without a manual parameter change; content validation occurs on the server when processing is submitted. Both dimension limits remain independently optional. If dimensions are supplied without an output format, the output is JPEG for every input format. Supplying neither dimensions nor an output format remains an error; the omitted-format fallback does not count as a supplied parameter. Preview stays entirely on the frontend, unsupported preview formats are silently omitted and no file is sent to the server until processing is submitted. Performance timing targets and timing measurements are explicitly excluded by the owner.

## 2. Goals

- Complete image selection, visual verification, parameter selection and download within one local page.
- Deliver an image within supplied maximum dimensions, preserving aspect ratio and never enlarging it.
- Produce predictable conversions and errors while keeping image contents transient.

## 3. Non-goals

- File-size targeting and minimum quality under a byte budget belong to image-size-limit.
- Batch processing, cropping, stretching, enlargement and saved presets are outside the agreed workflow.
- Accounts, history, persistent image retrieval and public deployment are outside this local feature.
- Animation output, preservation of extra HEIC images, HDR output, a quality control and a cancel button are excluded to retain the agreed single-image flow.

## 4. User stories

### US-01: Select and inspect an image
**As a** Власник картинки
**I want** to select an Оригінал and see its Preview above the form when my browser can display it
**So that** I can verify the selected picture before processing.

### US-02: Set maximum dimensions
**As a** Власник картинки
**I want** to set either or both Максимальні розміри independently
**So that** the Результат fits my bounds without cropping, distortion or enlargement.

### US-03: Choose the output format
**As a** Власник картинки
**I want** to choose JPEG, PNG or WebP, with JPEG initially selected
**So that** I receive a Результат in the desired supported format.

### US-04: Download the current result
**As a** Власник картинки
**I want** to see actual dimensions and file size and download the Результат
**So that** I can use the completed file without overwriting the Оригінал.

### US-05: Recover from rejected processing
**As a** Власник картинки
**I want** clear validation and processing errors with a retry
**So that** I can correct my input without unnecessary reselection.

## 5. Acceptance criteria

### AC-01 (US-01) — happy
**Given** no Оригінал has been selected,
**When** Власник картинки opens the form,
**Then** the file-selection control remains available, transformation parameter controls are disabled or hidden and processing is disabled; selecting a non-empty file of at most 20,000,000 bytes reveals or enables the transformation controls with JPEG selected and empty dimension limits, and enables processing without waiting for content validation. Selecting an empty file or a file above that byte limit immediately shows an understandable error, omits Preview and keeps processing disabled.

### AC-02 (US-01) — happy
**Given** a supported Оригінал within the input limits,
**When** Власник картинки selects it,
**Then** a supported Preview appears above the form, preserves the complete image and correct orientation and is prepared entirely on the owner's device without sending the file for preview generation; when the browser cannot display the file, no Preview or broken-image placeholder is shown, and this absence does not block processing, including for HEIC.

### AC-03 (US-01, US-04) — cross-context
**Given** an Оригінал already has a Preview or Результат,
**When** Власник картинки makes a new file selection,
**Then** the previous Preview and Результат disappear, dimensions reset to empty and format resets to JPEG, including when the newly selected file is empty or above the byte limit; delayed work for the old selection must never replace the current Preview or Результат, and an unavailable or failed Preview is omitted rather than displaying the old picture, a broken-image placeholder or a processing error.

### AC-04 (US-02) — happy
**Given** a correctly oriented Оригінал measuring 2400 by 1200 pixels,
**When** Власник картинки sets only maximum width to 1200,
**Then** the Результат measures 1200 by 600 pixels; a height-only limit of 300 yields 600 by 300; both width 1200 and height 300 yield 600 by 300.

### AC-05 (US-02) — domain invariant
**Given** supplied Максимальні розміри,
**When** Власник картинки processes the Оригінал,
**Then** the Результат uses the largest proportional scale that fits all supplied bounds without enlarging the oriented original, with no additional reduction. Each scaled dimension is rounded to the nearest whole pixel, with exact half-pixel values rounded up and a minimum of one pixel. The Результат does not exceed either supplied bound or either original oriented dimension, contains the whole image and preserves aspect ratio subject only to this whole-pixel rounding and minimum. An oriented original of 1000 by 333 pixels with maximum width 500 produces a result of 500 by 167 pixels.

### AC-06 (US-02, US-03) — happy
**Given** an Оригінал measuring 800 by 600 pixels,
**When** Власник картинки supplies maximum width 1600 or selects the same output format as the original,
**Then** processing remains allowed because a parameter is supplied; an ineffective dimension limit leaves dimensions unchanged, and a same-format operation still produces the agreed normalized Результат.

### AC-07 (US-03) — happy
**Given** a supported static JPEG, PNG, WebP or HEIC Оригінал,
**When** Власник картинки chooses JPEG, PNG or WebP and processes it,
**Then** a decodable Результат is produced in the chosen format; JPEG is the initial output choice for every input, including JPEG itself, and there is no guarantee of smaller file size or byte-identical output.

### AC-08 (US-03) — domain invariant
**Given** a selected Оригінал, whether or not its transparency is known or Preview is available,
**When** Власник картинки chooses JPEG,
**Then** the form always shows a conditional warning before processing: if the image has transparency, it will become white; this also applies when JPEG is selected by default and requires no advance transparency detection. The JPEG Результат uses white behind partial and full transparency; PNG and WebP output retain transparency.

### AC-09 (US-01, US-03) — domain invariant
**Given** an Оригінал with orientation information or service metadata,
**When** Власник картинки processes it,
**Then** the Результат and any available Preview have the correct visible orientation, and dimension limits apply to that orientation; the Результат omits GPS, camera and textual metadata while retaining information required for correct color interpretation.

### AC-10 (US-01, US-03) — happy
**Given** a HEIC Оригінал with additional images or high-dynamic-range content,
**When** Власник картинки processes it,
**Then** only the designated primary static image is used; the form explains the general HEIC rules before submission: extra images are omitted and high-dynamic-range content becomes ordinary 8-bit output, with no promise of retaining the original high-dynamic-range appearance; this notice requires no advance server inspection.

### AC-11 (US-05) — error
**Given** no file, no supplied transformation parameter, an invalid dimension or an unsupported output choice,
**When** processing is attempted,
**Then** the system rejects the attempt and explains the reason even when form restrictions are bypassed; dimensions must be positive whole pixel counts, empty dimensions impose no bound, and a supplied output format including the form's default JPEG counts as a parameter. Valid supplied dimensions with no output format produce JPEG; omitting both dimensions and output format remains an error.

### AC-12 (US-05) — error
**Given** an empty, corrupted, unsupported or animated Оригінал, or an input above 20 million bytes or 40 million decoded pixels,
**When** processing is attempted,
**Then** the system rejects it with an understandable reason and produces no successful Результат; exact limits are allowed, support is determined from actual content, and additional HEIC images are subject to the primary-image rule rather than treated as animation. The form checks only whether the selected file is empty or exceeds the byte limit before preparing Preview; the server checks content, animation and decoded pixel count when processing is submitted, and enforces all input limits even when form restrictions are bypassed.

### AC-13 (US-04) — cross-context
**Given** successful processing for the current selection,
**When** Власник картинки inspects and downloads the Результат,
**Then** the displayed width, height, format and file size describe that exact downloaded file, the filename extension matches its format and the Оригінал remains untouched. Changing either dimension limit or the output format, or starting another processing operation, immediately removes the previous Результат and its download action; a failed new operation does not restore the previous Результат.

### AC-14 (US-04) — authorization
**Given** a Результат belongs to a different operation or is no longer available to the current page,
**When** Власник картинки attempts to retrieve it,
**Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.

### AC-15 (US-05) — error
**Given** processing is in progress,
**When** Власник картинки waits, processing fails or the page closes,
**Then** the form disables file selection, all transformation parameter controls and repeat submission while processing, shows a truthful busy state without fabricated percentages, restores the controls and retry with the selected file and parameters after a recoverable error, and offers no result restoration after closing or reloading the page. Successful completion also restores the controls; only the current operation may display a Результат.

### AC-16 (US-01, US-04, US-05) — cross-context
**Given** processing has completed, failed or been interrupted,
**When** that operation's lifecycle ends,
**Then** the application retains no server-side original or result for future retrieval; preview generation never sends a file to the server. The current page may retain its Preview until a new file selection or page closure. It may retain its Результат until a new file selection, a dimension or output-format change, another processing operation starts, or the page closes. Each removal releases the obsolete preview or download resources immediately.

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Input limits | At most 20,000,000 bytes and 40,000,000 decoded pixels of the selected static image; equality allowed | Processing boundary tests before expensive server decoding; selection checks reject empty files and files above the byte limit before preparing a local Preview, while server content, animation and pixel-count checks run on submission |
| Preview locality | Zero file-upload requests caused by selection, parameter editing or Preview preparation | Browser network checks; native image display using a local object URL, without an added decoder dependency or a server preview operation |
| Form concurrency | At most one submitted processing operation from the current form; file selection and all transformation parameter controls disabled while processing | Duplicate-submit and disabled-control checks, including restoration after success or recoverable failure |
| Transient resources | Zero retained upload handles, decoded images or result buffers after their operation lifecycle; zero image content in logs | Success, failure and interruption lifecycle tests and log inspection; allocator-reserved memory is not treated as a retained image |
| Accessibility | Every interactive control is keyboard-usable with visible focus; every label, error and action passes the project owner's manual readable-contrast review; with reduced motion, zero decorative animations and zero loss of functionality | Full keyboard flow, visible-focus review, manual contrast acceptance by the project owner without numeric contrast thresholds, and reduced-motion browser check |
| Responsive UI | Complete flow at viewport widths 360 and 1280 CSS pixels with no horizontal page overflow | Browser visual review at both widths |

Performance latency, throughput and timing benchmarks are N/A by explicit owner decision. Public-service uptime targets are N/A for this local-only feature. Under ordinary motion settings, retain animations that communicate actions and state changes; remove decorative motion when reduced motion is requested. UI motion must not delay input or result download, fabricate progress or cause layout jumps.

## 6.1 Security / privacy

- **Data classification:** confidential — originals may contain personal photos.
- **Personal data touched:** image contents and input metadata may contain people and locations; no new identity fields or accounts.
- **AuthZ/AuthN impact:** none; this is a local owner-operated application without accounts. Result isolation is achieved by absence of persistent lookup or history, not by claiming authenticated ownership.
- **Abuse cases:** oversized or excessive-pixel input is rejected before expensive decoding; malformed or disguised content is rejected; stale work never exposes a different selection; image contents and identifying metadata are not logged or retained for future retrieval.
- **Security review:** Required before implementation acceptance because untrusted image decoding and temporary-file handling are introduced.

## 7. Metrics / KPIs

Acceptance indicators rather than usage analytics; all targets are due before this feature is declared complete.

- Supported transformation coverage — baseline 0 existing processing scenarios; target all 12 input-to-output format combinations pass with valid control fixtures, including static HEIC primary-image handling.
- Constraint and error coverage — baseline 0 feature validation scenarios; target all agreed bound, orientation, transparency, metadata, invalid-input and interruption checks pass.
- Complete user journey — baseline 0 implemented image-to-download journeys; target the complete selection-to-download flow, including displayed and unavailable Preview cases, passes at both specified viewport widths, with keyboard-only interaction, visible focus, readable contrast and decorative motion disabled under reduced motion.

No analytics collection or timing measurement is added.

## 8. Open questions

None at the product-requirement level. The Tech Lead must verify HEIC decoder/platform feasibility and the resource-cleanup approach during design, before sdd:tasks; implementation must prove cleanup on success, failure and interruption. These checks do not permit dropping accepted HEIC conversion behavior. HEIC Preview is optional and depends solely on native browser support.

## Clarification log — 2026-09-06

Depth: medium. Independent clean-context ambiguity review completed. Six findings resolved, zero deferred, and one rejected by the project owner; no findings remain unresolved.

| Class | Reference | Outcome | Before / after |
|---|---|---|---|
| conflicting-requirement | §6 Accessibility and motion | resolved | Unqualified decorative-motion ban / decorative motion removed only under reduced motion; ordinary state-change animations retained |
| under-specified-AC | AC-03, AC-13, AC-15, AC-16 | resolved | Result lifetime and editing during processing unspecified / parameter changes and new processing remove the result immediately; processing locks controls; recovery retains the input and parameters |
| under-specified-AC | §1, AC-11 | resolved | Dimensions without an output format unspecified / JPEG fallback for supplied dimensions; no supplied parameters remains an error |
| under-specified-AC | AC-08 | resolved | Warning depends on unspecified advance transparency knowledge / conditional warning for every JPEG output, including the default |
| under-specified-AC | AC-01, AC-03, AC-12, §6 Input limits | resolved | Valid-selection timing unspecified / local empty-file and byte-limit checks; server content, animation and pixel checks on submission; every new selection resets prior state |
| under-specified-AC | AC-05 | resolved | Whole-pixel rounding and degree of reduction unspecified / largest fitting scale; nearest-pixel rounding with halves up and minimum one pixel |
| unmeasured-NFR | §6 Accessibility | rejected | Numeric contrast thresholds proposed / project owner explicitly retains manual readable-contrast acceptance without numeric thresholds |
