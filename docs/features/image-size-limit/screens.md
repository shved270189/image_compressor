---
status: approved
feature_size: S
tool: code
updated_at: "2026-09-13"
---

# Screens — image-size-limit

The canonical screen manifest for tasks, implement and review. Each UI task cites
SCR-01 and the applicable states below; downstream readers do not need a separate
design file. The owner approved this screen, its states and native controls at
medium depth. Size S and route quick come from `.size` and `.route`.

## Source

- **Tool:** code. `docs/design-system.md` is absent, so this is the explicit
  missing-canon fallback, not a Figma or Pencil export. Named degradation:
  no design-system canon and no Figma/Pencil MCP target; wireframes are inline.
- **File:** inline wireframes below. Source-refs identify their headings; states
  sharing a layout explicitly share a wireframe.
- **Requirements:** [spec.md](./spec.md) §5–6; [ux-flows.md](./ux-flows.md)
  single-screen inventory; [sad.md](./sad.md) §6 branches; [OpenAPI](./contracts/openapi.yaml)
  `POST /api/v1/images/process` responses and headers.
- **Reuse evidence:** `frontend/src/App.tsx` is the closest screen. Extend its
  parameter fieldset; do not add a second page. `frontend/src/index.css` provides
  `canvas`, `ink`, `muted`, `accent`, `surface`, `line`, `danger` and reduced-motion
  behavior. There is no component inventory to match against. Use the native
  fallback inventory below; do not claim canonical design-system registration.

### Native fallback inventory

These are HTML elements composed in the existing React screen, not new reusable
React components. The labels below are the exact component names used in the
state table.

| Name | Existing element or native composition |
|---|---|
| Shell | Existing `main`, product identity, heading and theme tokens |
| File input | Labeled native `input type="file"`, one file, native filename display |
| Dimension inputs | Two labeled optional native number inputs, positive whole pixels, no product upper bound |
| Size limit inputs | Labeled optional native number input for a positive decimal, with a native `select` of `Mb` / `Kb` placed to the right of the number; `Mb` selected initially; empty allowed |
| Format select | Labeled native `select` with JPEG, PNG and WebP |
| Process button | Native submit `button`; same action is available again after recovery or miss |
| Preview | Native `img` with meaningful alt text; whole oriented image, contained without cropping |
| Notices | Native text paragraphs for limits, dimensions, JPEG transparency and HEIC behavior |
| Validation text | Native text associated with the affected field; form-level text when no field is identified |
| Status text | Native text with a polite live announcement for processing |
| Error text | Native alert text with a readable request, processing or transfer explanation |
| Miss notice | Native status text showing the actual result size in whole bytes and that the size limit was exceeded; not Error text |

## Screens

### SCR-01 — Image processing

**Entry:** open or reload the application, or return after a met-limit or
omitted-bound download handoff. **Exit:** close the page; a native browser
download leaves the user on SCR-01. File picker and browser download UI are not
application screens. There is no history, lookup or retrieve screen (AC-09).

**Layout:** existing two-column page at 1280 CSS pixels (intro + form); one
column at 360. Product identity and heading precede the optional Preview above
the form. The form contains file selection, maximum dimensions, Ліміт ваги
(unit selector right of the number), output format, notices, feedback and Process
image. At 360 CSS pixels, dimension fields stack; the unit selector stays to the
right of the number with no horizontal page overflow. Preview
preserves the whole image and correct visible orientation.

| State | Trigger / condition and behavior | Components (native fallback inventory) | Source-ref |
|---|---|---|---|
| default | Initial entry or reload. No file or Preview; empty dimensions; empty Ліміт ваги; unit Mb; JPEG selected. Only file selection is enabled. No restoration. AC-01, AC-02, AC-09; SAD §6 US-01; ux-flows S1_READY. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form) |
| empty | Same visible form as default, including after a met-limit or omitted-bound handoff. Parameters remain visible but disabled; processing disabled. AC-06; SAD §6 S3_CLEAN. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form) |
| ready | Eligible file selected. Enable dimensions, Ліміт ваги, format and processing immediately. Empty bound means no result byte bound. A supplied positive bound with only the initial JPEG is enough to process. New selections reset dimensions, bound, unit to Mb, JPEG, errors and miss facts. Preview may be visible, pending or unavailable; pending and failed Preview render no placeholder and never block submission. AC-01–AC-03, AC-10; SAD §6 S1_ALLOWED / S1_RESET. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Preview (only when available), Notices | [WF-02](#wf-02--ready-form) |
| validation | Local file, dimension or Ліміт ваги rejection, or HTTP 413/415/422. Explain the reason using the mapping below. Invalid bound copy: Ліміт ваги must be a positive number with Mb or Kb or left empty. No Результат. Keep the Оригінал so the owner can correct or clear the field. AC-08; SAD §6 US-05; contract 413/415/422 including `invalidSizeLimit`, `missingSizeUnit`, `invalidSizeUnit`. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Preview (current eligible selection only), Notices, Validation text | [WF-03](#wf-03--validation) |
| loading | Processing submitted. Disable file selection and all transformation controls including Ліміт ваги. Display Processing… without fabricated percentages or Cancel. A new process replaces previous miss facts. AC-11; SAD §6 S4_WAIT. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Preview (if available), Notices, Status text | [WF-04](#wf-04--processing) |
| error | HTTP 400/500, request failure or incomplete transfer. No download. Show a safe readable explanation, retain current file, parameters, bound, unit and available Preview, restore controls. A retry is a new submission. AC-11; SAD §6 recoverable failure; contract 400/500. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Preview (if available), Notices, Error text | [WF-05](#wf-05--recoverable-error) |
| success | Complete 200 belongs to the current operation and the bound was omitted or `X-Size-Limit-Met: true`. Initiate one automatic download, then reset to empty after handoff. N/A: separate success layout, result panel and repeat-download action are excluded. AC-06; SAD §6 US-03; contract 200 with omitted headers or `X-Size-Limit-Met: true`. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form), after handoff |
| miss | Complete 200 belongs to the current operation and `X-Size-Limit-Met: false`. Initiate one automatic download; do not reset. Keep the Оригінал and parameters. Show Miss notice: `The result is {N} bytes. The size limit was exceeded.` `{N}` is `X-Result-Bytes` in whole bytes. Controls usable for retry. Notice remains until the next process, a new file selection or page close. AC-07, AC-11; SAD §6 US-04; contract 200 miss headers. | Shell, File input, Dimension inputs, Size limit inputs, Format select, Process button, Preview (if available), Notices, Miss notice | [WF-06](#wf-06--miss) |

### Controls, notices and transitions

- **Selection:** every replacement invalidates previous Preview work and resets
  dimensions, format, Ліміт ваги (empty), unit to Mb, errors and miss facts,
  including invalid replacements. Reject zero bytes and more than 20,000,000
  bytes before preparing Preview. Exactly 20,000,000 bytes is eligible. Ліміт
  ваги is not an upload cap. Keep file selection enabled after local rejection;
  parameter controls remain disabled until an eligible selection.
- **Ліміт ваги:** visible label `Size limit` with optional. Native `select` of
  `Mb` and `Kb` sits to the right of the number. `Mb` is selected initially and
  after every reset. Empty remains allowed and means no bound. A positive
  decimal is accepted; zero, negative or otherwise non-positive values are
  rejected locally before submit, matching existing dimension checks. There is
  no product upper bound on the entered number. Unit without a filled number is
  ignored; a filled number always has a unit because the selector always has a value.
- **Parameters and notices:** reuse existing dimension and format copy from the
  current form. JPEG transparency and HEIC guidance stay as they are. Do not
  promise a smaller file when the bound is empty.
- **Busy and concurrency:** at most one submitted operation. File selection and
  every transformation control including Ліміт ваги are disabled while
  processing. Ignore stale completions: no download, no form change, no miss
  facts from an old operation.
- **Completion:** wait for the complete binary result. Use the contract
  attachment filename. When `size_limit` was omitted or empty, omit miss
  handling and reset after one download. When it was supplied, read
  `X-Result-Bytes` and `X-Size-Limit-Met`. Met (`true`) follows success. Miss
  (`false`) follows miss. Reset does not wait for disk-save confirmation.
  Download URL cleanup must not interrupt the initiated download.
- **Accessibility and motion:** native labels, keyboard access and visible
  focus for the number and the unit selector. Associate validation with
  `size_limit` / `size_unit` when `loc` names them. Announce miss with a polite
  live region, not `role="alert"`. Expose busy with `aria-busy` and Status
  text. After successful reset, return focus to file selection. Readable
  contrast for labels, errors and the exceeded notice is owner-reviewed.
  Reduced motion removes decorative animation without losing functionality.

### Validation and error mapping

Messages specify explanations, not stable server text. Associate known `loc`
fields (`file`, `max_width`, `max_height`, `output_format`, `size_limit`,
`size_unit`) with controls. Show string detail and unmapped validation at form
level. Never branch on exact message wording.

| Source | Explanation and recovery | State |
|---|---|---|
| Local zero bytes or file above 20,000,000 bytes | File is empty or exceeds the byte limit; choose another file. No Preview or submission. | validation |
| Local non-positive or fractional dimension | Enter a positive whole pixel count, or leave the field empty. Preserve input for correction. | validation |
| Local zero, negative or non-positive Ліміт ваги | Ліміт ваги must be a positive number with Mb or Kb or left empty. Keep the Оригінал. | validation |
| HTTP 413 | File exceeds 20,000,000 bytes or selected static image exceeds 40,000,000 decoded pixels. Ліміт ваги is not this cap. | validation |
| HTTP 415 | Unsupported request media type or actual image content. | validation |
| HTTP 422 | Missing file or all parameters, invalid dimensions/output, empty/corrupted/animated input, invalid `size_limit` or `size_unit`. Explain the returned reason; keep the Оригінал. | validation |
| HTTP 400 | Malformed multipart request; show a readable request failure and permit retry. | error |
| HTTP 500 | Processing failed; show a safe explanation and permit retry. | error |
| Failed request or incomplete transfer | Result could not be received; retain input and permit retry without downloading partial output. | error |

A miss is HTTP 200 with `X-Size-Limit-Met: false`, not a row in this table.
Closing or reloading returns to default without restoring input, miss facts or
results. Backend geometry and byte arithmetic (AC-04, AC-05, AC-12) are
verified in the downloaded file, not a result panel.

### WF-01 — Initial form

Shared by default, empty and success after download handoff. `[disabled]`
describes control state; it is not UI copy.

```text
Image compressor.
One image. A better fit.

Resize & convert
Make room. Keep the picture.

Choose an image
[Choose file] No file chosen
A preview appears when your browser supports the image.

Maximum dimensions · optional
Width (px)              Height (px)
[empty, disabled]      [empty, disabled]
Leave either blank to keep it unconstrained.

Size limit · optional
[empty, disabled]  [Mb v, disabled]
Leave empty for no result size bound.

Output format            [JPEG v, disabled]
HEIC: only the primary image is used; extra images are omitted.
HDR becomes ordinary 8-bit output and may not retain its original appearance.

[Process image, disabled]
Your result downloads automatically.
```

### WF-02 — Ready form

The Preview region exists only after a successful current native-image load.
Pending, unsupported and failed Preview omit the entire region. JPEG notice is
absent for PNG/WebP; HEIC guidance remains.

```text
+------------------------------------------+
| Optional whole, correctly oriented image |
+------------------------------------------+

Choose an image
[Choose file] selected.png

Maximum dimensions · optional
Width (px)              Height (px)
[1200              ]   [empty             ]

Size limit · optional
[0.5            ]  [Mb v]
Leave empty for no result size bound.

Output format            [JPEG v]
If the image has transparency, JPEG turns it white.
HEIC: only the primary image is used; extra images are omitted.
HDR becomes ordinary 8-bit output and may not retain its original appearance.

[Process image]
Your result downloads automatically.
```

At 360 CSS pixels the unit selector stays immediately right of the number. If the
row wraps, wrap the group together:

```text
Size limit · optional
[0.5                   ]  [Mb v]
```

### WF-03 — Validation

Local invalid selection uses WF-01 with the rejected filename, an associated
file error and no Preview. Bound and dimension validation keep the current
file. These are variants of one validation state, not new screens.

```text
Local bound rejection                 Local file rejection
[Current Preview, if available]       Choose an image
Choose an image                       [Choose file] empty.png
[Choose file] selected.png            Choose a non-empty image.
Size limit · optional                 [Parameters disabled]
[0]  [Mb v]                           [Process image, disabled]
Ліміт ваги must be a positive
number with Mb or Kb or left empty.
[Remaining form values retained]
[Process image]
```

Server 422 without a field location appears at form level above Process image.
`loc` of `size_limit` or `size_unit` associates with Size limit inputs.

### WF-04 — Processing

Use WF-02 with current values and available Preview preserved. Disable file
selection and every parameter control including Ліміт ваги. Hide previous miss
facts. Status text is the single busy announcement.

```text
[Current Preview, if available]
Choose an image          [Choose file, disabled] selected.png
Width (px)               Height (px)
[1200, disabled]        [empty, disabled]
Size limit · optional
[0.5, disabled]  [Mb v, disabled]
Output format            [JPEG v, disabled]
[Current notices]
[Process image, disabled] Processing…
Processing your image…
```

### WF-05 — Recoverable error

Use WF-02 with controls restored and current input retained, including Ліміт
ваги and unit.

```text
[Current Preview, if available]
Choose an image          [Choose file] selected.png
Width (px)               Height (px)
[1200              ]    [empty             ]
Size limit · optional
[0.5            ]  [Mb v]
Output format            [JPEG v]
[Current notices]
Processing failed. Please try again.
[Process image]
```

### WF-06 — Miss

Use WF-02 after one automatic download. Do not reset. Show Miss notice with
whole encoded bytes from `X-Result-Bytes`. Controls are usable.

```text
[Current Preview, if available]
Choose an image          [Choose file] selected.png
Width (px)               Height (px)
[1200              ]    [empty             ]
Size limit · optional
[0.5            ]  [Mb v]
Output format            [JPEG v]
[Current notices]
The result is 612,344 bytes. The size limit was exceeded.
[Process image]
Your result downloads automatically.
```

All wireframes describe the same responsive form. At 360 CSS pixels, stack
width and height, keep the unit selector right of the number, and wrap notices without
horizontal page overflow. At 1280 CSS pixels, keep dimensions in two columns
and the unit selector in one row with the number.

## New components

None — all screens compose the existing native fallback inventory. Size limit
inputs and Miss notice are native HTML in the existing screen, not new React
primitives. Canonical design-system registration is N/A because
`docs/design-system.md` is absent. Recommend `/sdd:design-system` separately;
creating it is not part of this manifest.

## Verification and readiness

The owner confirmed SCR-01 without changes. Review the implementation against
every state, including empty bound, bound-plus-JPEG-only submit, invalid bound
kept original, loading lock of Ліміт ваги, miss keep-form with actual bytes,
met-limit reset that also clears bound and miss facts, new-file reset to Mb,
stale completion suppression and clean reload. Check the keyboard journey for
number and the unit selector, visible focus, owner-approved contrast for the
exceeded notice, reduced motion and no horizontal overflow at 360 and 1280 CSS
pixels.
