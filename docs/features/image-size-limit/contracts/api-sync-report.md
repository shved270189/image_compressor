# API sync report — image-size-limit

Date: 2026-09-13. Size: S. Route: quick, from `.size` and `.route`.
Contract: [openapi.yaml](./openapi.yaml), OpenAPI 3.1.0, initial version 0.1.0.
This extends the shipped process endpoint; extra-shrink and miss headers are
not implemented yet.

## Gate and inputs

`data-model.md` is absent — legal fast-lane skip (no schema change). sad.md §5
names no new building blocks or entities, no staged `docs/features/image-size-limit/migrations/`,
and spec.md introduces no new entity. Runtime flags state data-model is N/A.
Fields are derived from the **existing schema**: live `backend/main.py` multipart
parser and `ImageResponse`, [image-resize-convert openapi.yaml](../../image-resize-convert/contracts/openapi.yaml),
[image-resize-convert data-model.md](../../image-resize-convert/data-model.md)
transient rules, [architecture-map.md](../../../architecture-map.md) §Datastores /
§Conventions, plus this feature's spec §4/§5, sad.md §6/§8 and ADR 0002.

Found: `spec.md`, `sad.md` (`target_surfaces: [backend-service, web-frontend]`),
all five user-story sequences in §6, feature [CONTEXT.md](../CONTEXT.md).
Missing: `data-model.md` (legal skip), root `CONTEXT.md` (feature glossary used).
No `<message-bus>` / `<external-system>` / retry note — no `events.md`, no
Idempotency-Key. Interface kind: HTTP/REST from declared `backend-service`
(web-frontend consumes this contract; it does not author one).

English schema identifiers follow the shipped contract: `Original`, `Result` and
`MaximumDimension` map to Original, Result and Maximum dimensions;
`SizeLimit` and `SizeUnit` map to Size limit and its Mb/Kb unit.

## A. Field origins

| Schema path | Origin | Confidence |
|---|---|---|
| `processImage.request.file` | existing schema — `backend/main.py` `file` part; image-resize-convert data-model uploaded original; spec AC-01 | high |
| `processImage.request.max_width` | existing schema — `backend/main.py` `max_width`; spec AC-04, AC-05 | high |
| `processImage.request.max_height` | existing schema — `backend/main.py` `max_height`; spec AC-04, AC-05 | high |
| `processImage.request.output_format` | existing schema — `backend/main.py` `output_format`; spec AC-01, AC-03, AC-05 | high |
| `processImage.request.size_limit` | sad.md §8 Bound transport; spec AC-02, AC-03, AC-08, AC-12; feature ADR 0002 | high |
| `processImage.request.size_unit` | sad.md §8 `mb` or `kb`; spec AC-02, AC-12; feature ADR 0002 | high |
| `processImage.request` size_unit required when size_limit is positive | derived from AC-12 conversion needing the unit; SAD names both fields, not the missing-unit pairing | medium |
| `processImage.response.200.body` | existing schema — `ImageResponse` binary body; spec AC-06, AC-07; feature ADR 0002 | high |
| `processImage.response.200.Content-Type` | existing schema — `image/{jpeg,png,webp}` | high |
| `processImage.response.200.Content-Disposition` | existing schema — `result.jpg` / `result.png` / `result.webp` | high |
| `processImage.response.200.X-Result-Bytes` | sad.md §8 Miss facts; feature ADR 0002; spec AC-07, AC-12 | high |
| `processImage.response.200.X-Size-Limit-Met` | sad.md §8 Miss facts (`true` or `false`); feature ADR 0002; spec AC-06, AC-07 | high |
| `processImage.response.{400,413,415,422,500}.detail` (string) | existing schema — FastAPI `HTTPException` in `backend/main.py`; foundation ADR 0002 | high |
| `processImage.response.422.detail` (array) | existing image-resize-convert contract; FastAPI validation envelope, unused by the live manual parser | high |
| `processImage.response.422.detail[].loc` | same shipped validation schema | high |
| `processImage.response.422.detail[].msg` | same shipped validation schema | high |
| `processImage.response.422.detail[].type` | same shipped validation schema | high |
| `processImage.response.422.detail[].input` | same shipped validation schema | high |
| `processImage.response.422.detail[].ctx` | same shipped validation schema | high |

`PositiveSizeLimit`, `SizeLimit` and `SizeUnit` introduce no extra payload
fields beyond the two named multipart parts. `x-max-file-bytes` and
`x-max-decoded-pixels` remain documentation extensions. Multipart schemas
describe logical scalars; serialization uses text parts. Binary example strings
are placeholders, not real images.

## B. Drift findings

### Four-point structural check

| Check | Result | Evidence |
|---|---|---|
| Endpoint ↔ data model (core) | PASS with persistent-entity check N/A | One `processImage` reads the transient original and writes the transient result. No entities, IDs, columns or migrations exist. New `size_limit` / `size_unit` and miss headers are request-scoped, from sad.md §8. |
| Error code ↔ repository (core) | PASS with domain-code registry N/A | No error registry in the repo. Foundation ADR 0002 and sad.md §8 keep standard FastAPI `{detail: ...}` instead of the skill template `{code, message, details?}`. New 422 strings are the contract's proposal; reconcile when implemented. |
| Validation ↔ constraints (core) | PASS | Positive decimal size_limit, empty-as-absent, `mb`/`kb` enum, inclusive 20,000,000-byte / 40,000,000-pixel caps, existing dimension/format rules, and extra-shrink only while over the bound match spec AC-05, AC-08, AC-12 and sad.md §8. Stricter pairing: size_unit required when size_limit is positive. |
| OpenAPI ↔ sequences (supporting) | PASS with explicit UI/lifecycle boundaries | Server success/rejection branches map below. Miss is 200 with headers, not 4xx. UI-only branches do not manufacture HTTP operations. No async actor, so no Idempotency-Key. |

Inherited deviations, not new conflicts: no BearerAuth (spec §6.1, AC-09);
FastAPI detail envelope (foundation ADR 0002); no cursor pagination (no list);
URL `/api/v1/images/process` unchanged; binary success body with miss headers
instead of a JSON envelope (feature ADR 0002).

No unresolved core finding. Medium-confidence size_unit pairing is declared
incompleteness, not a pause. Zero flags requiring Accept / Fix / Save-as-OQ / Drop.

### Operation and branch coverage

`processImage` is the only operation. It implements US-02, supplies the file for
US-03 and US-04, accepts the bound from US-01, and rejects US-05. Setting the
control, download handoff, form reset/keep and file-selection reset are UI-only.

| SAD section 6 branch | Operation/response or non-HTTP boundary |
|---|---|
| Set optional Size limit — Bound empty | Request: omit or empty `size_limit`; 200 without miss headers; existing geometry |
| Set optional Size limit — Bound is a positive number | Request: positive `size_limit` + `size_unit`; counts as a transformation parameter (anyOf) |
| Set optional Size limit — Bound is zero, negative, or not a positive number | Continues through US-05 → 422 `invalidSizeLimit` |
| Set optional Size limit — User selects another file | UI-only; no extra operation |
| Shrink below dimension ceiling — Bound omitted | 200, no extra shrink, no miss headers; 2400×1200 width 1200 → 1200×600 |
| Shrink below dimension ceiling — Bound supplied and encoded bytes meet it | 200 with `X-Size-Limit-Met: true` and `X-Result-Bytes` |
| Shrink below dimension ceiling — Bound supplied and even one pixel exceeds it | 200 with `X-Size-Limit-Met: false` and `X-Result-Bytes`; not 4xx |
| Download when within limit — Completion is not the current operation | UI-only stale ignore |
| Download when within limit — Bound omitted or encoded bytes at most the bound | 200 as above; one download and clean form are client obligations |
| Download when within limit — Bound supplied and encoded bytes exceed it | Continues through US-04 |
| Download when within limit — User closes or reloads | UI-only; no history/lookup endpoint (AC-09) |
| Retry after a miss — Completion is not the current operation | UI-only stale ignore |
| Retry after a miss — Bound is met | Continues through US-03 |
| Retry after a miss — Bound still exceeded | 200 miss headers; keep-form and notice are client obligations |
| Retry after a miss — Recoverable failure | 400 / 413 / 415 / 422 / 500 as existing plus invalid bound |
| Retry after a miss — User changes settings and processes again | New `processImage` submission; no Idempotency-Key |
| Retry after a miss — User selects a new file / closes or reloads | UI-only |
| Correct an invalid Size limit — Bound is zero, negative, or not a positive number | 422; no result |
| Correct an invalid Size limit — Bound is empty or a positive number with Mb or Kb | Valid request; continues through US-01 submit |

Unsupported outer request media type remains 415. Sequence gap: none of the
§6 `alt` branches show an invalid `size_unit` or a positive `size_limit`
without `size_unit`. Those 422s are implied by sad.md §8 enum + AC-12, not a
missing authorization branch. Not filed as an upstream OQ: the contract does
not need a sequence the spec already constrains.

### Acceptance-criteria back-feed

Every AC maps to ≥1 operation/response or an explicit non-HTTP boundary.
`processImage` maps to US-01–US-05.

| AC | Contract coverage / explicit boundary |
|---|---|
| AC-01 | Empty `size_limit` applies no byte bound; 200 description keeps existing geometry |
| AC-02 | `size_limit` positive decimal + `size_unit` `mb`/`kb`; control placement is UI-only |
| AC-03 | anyOf includes positive `size_limit`; omitted format falls back to JPEG |
| AC-04 | 200 description: bound omitted, 2400×1200 width 1200 → 1200×600, no extra shrink |
| AC-05 | 200 description: extra-shrink rules, rounding, one-pixel miss continues as 200 |
| AC-06 | 200 omitted headers or `X-Size-Limit-Met: true`; download/reset are client obligations |
| AC-07 | 200 `X-Size-Limit-Met: false` + `X-Result-Bytes`; keep-form notice is UI-only |
| AC-08 | 422 `invalidSizeLimit`; no result |
| AC-09 | No lookup, history, retrieval or authentication interface |
| AC-10 | New-file reset is UI-only; stale completions must not consume this response |
| AC-11 | Recoverable 4xx/5xx; busy/lock/stale/retry/teardown are client obligations |
| AC-12 | Conversion constants and whole-byte comparison in the operation description |

## Validation evidence

The following check uses the existing Ruby YAML parser, installed FastAPI
OpenAPI model and the frontend's existing transitive Ajv dependency. Ajv checks
the JSON Schema keywords used here (a draft-07-compatible subset); this is not
a substitute for a complete OpenAPI 3.1 dialect validator. Binary format is an
annotation in this check, so illustrative binary placeholders are not decoded.

Result: OpenAPI model PASS; YAML PASS; 22 local references resolved; 26 examples
matched their declared shapes; 11 valid and 18 invalid logical requests behaved
as expected. Cases include size_limit-only JPEG eligibility, 0.5 mb / 200 kb,
empty size_limit with existing geometry, zero/negative size_limit (including
alongside jpeg), unsupported size_unit, and size_unit-only (not a parameter).
A positive size_limit without size_unit is schema-valid and still 422 at HTTP
(medium-confidence pairing). Inclusive byte/pixel limits are checked as
contract annotations, not exercised against real image uploads.

Reproduce from the repository root:

```sh
rtk proxy node <<'JS'
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const Ajv = require(require.resolve('ajv', { paths: ['./frontend'] }));
const file = 'docs/features/image-size-limit/contracts/openapi.yaml';
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
assert.deepEqual(doc.components.schemas.SizeUnit.enum, ['mb', 'kb']);
assert.equal(doc.components.schemas.PositiveSizeLimit.exclusiveMinimum, 0);
assert.ok(op.responses['200'].headers['X-Result-Bytes']);
assert.ok(op.responses['200'].headers['X-Size-Limit-Met']);
const request = ajv.compile({ $ref: 'contract#/components/schemas/ImageProcessingRequest' });
const valid = [
  { file: 'fixture', output_format: 'jpeg' },
  { file: 'fixture', max_width: 1200 },
  { file: 'fixture', max_height: 300 },
  { file: 'fixture', max_width: 1200, max_height: 300 },
  { file: 'fixture', max_width: '', max_height: '', output_format: 'webp' },
  { file: 'fixture', max_width: 1000000000000 },
  { file: 'fixture', size_limit: 0.5, size_unit: 'mb' },
  { file: 'fixture', size_limit: 200, size_unit: 'kb' },
  { file: 'fixture', output_format: 'jpeg', size_limit: '' },
  { file: 'fixture', max_width: 1200, output_format: 'jpeg', size_limit: 0.5, size_unit: 'mb' },
  { file: 'fixture', size_limit: 0.5 },
];
const invalid = [
  {}, { output_format: 'jpeg' }, { file: 'fixture' },
  { file: 'fixture', max_width: '', max_height: '' },
  ...[0, -1, 1.5, null, 'abc'].map(max_width => ({ file: 'fixture', max_width })),
  { file: 'fixture', max_height: 0, output_format: 'png' },
  ...['', 'gif', null].map(output_format => ({ file: 'fixture', output_format })),
  { file: 'fixture', size_limit: 0, size_unit: 'mb' },
  { file: 'fixture', size_limit: -1, size_unit: 'mb' },
  { file: 'fixture', output_format: 'jpeg', size_limit: 0 },
  { file: 'fixture', size_limit: 0.5, size_unit: 'gb' },
  { file: 'fixture', size_unit: 'mb' },
];
valid.forEach(value => assert(request(value), JSON.stringify(request.errors)));
invalid.forEach(value => assert.equal(request(value), false, JSON.stringify(value)));
let examples = 0;
for (const media of [
  ...Object.values(op.requestBody.content),
  ...Object.values(op.responses).flatMap(response => Object.values(response.content || {})),
]) {
  const schema = { ...media.schema, components: doc.components };
  if ('example' in media) { check(schema, media.example); examples++; }
  for (const example of Object.values(media.examples || {})) {
    check(schema, example.value); examples++;
  }
}
console.log(`YAML, ${refs} refs, ${examples} examples, ${valid.length} valid/${invalid.length} invalid logical requests: PASS`);
JS
```

Spectral is not installed or configured; no new dependency or check target is
added. Full Spectral lint and image, browser or container runtime verification
are not claimed by this stage. Build, pytest, Ruff and ESLint are not run for
these documentation-only changes.

## Handoff

Review [openapi.yaml](./openapi.yaml) and this report. Proposed commit:
`api: image-size-limit contract`.

Next: `/sdd:screens image-size-limit`. Declared `web-frontend` means the no-UI
skip to tasks does not apply.
