# API sync report — image-resize-convert

Date: 2026-09-06. Size: M. Route: standard, from `.size` and `.route`.
Contract: [openapi.yaml](./openapi.yaml), OpenAPI 3.1.0, initial version 0.1.0.
This is a planned interface, not an implemented or runtime-verified endpoint.

## A. Field origins

Inputs found: [data-model.md](../data-model.md), [spec.md](../spec.md),
[SAD](../sad.md) with `target_surfaces: [web-frontend, backend-service]` and all
five user-story sequences in section 6, and [feature glossary](../CONTEXT.md).
There is no root glossary or existing feature contract to reconcile.

The data model explicitly declares no persistent entities or schema change.
Fields derive from its transient input rules, spec ACs and SAD flows, not invented
database columns. Column/entity checks are N/A under the accepted no-storage
architecture. `medium` denotes an explicit non-persistent product field;
`high` denotes a directly verified framework shape or specified wire convention.
No field has a sequence-only, low-confidence origin. English schema identifiers
follow the owner's identifier rule; `Original`, `Result` and `MaximumDimension`
map to the glossary's Оригінал, Результат and Максимальні розміри respectively.

| Schema path | Origin | Confidence |
|---|---|---|
| `processImage.request.file` | Data model, Entities: uploaded original and input boundary; spec AC-07, AC-10–AC-12; SAD US-05 | medium |
| `processImage.request.max_width` | Data model, Entities: independently optional positive whole pixel bounds; spec AC-04–AC-06, AC-11 | medium |
| `processImage.request.max_height` | Same input rule; spec AC-04 height-only and combined examples, AC-05–AC-06, AC-11 | medium |
| `processImage.request.output_format` | Data model input boundary; spec AC-07, AC-11 and section 1: JPEG/PNG/WebP, browser JPEG default and conditional omission fallback | medium |
| `processImage.response.200.body` | Data model encoded result; SAD US-03/US-04; accepted feature ADR 0004: complete binary result in this response | medium |
| `processImage.response.200.Content-Type` | Spec AC-07, AC-13: effective output format; API mapping to `image/jpeg`, `image/png`, `image/webp` | medium |
| `processImage.response.200.Content-Disposition` | Spec AC-13 matching extension; accepted implementation plan selects fixed `result.jpg`, `result.png`, `result.webp` attachment names | high |
| `processImage.response.{400,413,415,422,500}.detail` (string) | Foundation ADR 0002 standard FastAPI HTTP errors; installed `fastapi.exception_handlers.http_exception_handler`; SAD US-05 failure branches | high |
| `processImage.response.422.detail` (array) | Installed `fastapi.exception_handlers.request_validation_exception_handler` and `fastapi.openapi.utils.validation_error_response_definition` | high |
| `processImage.response.422.detail[].loc` | Installed `fastapi.openapi.utils.validation_error_definition`: array of string/integer location elements | high |
| `processImage.response.422.detail[].msg` | Same definition: required string | high |
| `processImage.response.422.detail[].type` | Same definition: required string; framework validation type, not a new domain-code registry | high |
| `processImage.response.422.detail[].input` | Same definition: optional unconstrained input; spec section 6.1 limits it to safe non-image parameter data | high |
| `processImage.response.422.detail[].ctx` | Same definition: optional object; spec section 6.1 excludes identifying data and internal exception details | high |

`PositiveDimension` and `MaximumDimension` share the two dimension fields' origin;
`OutputFormat`, `Original` and `Result` introduce no additional payload fields.
The `x-max-file-bytes` and `x-max-decoded-pixels` annotations copy the input limits;
they are documentation extensions, not request fields or executable validators.
The multipart schema describes logical scalar values; serialization uses text
parts. Binary example strings explicitly denote placeholder file contents, not
real images, base64 payloads or valid decoder fixtures.

## B. Drift findings

### Four-point structural check

| Check | Result | Evidence |
|---|---|---|
| Endpoint ↔ data model (core) | PASS with persistent-entity check N/A | One request transforms the transient original into the transient result. No entities, IDs, columns or migrations exist by data-model Entities, foundation ADR 0003 and feature ADR 0004. The owner approved derivation from transient rules and ACs. |
| Error code ↔ repository (core) | PASS with domain-code registry N/A | Existing foundation has no domain error definitions. The owner explicitly retained standard FastAPI `{detail: ...}` instead of template `{code, message, details?}`. Validation shapes match installed framework definitions. No proposed domain codes are presented as implemented. |
| Validation ↔ constraints (core) | PASS | Positive independent bounds, empty-as-absent, three output choices, conditional JPEG fallback, one required file and inclusive 20,000,000-byte/40,000,000-pixel limits match data-model Entities and AC-11–AC-12. No invented dimension maximum or file-size target. |
| OpenAPI ↔ sequences (supporting) | PASS with explicit UI/lifecycle boundaries | All server success/rejection branches map below; UI-only branches and interrupted connections do not manufacture HTTP operations or responses. SAD retry is explicitly a new user submission, not server replay. |

The owner confirmed the error-format deviation during planning on 2026-09-06.
[Foundation ADR 0002](../../../adr/0002-single-service-and-kamal.md) and SAD section
8 take precedence over the generic skill envelope. Authentication is absent by
spec section 6.1, AC-14 and SAD section 8; both document and operation declare
`security: []`, without an unused BearerAuth scheme or invented 401/403 responses.
The `/api/v1` path follows the skill's URL-versioning convention and the approved
plan; existing `/api/health`, static serving and API 404 behavior remain outside
this feature contract and unchanged.

No list endpoint, pagination, Preview upload, result lookup, events document,
callback, queue or Idempotency-Key is introduced. Browser facilities are internal
to the UI, not async application actors. The pipeline makes one request; the
US-02 and US-03 sequences are views of the same operation.

### Operation and branch coverage

`processImage` implements US-02 and US-03, supplies the result for US-04 and
provides the server outcomes for US-05. US-01 is browser-only selection and
Preview; no separate operation belongs to it.

| SAD section 6 branch | Operation/response or non-HTTP boundary |
|---|---|
| Overview accepted input; US-02 reduced or unchanged dimensions; US-03 JPEG or PNG/WebP; HEIC primary/HDR handling | `processImage` 200, description and binary media alternatives |
| US-05 malformed multipart / parser failure while a response is possible | 400; bounded parsing and partial-upload cleanup in operation description |
| US-05 missing file/parameters, invalid bounds or unsupported output | 422, string or structured validation detail; omission rules in request schema |
| US-05 empty, corrupted or animated original | 422, with separate illustrative explanations |
| US-05 actual unsupported content | 415; filename and supplied MIME type do not determine image support |
| US-05 initial or rechecked byte/pixel limit failure | 413, inclusive boundaries preserved |
| US-03/US-05 decoding, color, transformation or encoding failure | Input-attributable failures use 413/415/422 above; internal processing failures use 500 |
| US-01 local eligibility, optional Preview success/failure and replacement; US-02 local invalid-bound branch; US-03 pre-submit notices | UI-only; operation description explicitly forbids Preview uploads and the report retains these AC obligations |
| US-04 stale/consumed completion, full download handoff/reset, next selection | Client currentness and resource ownership; no extra status or request |
| US-04 transfer failure; US-05 interruption during parsing, native work or response | No guaranteed HTTP response after disconnect or partial transfer; no successful result; resource ownership continues until safe release |
| US-05 form caller versus direct caller, retained input and user retry | Same operation and response shapes; UI restoration is client-only, retry creates a new request |

Unsupported outer request media type maps to 415 at the declared multipart
boundary, within US-05's parsing/input validation stage. It does not introduce a
new product capability or an authorization branch. When multiple invalid inputs
coexist, the contract does not promise which rejection is reported first.

### Acceptance-criteria back-feed

Every AC is accounted for; a UI-only AC maps to an explicit non-HTTP boundary
rather than a fabricated operation. These mappings assert contract coverage,
not passing image-processing or browser tests.

| AC | Contract coverage / explicit boundary |
|---|---|
| AC-01 | `Original` byte allowance and 413/422 server checks; initial controls and immediate selection eligibility are UI-only |
| AC-02 | No Preview operation; local correctly oriented Preview or silent omission is UI-only |
| AC-03 | Operation description limits consumption to current work; selection reset, stale Preview and duplicate suppression are UI-only |
| AC-04 | 200 description includes width-only, height-only and combined exact geometry |
| AC-05 | 200 description: largest fitting scale, no enlargement, halves-up rounding, minimum one pixel; 1000x333 becomes 500x167 |
| AC-06 | Positive bounds without an invented maximum; ineffective bounds and same-format normalization accepted |
| AC-07 | Four actual static input formats, three output media types, JPEG default/fallback, no size or byte-identity guarantee |
| AC-08 | JPEG white compositing and PNG/WebP alpha preservation; conditional pre-submit JPEG warning is UI-only |
| AC-09 | Orientation before bounds, compatible color handling and identifying metadata removal; Preview orientation is UI-only |
| AC-10 | HEIC designated primary image, omitted extra images, ordinary 8-bit HDR output; general pre-submit notice is UI-only |
| AC-11 | Required file, request `anyOf`, positive-or-empty dimensions, output enum, conditional fallback; 422 examples |
| AC-12 | Actual-content validation and 413/415/422 branches, inclusive limits, pre-decode checks and post-decode recheck |
| AC-13 | Complete 200 binary response and matching attachment extension; single automatic download and safe clean-form reset are client obligations |
| AC-14 | No persistent ID, lookup, retrieval or history interface; caller receives only its own response; no authentication invented |
| AC-15 | Recoverable errors and incomplete transfers provide no successful result; busy state, retained input, retry and teardown are client obligations |
| AC-16 | Operation description requires partial-upload, native-work and response cleanup; browser selection/handoff ownership remains client-only |

No unresolved contract/source mismatch or new upstream open question is retained.
The existing HEIC/color and resource/download feasibility gates in SAD section 11
remain open before `sdd:tasks`; this contract does not close them. The separate
security review remains due before implementation acceptance.

### Validation evidence

The following check passed using the existing Ruby YAML parser, installed FastAPI
OpenAPI model and the frontend's existing transitive Ajv dependency. Ajv checks
the JSON Schema keywords used here (a draft-07-compatible subset); this is not
a substitute for a complete OpenAPI 3.1 dialect validator. Binary format is an
annotation in this check, so illustrative binary placeholders are not decoded.

Result: OpenAPI model PASS; YAML PASS; 18 local references resolved; 19 examples
matched their declared shapes; 6 valid and 13 invalid logical requests behaved
as expected. Cases include dimensions-only JPEG eligibility, absent/all-empty
parameters, zero/negative/fractional/null bounds, unsupported/empty output,
missing file and an ineffective large dimension. Inclusive byte/pixel limits
are checked as contract annotations, not exercised against real image uploads.

Reproduce from the repository root:

```sh
rtk proxy node <<'JS'
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const Ajv = require(require.resolve('ajv', { paths: ['./frontend'] }));
const file = 'docs/features/image-resize-convert/contracts/openapi.yaml';
const doc = JSON.parse(execFileSync('ruby', ['-rjson', '-ryaml', '-e',
  'puts JSON.generate(YAML.safe_load_file(ARGV.fetch(0)))', file], { encoding: 'utf8' }));
execFileSync('.venv/bin/python', ['-c',
  'import sys; from fastapi.openapi.models import OpenAPI; OpenAPI.model_validate_json(sys.stdin.read()); print("OpenAPI model: PASS")'],
  { input: JSON.stringify(doc), stdio: ['pipe', 'inherit', 'inherit'] });
const ajv = new Ajv({ allErrors: true });
ajv.addFormat('binary', () => true);
ajv.addSchema(doc, 'contract');
const check = (schema, value) => {
  const validate = ajv.compile(schema);
  assert(validate(value), JSON.stringify(validate.errors));
};
let refs = 0;
function walk(value) {
  if (!value || typeof value !== 'object') return;
  if (value.$ref) {
    assert(value.$ref.startsWith('#/'));
    assert(value.$ref.slice(2).split('/').reduce((node, key) =>
      node[key.replace(/~1/g, '/').replace(/~0/g, '~')], doc) !== undefined);
    refs++;
  }
  Object.values(value).forEach(walk);
}
walk(doc);
assert.equal(doc.openapi, '3.1.0');
assert.deepEqual(Object.keys(doc.paths), ['/api/v1/images/process']);
const op = doc.paths['/api/v1/images/process'].post;
assert.deepEqual(op.security, []);
assert.deepEqual(Object.keys(op.responses).sort(), ['200', '400', '413', '415', '422', '500']);
const origin = doc.components.schemas.Original;
assert.equal(origin['x-max-file-bytes'], 20000000);
assert.equal(origin['x-max-decoded-pixels'], 40000000);
assert.deepEqual(doc.components.schemas.OutputFormat.enum, ['jpeg', 'png', 'webp']);
assert(!('default' in doc.components.schemas.OutputFormat));
const request = ajv.compile({ $ref: 'contract#/components/schemas/ImageProcessingRequest' });
const valid = [
  { file: 'fixture', output_format: 'jpeg' },
  { file: 'fixture', max_width: 1200 },
  { file: 'fixture', max_height: 300 },
  { file: 'fixture', max_width: 1200, max_height: 300 },
  { file: 'fixture', max_width: '', max_height: '', output_format: 'webp' },
  { file: 'fixture', max_width: 1000000000000 },
];
const invalid = [
  {}, { output_format: 'jpeg' }, { file: 'fixture' },
  { file: 'fixture', max_width: '', max_height: '' },
  ...[0, -1, 1.5, null, 'abc'].map(max_width => ({ file: 'fixture', max_width })),
  { file: 'fixture', max_height: 0, output_format: 'png' },
  ...['', 'gif', null].map(output_format => ({ file: 'fixture', output_format })),
];
valid.forEach(value => assert(request(value), JSON.stringify(request.errors)));
invalid.forEach(value => assert.equal(request(value), false, JSON.stringify(value)));
let examples = 0;
for (const media of [
  ...Object.values(op.requestBody.content),
  ...Object.values(op.responses).flatMap(response => Object.values(response.content)),
]) {
  const schema = { ...media.schema, components: doc.components };
  if ('example' in media) { check(schema, media.example); examples++; }
  for (const example of Object.values(media.examples || {})) {
    check(schema, example.value); examples++;
  }
}
console.log(`YAML, ${refs} refs, ${examples} examples, ${valid.length} valid/${invalid.length} invalid logical requests: PASS`);
console.log('Binary placeholders are illustrative; file bytes, decoding and HTTP runtime are not tested.');
JS
```

Document checks also verify local Markdown links, AC-01–AC-16 coverage, trailing
whitespace and the exact two-file scope. `rtk git diff --check` passed; because
new files are initially untracked, direct whitespace checks cover them too.

Spectral is not installed or configured in this repository; no new dependency,
check target or test infrastructure is added. Full Spectral lint and image,
browser or container runtime verification are not claimed by this stage.
Build, pytest, Ruff and ESLint are not run for these documentation-only changes.

## Handoff

Review [openapi.yaml](./openapi.yaml) and this report. Proposed commit:
`docs: define image resize conversion API contract`.

Next: `/sdd:screens image-resize-convert`, after a fresh context. The declared
web frontend means the no-UI skip to tasks does not apply. Resolve both existing
pre-tasks feasibility gates before proceeding to `sdd:tasks`.
