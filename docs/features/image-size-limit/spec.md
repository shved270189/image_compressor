---
status: Draft
owner: "Project owner"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-13"
feature_size: S
---

# Spec — image-size-limit

> **Glossary:** [CONTEXT.md](./CONTEXT.md)
> **Sources:** [Idea brief](../../idea-brief.md), [roadmap](../../roadmap.md), [architecture map](../../architecture-map.md), [image-resize-convert spec](../image-resize-convert/spec.md), confirmed interview, and the form and processing modules named in the interview.
> **Route:** quick.

## 1. Context

The project owner needs the existing single-image form to honour an independently optional result file-size budget. Resize and convert already deliver optional maximum dimensions, format choice, automatic download and a clean form; they do not target result bytes, and they forbid extra shrinking beyond supplied dimension bounds.

The trigger is the owner's personal workflow and roadmap step 3. There is no launch deadline or public-hosting requirement. Decision D2 (minimum quality and unattainable limits) is closed in this specification.

The committed approach is one form with an independent Ліміт ваги. When supplied, it is the primary constraint: the result may use fewer pixels than the supplied maxima and the original, without cropping, stretching, enlargement or a silent format change. Adjacent compress-to-size tools already offer kilobyte or megabyte targets, but they do not treat that target as a constraint that may undercut chosen maxima, and they do not auto-download a miss while leaving the form ready to retry. When the encoded result meets the bound or the bound is omitted, automatic download and form reset stay as they are today. When the bound cannot be met even at the technical minimum, the smallest result still downloads, the form is kept, and the actual size plus a notice that the bound was exceeded are shown so the owner can change settings and process again.

Traceability: this feature extends the current parameter fieldset rather than a second screen. Empty Ліміт ваги must preserve the existing geometry rule (largest proportional fit, no extra reduction). Upload byte and pixel caps stay unchanged and are not this bound.

## 2. Goals

- Let the image owner apply an optional result byte budget without losing the current one-form flow.
- Meet that budget when it is attainable, preferring the largest proportional result that still fits.
- Make an unattainable budget visible and retryable instead of a silent oversize file or a hard failure with no file.

## 3. Non-goals

- A quality slider or minimum-quality/minimum-dimension floor — the owner chose no floor beyond one pixel and the smallest file the chosen format can produce.
- Silently changing the output format to hit the bound — format remains the owner's choice.
- Changing the upload cap, decoded-pixel cap, batch processing, cropping, stretching, enlargement, accounts, history or public deployment — those stay outside this increment.
- Showing result characteristics after a met-limit or omitted-limit success — that path keeps today's automatic download and clean form.
- A cancel control during processing — the existing single-operation busy state remains.

## 4. User stories

### US-01: Set optional Ліміт ваги
**As a** Власник картинки
**I want** to set an independently optional Ліміт ваги as a positive decimal with a unit selector of Mb or Kb to the right of the number, Mb initially selected, empty meaning no bound
**So that** the Результат can target a file-size budget, and a supplied Ліміт ваги counts as a transformation parameter (processing may run with only that bound and the initial JPEG).

### US-02: Shrink below dimension ceiling
**As a** Власник картинки
**I want** a supplied Ліміт ваги to outrank Максимальні розміри as a floor
**So that** the system may reduce pixels below those maxima and below the Оригінал to meet the budget, while maxima remain a ceiling, without cropping, stretching, enlargement or a silent format change.

### US-03: Download when within limit
**As a** Власник картинки
**I want** a Результат that meets the Ліміт ваги, or processing with an empty Ліміт ваги, to download automatically and the form to reset
**So that** success stays the same as today's flow and no result characteristics remain on the page.

### US-04: Retry after a miss
**As a** Власник картинки
**I want** the smallest Результат still downloaded when the Ліміт ваги cannot be met, the form kept, and the actual size plus that the bound was exceeded shown
**So that** I can change settings and process again; a new file starts a new cycle.

### US-05: Correct an invalid Ліміт ваги
**As a** Власник картинки
**I want** zero, negative or non-positive Ліміт ваги rejected with a clear reason
**So that** I can fix the field without losing the Оригінал. Empty remains valid and means no bound.

## 5. Acceptance criteria

### AC-01 (US-01) — happy
**Given** a selected Оригінал within the input limits,
**When** Власник картинки leaves Ліміт ваги empty and processes,
**Then** no result byte bound is applied and dimension and format behaviour matches the existing form.

### AC-02 (US-01) — happy
**Given** a selected Оригінал,
**When** Власник картинки sets Ліміт ваги,
**Then** the control is a numeric field that accepts a positive decimal, with a unit selector to the right of the number whose options are Mb and Kb and with Mb selected initially; empty remains allowed and means no bound.

### AC-03 (US-01) — happy
**Given** a selected Оригінал and no Максимальні розміри,
**When** Власник картинки supplies only a Ліміт ваги and leaves output format at the initial JPEG,
**Then** processing is allowed because a transformation parameter is supplied.

### AC-04 (US-02) — domain invariant
**Given** supplied Максимальні розміри and an empty Ліміт ваги,
**When** Власник картинки processes the Оригінал,
**Then** the Результат uses the largest proportional scale that fits all supplied bounds without enlarging and with no additional reduction. An oriented original of 2400 by 1200 pixels with only maximum width 1200 yields 1200 by 600.

### AC-05 (US-02) — domain invariant
**Given** a Ліміт ваги and optional Максимальні розміри,
**When** Власник картинки processes the Оригінал,
**Then** the Результат never exceeds any supplied dimension bound or either original oriented dimension, never enlarges, never crops or stretches, and keeps the chosen output format. Additional reduction happens only while the encoded file is larger than the Ліміт ваги and stops at the largest proportional size and highest encoding quality the chosen format allows that already meets the bound. If even one pixel and the smallest file of that format still exceed the bound, that is a miss under AC-07, not a rejection without a file. Each scaled dimension is rounded to the nearest whole pixel, with exact half-pixel values rounded up and a minimum of one pixel. An oriented original of 2400 by 1200 pixels with maximum width 1200 and a Ліміт ваги smaller than the 1200-by-600 encoding yields a result shorter than 1200 in width, with aspect ratio 2 to 1 subject to that rounding.

### AC-06 (US-03) — happy
**Given** a Ліміт ваги that the Результат can meet, or an empty Ліміт ваги,
**When** processing completes successfully,
**Then** the page initiates exactly one automatic download of a Результат whose size in bytes is at most the Ліміт ваги when one was supplied, then resets the form to the initial empty state: the selected file, Preview, Результат, errors, miss facts, both dimension limits and Ліміт ваги are cleared and format returns to JPEG.

### AC-07 (US-04) — happy
**Given** a Ліміт ваги that cannot be met even at one pixel and the smallest file the chosen format can produce,
**When** processing completes,
**Then** a Результат is still produced in the chosen format and one automatic download starts; the form is not reset; the page shows the actual Результат size and that the Ліміт ваги was exceeded; the Оригінал and parameters remain so the owner can change them and process again.

### AC-08 (US-05) — error
**Given** a filled Ліміт ваги that is zero, negative or not a positive number,
**When** processing is attempted,
**Then** the system rejects the attempt, explains that Ліміт ваги must be a positive number with Mb or Kb or left empty, produces no Результат, and keeps the Оригінал.

### AC-09 (US-03, US-04) — authorization
**Given** a Результат belongs to a different operation or is no longer available to the current page,
**When** Власник картинки attempts to retrieve it,
**Then** the application provides no history, lookup or retrieval capability for that result and discloses no image from another operation; no account or ownership-verification system is introduced.

### AC-10 (US-01, US-04) — cross-context
**Given** an Оригінал has been selected, including after a miss,
**When** Власник картинки makes a new file selection,
**Then** the previous Preview, miss facts, errors, dimensions, format and Ліміт ваги reset (empty bound, JPEG); delayed work for an old selection or completed operation must never replace the current Preview, show an old miss or trigger another download.

### AC-11 (US-04) — cross-context
**Given** processing is in progress,
**When** Власник картинки waits, starts another process, processing fails or the page closes,
**Then** file selection and all transformation controls including Ліміт ваги are disabled while processing, a truthful busy state is shown without fabricated percentages, a new process replaces previous miss facts, only the current operation may initiate a download, recoverable failure restores retry with the selected file and parameters, and closing or reloading the page restores neither input nor result. After a miss, those controls remain usable so the owner can change settings and process again.

### AC-12 (US-01, US-02) — domain invariant
**Given** a supplied Ліміт ваги,
**When** the encoded Результат is compared with that bound,
**Then** the bound in bytes equals the entered number multiplied by 1,000,000 for Mb or by 1,000 for Kb, comparison uses whole bytes of the encoded Результат, and 0.5 Mb equals 500,000 bytes.

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Input limits | At most 20,000,000 bytes and 40,000,000 decoded pixels of the selected static image; equality allowed; Ліміт ваги is not an upload cap | Existing processing-boundary checks; selection still rejects empty files and files above the byte limit before Preview |
| Ліміт ваги arithmetic | 1 Mb = 1,000,000 bytes; 1 Kb = 1,000 bytes; comparison after encoding in whole bytes | Fixture: 0.5 Mb = 500,000 bytes; 200 Kb = 200,000 bytes |
| Form concurrency | At most one submitted processing operation; file selection and all transformation controls including Ліміт ваги disabled while processing | Duplicate-submit checks; miss-retry remains single-flight |
| Miss visibility | After an over-limit Результат, actual size and the exceeded notice remain until the next process, a new file selection or page close | Browser check of the kept form |
| Transient resources | Zero server-side originals or results after the operation lifecycle; a miss does not create retrievable history. The current page may keep the Оригінал and parameters through a miss until a new file selection, a met-limit reset or page close | Success, miss, failure and interruption lifecycle checks |
| Accessibility | Every interactive control including the Ліміт ваги number and unit is keyboard-usable with visible focus; labels, errors and the exceeded notice pass the project owner's manual readable-contrast review; reduced motion as on the existing form | Keyboard flow, visible-focus review, owner contrast acceptance, reduced-motion check |
| Responsive UI | Complete flow at viewport widths 360 and 1280 CSS pixels with no horizontal page overflow, including the unit choice beside the number | Browser visual review at both widths |

Performance latency, throughput and timing benchmarks are N/A by explicit owner decision. Public-service uptime targets are N/A for this local-only feature.

## 6.1 Security / privacy

- **Data classification:** confidential — originals may contain personal photos.
- **Personal data touched:** image contents and input metadata; no new identity fields or accounts.
- **AuthZ/AuthN impact:** none; local owner-operated application without accounts. Result isolation by absence of lookup or history.
- **Abuse cases:** a one-pixel or lowest-quality file that still meets the bound follows the success reset and can be used as if it were a useful result; an over-limit file is still auto-downloaded and can be treated as done; a tight bound on a large original can hold the only screen in a busy state with no cancel.
- **Security review:** N/A — no new authz boundary and no new PII; this increment extends existing local processing. Residual risk is owner-induced long encoding search and misread units.

## 7. Metrics / KPIs

Acceptance indicators rather than usage analytics; all targets are due before this feature is declared complete. Baseline for each is 0.

- Met-limit journey — target: automatic download and form reset with Результат bytes at most the Ліміт ваги on agreed JPEG, PNG and WebP controls.
- Miss journey — target: automatic download of the smallest file, form not reset, actual size and exceeded notice visible.
- Geometry — target: empty Ліміт ваги keeps 2400 by 1200 with max width 1200 at 1200 by 600; a smaller bound yields width under 1200 with preserved aspect ratio.
- Invalid Ліміт ваги — target: zero and negative values rejected while the Оригінал remains.

No analytics collection or timing measurement is added.

## 8. Open questions

None at the product-requirement level. D2 and the unit, miss and extra-shrink decisions are closed in this specification.

## Test plan

Optional Ліміт ваги on the existing one-form flow: empty bound keeps today's geometry; a supplied bound may shrink below maxima; a miss still downloads and keeps the form. Size S and route quick from `.size` / `.route`. Levels chosen in planning: unit, integration, contract, e2e-through-UI. No component, visual-regression or load suite.

### AC coverage

| AC (spec.md §5) | Test name (intent-based) | Level | Expected outcome |
|---|---|---|---|
| AC-01 | empty or omitted bound applies no result byte budget | contract | Existing dimension and format rules stay; no miss handling |
| AC-01 | empty Size limit on the form keeps today's success path | e2e-through-UI | Process with empty bound; one download then clean form; no extra shrink |
| AC-02 | Size limit accepts a positive decimal with Mb or Kb | e2e-through-UI | Unit selector sits right of the number; Mb selected initially; empty means no bound |
| AC-03 | size-limit-only JPEG is enough to process | contract | A supplied bound with no maxima and initial JPEG counts as a transformation parameter |
| AC-04 | empty bound keeps largest proportional fit | unit | 2400 by 1200 with only max width 1200 yields 1200 by 600; no extra reduction |
| AC-04 | empty bound encoded output matches that geometry | integration | Decoded result is 1200 by 600 |
| AC-05 | extra shrink stays proportional and inside the ceiling | unit | Width under 1200 at aspect 2 to 1; halves round up; minimum one pixel; no crop, stretch, enlarge, or format change |
| AC-05 | extra shrink meets the bound when attainable | integration | Encoded bytes are at most the bound; proportions and maxima still hold |
| AC-06 | met or omitted bound returns a fitting file | contract | Encoded bytes at most the bound when supplied; omitted bound sends the file without miss facts |
| AC-06 | met or omitted bound downloads once then resets | e2e-through-UI | One automatic download; file, preview, errors, miss facts, dimensions and Size limit clear; JPEG restored |
| AC-07 | unattainable bound still returns the smallest file | contract | A result is produced; caller is told the bound was exceeded and the actual size |
| AC-07 | unattainable bound downloads once and keeps the form | e2e-through-UI | One download; form not reset; actual size and exceeded notice shown; original and parameters remain |
| AC-08 | zero, negative or non-positive bound is rejected | contract | Attempt rejected; bound must be a positive number with Mb or Kb or left empty; no result |
| AC-08 | invalid Size limit is rejected and the original is kept | e2e-through-UI | Same explanation on the form; original remains so the owner can fix the field |
| AC-09 | application exposes no result lookup or history | contract | No retrieval capability; a lookup-style request discloses no image from another operation |
| AC-09 | reload restores neither input nor result | e2e-through-UI | Close or reload returns to the initial form with no history |
| AC-10 | new file selection resets bound and miss facts | e2e-through-UI | Preview, miss facts, errors, dimensions, format and Size limit reset; empty bound and JPEG |
| AC-10 | delayed work from an old selection never wins | e2e-through-UI | Old preview, old miss or extra download cannot replace the current selection |
| AC-11 | processing locks Size limit and shows a truthful busy state | e2e-through-UI | File selection and all transformation controls including Size limit disabled; no fabricated percentages |
| AC-11 | stale completion cannot download; failure restores retry | e2e-through-UI | Only the current operation may download; recoverable failure keeps file and parameters; after a miss, controls work again |
| AC-12 | Mb and Kb convert with decimal multipliers | unit | 0.5 Mb = 500000 bytes; 200 Kb = 200000 bytes |
| AC-12 | process request compares whole encoded bytes to that bound | contract | Comparison uses whole bytes of the encoded result after the same conversion |

### Edge cases / error paths

- missing unit with a filled bound → expected: rejected, no result
- non-numeric bound → expected: rejected, original kept
- processing failure → expected: retry restored, no download
- empty and omitted bound → expected: both mean no budget
- Size limit is not an upload cap → expected: selection still uses the existing file-byte limit
- one-pixel smallest file that still exceeds the bound → expected: miss with a file, not a rejection without a file
- new file after a miss → expected: new cycle; previous miss facts and bound do not remain

### Test data

- Seed strategy: synthetic images with known oriented sizes (including 2400 by 1200) plus existing repository fixtures where they already match; no personal photographs.
- Integration dependency: real codec and isolated temporary files in a disposable application runtime. No datastore, queue or cache exists; do not add a throwaway database.
- Cleanup boundary: per-test — close images, streams and generated files so runs stay independent. Per-suite — stop any created process and remove its temporary directory.

### NFR validation (load)

<!-- N/A: no numeric NFR -->

Performance latency, throughput and timing benchmarks are excluded by owner decision. Functional numbers in spec §6 (input caps, Mb/Kb arithmetic, 360 and 1280 CSS-pixel layout) are covered by the AC rows above, not by load.

### CI placement

- On every PR: unit, contract and bounded integration.
- On schedule / pre-release: e2e-through-UI journeys and recorded browser acceptance.
- Advice only; implementation and the repository CI own the wiring. Extend existing tests first.
