---
status: approved
feature_size: M
tool: code
updated_at: "2026-09-06"
---

# Screens — image-resize-convert

The canonical screen manifest for tasks, implement and review. Each UI task cites
SCR-01 and the applicable states below; downstream readers do not need a separate
design file. The owner approved this screen, its states and native controls at
medium depth. Size M and route standard come from `.size` and `.route`.

## Source

- **Tool:** code. `docs/design-system.md` is absent, so this is the explicit
  missing-canon fallback, not a Figma or Pencil export.
- **File:** inline wireframes below. Source-refs identify their headings; states
  sharing a layout explicitly share a wireframe.
- **Requirements:** [spec.md](./spec.md) §5–6, including the automatic-download
  amendment; [ux-flows.md](./ux-flows.md), including its single-screen inventory;
  [sad.md](./sad.md) §6; [OpenAPI](./contracts/openapi.yaml),
  `POST /api/v1/images/process` responses.
- **Reuse evidence:** `frontend/src/App.tsx` provides the main shell and product
  identity; `frontend/src/index.css` provides `canvas`, `ink`, `muted`, `accent`,
  the font stack and reduced-motion behavior. There is no component inventory to
  match against. Use the explicit native fallback inventory below; do not claim
  canonical design-system registration or introduce a component library.

### Native fallback inventory

These are HTML elements composed in the existing React screen, not new reusable
React components. The labels below are the exact component names used in the
state table.

| Name | Existing element or native composition |
|---|---|
| Shell | Existing `main`, product identity, heading and theme tokens |
| File input | Labeled native `input type="file"`, one file, native filename display |
| Dimension inputs | Two labeled optional native number inputs, positive whole pixels, no product upper bound |
| Format select | Labeled native `select` with JPEG, PNG and WebP |
| Process button | Native submit `button`; same action is available again after recovery |
| Preview | Native `img` with meaningful alt text; whole oriented image, contained without cropping |
| Notices | Native text paragraphs for limits, dimensions, JPEG transparency and HEIC behavior |
| Validation text | Native text associated with the affected field; form-level text when no field is identified |
| Status text | Native text with a polite live announcement for processing |
| Error text | Native alert text with a readable request, processing or transfer explanation |

## Screens

### SCR-01 — Image conversion

**Entry:** open or reload the application, or return after successful download
handoff. **Exit:** close the page; a native browser download leaves the user on
SCR-01. File picker and browser download UI are not application screens.

**Layout:** one centered column. Product identity and a concise heading precede
the optional Preview above the form. The form contains file selection, maximum
dimensions, output format, notices, feedback and the processing action. At
360 CSS pixels, dimension fields stack; at 1280 CSS pixels they sit side by side.
All content, including long filenames and errors, fits without horizontal page
overflow. Preview preserves the whole image and correct visible orientation.

| State | Trigger / condition and behavior | Components (native fallback inventory) | Source-ref |
|---|---|---|---|
| default | Initial entry or reload. No file or Preview; empty bounds and JPEG selected. Only file selection is enabled. No restoration. AC-01, AC-15–AC-16; SAD §6 US-01/US-04. | Shell, File input, Dimension inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form) |
| empty | Same visible form as default, including after successful handoff. Parameters remain visible but disabled; processing disabled. AC-01, AC-13. | Shell, File input, Dimension inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form) |
| ready | Non-empty file at most 20,000,000 bytes selected. Enable parameters and processing immediately; new selections reset bounds and JPEG. Preview may be visible, pending or unavailable; pending and failed Preview render no placeholder and never block submission. AC-01–AC-03, AC-07–AC-10; SAD §6 US-01/US-03. | Shell, File input, Dimension inputs, Format select, Process button, Preview (only when available), Notices | [WF-02](#wf-02--ready-form) |
| validation | Local selection or dimension rejection, or HTTP 413/415/422. Explain the reason using the mapping below. Local empty/oversized files have no Preview and cannot submit. Retain current input after server rejection and restore controls for correction or retry. AC-01, AC-11–AC-12, AC-15; SAD §6 US-02/US-05; contract 413/415/422. | Shell, File input, Dimension inputs, Format select, Process button, Preview (current eligible selection only), Notices, Validation text | [WF-03](#wf-03--validation) |
| loading | Processing submitted; upload, server work and receiving the complete response are one busy state. Disable file selection, both dimensions, format and repeat submission. Display Processing… without fabricated percentages or Cancel. AC-15; SAD §6 US-02–US-05. | Shell, File input, Dimension inputs, Format select, Process button, Preview (if available), Notices, Status text | [WF-04](#wf-04--processing) |
| error | HTTP 400/500, request failure or incomplete/failed response transfer. No download; show a safe readable explanation, retain current file, parameters and available Preview, restore controls. A user retry is a new submission. AC-15–AC-16; SAD §6 US-04/US-05; contract 400/500 and interruption description. | Shell, File input, Dimension inputs, Format select, Process button, Preview (if available), Notices, Error text | [WF-05](#wf-05--recoverable-error) |
| success | Complete successful response belongs to the current unconsumed operation. Initiate one native download, then reset to empty after handoff. N/A: separate success layout, result panel and repeat-download action are explicitly excluded. AC-13–AC-16; SAD §6 US-04; contract 200. | Shell, File input, Dimension inputs, Format select, Process button, Notices | [WF-01](#wf-01--initial-form), after handoff |

### Controls, notices and transitions

- **Selection:** every replacement invalidates previous Preview work and resets
  bounds and format, including invalid replacements. Reject zero bytes and more
  than 20,000,000 bytes before preparing Preview. Exactly 20,000,000 bytes is
  eligible. Keep file selection enabled after local rejection; parameter controls
  remain disabled until an eligible selection. Selection, editing and Preview
  never upload. Unsupported native Preview, including HEIC, disappears silently.
- **Parameters and notices:** use labels `Maximum width (px)`,
  `Maximum height (px)` and `Output format`. Empty bounds mean no bound; JPEG is
  selected on every selection and reset. State that resizing preserves the whole
  image without enlargement. With a selected file and JPEG, always show:
  `If this image has transparency, JPEG will replace it with white.` Show general
  HEIC guidance before submission without detecting content first:
  `HEIC: only the primary image is used; extra images are omitted. HDR becomes
  ordinary 8-bit output and may not retain its original appearance.` Explain
  supported static JPEG/PNG/WebP/HEIC inputs and the inclusive 20,000,000-byte and
  40,000,000-decoded-pixel limits. No quality, file-size target or smaller-file promise.
- **Recovery:** dimension validation keeps the file and all entered values for
  correction. Server rejections preserve the current selection and parameters;
  an available current Preview may remain even when server content is rejected.
  The restored Process image action permits retry once local input is eligible.
  Field errors are corrected in place; a replacement file follows the full
  selection reset. Do not automatically retry or restore an earlier result.
- **Completion:** wait for the complete binary result and ignore stale or duplicate
  completions without downloading or changing the form. Use the contract's
  matching attachment filename: `result.jpg`, `result.png` or `result.webp`.
  After one browser handoff, clear the selected File, native file input, Preview,
  errors and result; empty bounds and select JPEG. The same file can be selected
  again. No result dimensions, format, size, history or manual download control
  remain. Reset does not wait for disk-save confirmation. Release obsolete Preview
  immediately; download URL cleanup must not interrupt the initiated download.
- **Accessibility and motion:** use native labels and keyboard controls, visible
  focus, field associations for errors and `aria-invalid` where applicable.
  Announce validation/errors accessibly and expose the form's busy state with
  `aria-busy` and Status text. After successful reset, return focus to file
  selection. Preserve readable contrast for the owner's manual review. Motion
  must not delay interaction/download, cause layout jumps or fabricate progress;
  reduced motion removes decorative animation without losing functionality.

### Validation and error mapping

Messages below specify explanations, not stable server text or domain error
codes. The contract uses HTTP statuses and either a string `detail` or a 422
validation array. Associate known `loc` fields (`file`, `max_width`, `max_height`,
`output_format`) with controls and present readable `msg` text. Show string detail
and unmapped validation at form level. Never branch on exact message wording or
depend on validation order. Do not render raw `input`, `ctx`, exception objects
or JSON dumps. If no readable error body is available, show a general failure
message; incomplete transfer remains an error even after an initial HTTP 200.

| Source | Explanation and recovery | State |
|---|---|---|
| Local zero bytes or file above 20,000,000 bytes | File is empty or exceeds the byte limit; choose another file. No Preview or submission. | validation |
| Local non-positive or fractional dimension | Enter a positive whole pixel count, or leave the field empty. Preserve input for correction. | validation |
| HTTP 413 | File exceeds 20,000,000 bytes or selected static image exceeds 40,000,000 decoded pixels; explain the reported limit. Equality is accepted. | validation |
| HTTP 415 | Unsupported request media type or actual image content; explain the returned rejection. Filename or declared MIME type does not prove support. | validation |
| HTTP 422 | Missing file or all parameters, invalid dimensions/output, empty/corrupted/animated input. Explain the returned reason and retain input. Direct-request-only cases do not add UI controls. | validation |
| HTTP 400 | Malformed multipart request; show a readable request failure and permit retry. | error |
| HTTP 500 | Processing failed; show a safe explanation and permit retry. | error |
| Failed request or incomplete transfer | Result could not be received; retain input and permit retry without downloading partial output. An interruption may have no error body. | error |

The browser supplies JPEG, so both blank dimensions are valid. The API's omitted
format fallback and missing-all-parameters rejection remain boundary behaviors,
not additional form modes. HEIC static extra images are not animation. Closing
or reloading returns to default without restoring input or results; it does not
create another error screen. Backend geometry, color and metadata properties
(AC-04–AC-10) are verified in the downloaded file, not a UI result panel.

### WF-01 — Initial form

Shared by default, empty and success after download handoff. `[disabled]` describes
control state; it is not UI copy. Initial and invalid-selection forms keep the
parameter controls visible but disabled.

```text
Image compressor
Resize and convert an image

Original image       [Choose file] No file chosen
Static JPEG, PNG, WebP or HEIC
Up to 20,000,000 bytes and 40,000,000 decoded pixels

Maximum width (px)    Maximum height (px)
[empty, disabled]    [empty, disabled]
Leave either limit empty for no bound. No enlargement.
Output format        [JPEG v, disabled]
HEIC: primary image only; extra images omitted.
HDR becomes ordinary 8-bit output; appearance may change.

[Process image, disabled]
```

### WF-02 — Ready form

The Preview region exists only after a successful current native-image load.
Pending, unsupported and failed Preview use this same layout with the entire
region omitted. JPEG notice is absent for PNG/WebP; HEIC guidance remains.

```text
Image compressor
Resize and convert an image

+------------------------------------------+
| Optional whole, correctly oriented image |
+------------------------------------------+

Original image       [Choose file] selected.png
Supported static formats and input limits
Maximum width (px)    Maximum height (px)
[1200            ]   [empty           ]
Leave either limit empty for no bound. No enlargement.
Output format        [JPEG v]
If this image has transparency, JPEG will replace it with white.
HEIC: primary image only; extra images omitted.
HDR becomes ordinary 8-bit output; appearance may change.

[Process image]
```

### WF-03 — Validation

Local invalid selection uses WF-01 with the rejected filename, an associated
file error and no Preview; file selection stays enabled. Parameter validation
and server rejection use WF-02 with current input retained. These are variants
of one validation state, not new screens.

```text
Local file rejection                  Parameter correction
Original image                        [Current Preview, if available]
[Choose file] empty.png                Original image [Choose file] selected.png
Input file is empty.                  Maximum width (px)
[Parameters disabled]                 [0]
[Process image, disabled]             Enter a positive whole pixel count,
                                      or leave this field empty.
                                      [Remaining form values retained]
```

Server rejection without a field location appears directly above the Process
image action. The action is available after controls are restored and local
validation permits submission; no replacement file is required merely to retry.

### WF-04 — Processing

Use WF-02 with all current values and available Preview preserved. Disable file
selection and every parameter control; the button cannot submit again. Status
text is the single busy announcement, not a numeric progress indicator.

```text
[Current Preview, if available]
Original image       [Choose file, disabled] selected.png
Maximum width (px)    Maximum height (px)
[1200, disabled]     [empty, disabled]
Output format        [JPEG v, disabled]
[Current notices]
Processing…
[Process image, disabled]
```

### WF-05 — Recoverable error

Use WF-02 with controls restored and current input retained. This layout also
shows form-level server validation, using Validation text instead of Error text.

```text
[Current Preview, if available]
Original image       [Choose file] selected.png
Maximum width (px)    Maximum height (px)
[1200            ]   [empty           ]
Output format        [JPEG v]
[Current notices]
Image processing failed. Please try again.
[Process image]
```

All wireframes describe the same responsive form. At 360 CSS pixels, stack width
and height and wrap notices/errors; at 1280 CSS pixels, align dimensions in two
columns. Error and busy variants retain the form structure and current values.

## New components

None. Compose the existing Shell and native fallback inventory above in the
existing screen. No new component registration is claimed: the canonical design
system is absent. Recommend `/sdd:design-system` separately; creating it is not
part of this manifest change.

## Verification and readiness

The owner confirmed SCR-01 without changes or deferred screen decisions. Review
the implementation against every state and variant, including exact byte-limit
eligibility, unavailable Preview, replacement with invalid input, retained input
after failure, one complete download, same-file reselection, stale completion
suppression and clean reload. Check the full keyboard journey, visible focus,
owner-approved readable contrast, reduced motion and no horizontal overflow at
360 and 1280 CSS pixels. These are acceptance scenarios, not claims of runtime
tests performed by this documentation stage.

Structural self-check covers the sole SCR inventory entry, complete states with
sources, component reuse through the explicit native fallback, and inline
wireframe references. Canonical design-system inventory matching is N/A because
that file is absent; native fallback verification must not be described as
canonical inventory registration.

**Pre-tasks gates remain open.** SAD §11 requires Tech Lead evidence for HEIC and
color behavior on macOS/Linux and for upload/decoder/output cleanup plus safe
automatic download handoff across the agreed browser matrix. This manifest does
not resolve either gate or authorize an arbitrary URL-revocation delay. Before
running `/sdd:tasks image-resize-convert`, close both gates. Once closed, start a
fresh context with `/clear`, then run that tasks stage using this manifest.
