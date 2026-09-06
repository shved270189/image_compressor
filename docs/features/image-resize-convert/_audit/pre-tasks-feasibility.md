# Pre-tasks feasibility — image-resize-convert

Date: 2026-09-06. Size M, route standard. Owner: Tech Lead.

**Readiness: READY FOR TASKS.** Both pre-tasks mechanism gates in [SAD §11](../sad.md#11-risks-and-technical-debt) are closed. This audit verifies mechanisms before
implementation planning. It does not claim a completed feature or complete
acceptance coverage. No production endpoint, dependency manifest, lockfile,
public API or task breakdown changed. Probes are reproducible experiments,
not production implementations to copy wholesale.

| Area | Recorded outcome | Implementation obligation |
|---|---|---|
| HEIC/color, macOS and Linux | 9 PASS per platform, exit 0: matching ICC synthesis and HDR-to-SDR transformation | Complete supported color/decoder coverage |
| HEIF animation, macOS and Linux | 21 PASS per platform: real sequence, static collection, spoofed brands and analytic timing controls | Complete presentation-timeline handling; unresolved probe cases are not production classifications |
| Server resources, macOS and Linux | 24 PASS and 2 asserted baseline GAP per platform; exit 0 | Integrate guarded parsing and worker-owned cleanup into the real route |
| Desktop Chrome, Safari and Firefox | Complete native downloads after reset and immediate URL release | Full feature acceptance across browsers |
| iOS Safari, Chrome and Firefox | Owner-reported download PASS in all three release modes: nine combinations | No additional owner check required for this feasibility stage; Android deferred |

## Reproducible artifacts and environment

| Artifact | Purpose |
|---|---|
| [feasibility-images.py](./feasibility-images.py) | Pinned public fixtures, matching ICC synthesis and HDR conversion |
| [feasibility-animation.py](./feasibility-animation.py) | Bounded container/timing inspection with explicit unresolved cases |
| [feasibility-resources.py](./feasibility-resources.py) | Framework-free parser, worker, response and real socket ownership probes |
| [feasibility-download.py](./feasibility-download.py) + [HTML](./feasibility-download.html) | Synthetic local response and browser handoff candidates; selected files never uploaded |
| [feasibility-browser.js](./feasibility-browser.js) | Chrome checks through the existing Playwright CLI; no project test framework |

Host: macOS 26.6.2 arm64, Python 3.14.6. Container: Linux 7.0.14-orbstack
aarch64, glibc 2.36, Python 3.14.6. Existing foundation image:
`image-compressor:smoke`, ID
`sha256:633581cdcdea12213de329b4f7aad839e63d253085a7810c5000ca7dbef7709a`.
The Linux probes use temporary environments or a read-only package overlay;
they do not rebuild or mutate that image.

Image packages: Pillow 12.3.0, pillow-heif 1.6.0, libheif 1.23.2,
libde265 1.1.1, x265 4.2+1-e444744. Resource packages: FastAPI 0.141.1,
Starlette 1.6.0, Pillow 12.3.0, python-multipart 0.0.22, AnyIO 4.15.1,
Uvicorn 0.52.4. Public fixtures and generated probe downloads live outside the
repository; URLs and SHA-256 pins are embedded in the image script and its JSON.

## HEIC and color evidence

| Case | Evidence and limits |
|---|---|
| Primary image | `zPug_3.heic` opens on index 1 of 3; one PNG exports only that primary image. Expected index comes from the pinned upstream test. |
| Animation | Frame count and MIME alone fail. Container/timing inspection detects real starfield even after removal of all sequence brands; allows the non-first-primary static collection and analytic empty/dwell edit galleries. General edit/composition/fragment timelines remain explicitly unresolved in this diagnostic. |
| Bit depth / alpha | 10/12-bit controls decode to 8-bit RGB/RGBA. Disabling auxiliary/depth/thumbnail loading retains primary alpha. PNG/WebP lossless pixels match; analytic partial/full transparency composites onto white for JPEG. |
| Orientation / ICC | Plugin applies orientation 6 once; `exif_transpose` is then inert. Compatible Display P3 ICC survives JPEG/PNG/WebP; EXIF/XMP/text are absent. Lossless output pixels match. A neutral Lab-white control converts to RGB white with a matching RGB profile. Arbitrary CMYK/gray coverage is not claimed. |
| Independent orientation | Apple ImageIO through `sips` decodes the pinned arrow independently. Explicit clockwise orientation gives matching 3024×4032 geometry, mean absolute RGB differences `[0.80231, 0.61710, 0.69410]` on a 0–255 scale, on both platforms. |
| NCLX without ICC | Tested SDR primaries=1/transfer=13. Synthesizing ICC from actual chromaticities and the matching transfer curve preserves interpretation in JPEG/PNG/WebP; lossless output pixels remain unchanged. |
| PNG without ICC | Independent gAMA=1/cHRM RGB128 control retains equivalent ICC and unchanged pixels in every output; independently expected sRGB display value 188 matches within one code value. |
| Real HLG | Public BT.2020 HLG HEIC decodes to 8-bit RGB. ImageCms transforms the decoded samples to SDR with the same BT.2020 primaries and a matching output ICC in all three formats. |
| Transfer controls | Analytic HLG/PQ neutral and red samples match independently calculated anchors within one 8-bit code value. This is not a photographed PQ fixture or a promise to preserve HDR appearance. |

The verified color route uses LittleCMS already bundled with Pillow: create an
RGB ICC from primaries/white point and gamma or sampled transfer curves, then
use normal ImageCms transforms when required. The probe accesses exported
LittleCMS functions through `ctypes` and Pillow's `_imagingcms` extension.
This binding is version/platform-sensitive; pin and verify the implementation
builds. No additional color-engine dependency is introduced by this experiment.
HLG inverse OETF and normalized PQ EOTF map the full source range into SDR;
the output keeps source primaries with an SDR transfer curve. HLG is scene-relative
inverse OETF, not a display OOTF; PQ is EOTF normalized by 10,000 cd/m².
Transfer equations follow [BT.2100](https://www.itu.int/rec/r-rec-bt.2100). This deliberately
does not promise original HDR display appearance or universal sRGB conversion.
The discarded metadata-clearing path lost NCLX/gAMA/HLG interpretation.

Animation is determined from visual-track presentation, not image count or
brands. The bounded probe proves the mechanism and exposes its coverage limit:
`NEEDS_TIMELINE` must never silently become either static or animated in the
feature. Implementation must handle edit lists, composition offsets and
fragmented timing, preserve non-timed galleries with zero/one presentation
samples, and reject genuine sequences. See
[Nokia's technical description](https://nokiatech.github.io/heif/technical.html) and its pinned [presentation-count rule](https://github.com/nokiatech/heif/blob/503194eb85e13434b54797bab9d82ad7f88fd35b/srcs/reader/heifreaderimpl.cpp#L2099).
Before acceptance, add edit-list/composition/fragmented controls and a complete
independently generated non-timed track gallery; the current analytic gallery
controls are timing structures, not decodable camera files. This is required
implementation work, not a new product/design decision.

Reproduce timing checks after fetching image fixtures:

```sh
rtk proxy python docs/features/image-resize-convert/_audit/feasibility-animation.py --fixtures /tmp/image-feasibility-fixtures
rtk proxy docker run --rm -v "$PWD/docs/features/image-resize-convert/_audit/feasibility-animation.py:/probe.py:ro" -v /tmp/image-feasibility-fixtures:/fixtures:ro --entrypoint python image-compressor:smoke /probe.py --fixtures /fixtures
```

Expected primary/orientation facts are documented in the
[pinned upstream tests](https://github.com/bigcat88/pillow_heif/blob/11a2a9f2e0259f0a5594e1e5df1afbe7b9204cce/tests/read_test.py).
The [plugin source](https://github.com/bigcat88/pillow_heif/blob/11a2a9f2e0259f0a5594e1e5df1afbe7b9204cce/pillow_heif/as_plugin.py)
and [MIME implementation](https://github.com/bigcat88/pillow_heif/blob/11a2a9f2e0259f0a5594e1e5df1afbe7b9204cce/pillow_heif/misc.py)
explain the tested behavior. [Nokia's examples](https://nokiatech.github.io/heif/examples.html)
independently classify starfield as an image sequence. The HLG
[producer and encoder](https://github.com/certiday/LUMIX2HLG/tree/00bd2e4457220df012ec530c4f0d2e59bfc5cfba)
declare BT.2020 HLG; raw NCLX bytes independently confirm `(9,18,9,128)`.
HLG fixture SHA-256: `75481b8fa596cedcdc782f593d946624c34a96196c02eb1ee4abaab8db45175e`.

Run from the repository root. The first image command downloads fixtures and
exits 1 only because the independent orientation reference is not supplied yet.
The final host/container commands supply that reference.

```sh
rtk proxy uv venv --python 3.14 /tmp/image-feasibility-venv
rtk proxy uv pip install --python /tmp/image-feasibility-venv/bin/python Pillow==12.3.0 pillow-heif==1.6.0
rtk proxy /tmp/image-feasibility-venv/bin/python docs/features/image-resize-convert/_audit/feasibility-images.py --fixtures /tmp/image-feasibility-fixtures
rtk proxy mkdir -p /tmp/image-feasibility-extra
rtk proxy sips -s format png /tmp/image-feasibility-fixtures/arrow.heic --out /tmp/image-feasibility-extra/arrow-native.png
rtk proxy /tmp/image-feasibility-venv/bin/python docs/features/image-resize-convert/_audit/feasibility-images.py --fixtures /tmp/image-feasibility-fixtures --orientation-reference /tmp/image-feasibility-extra/arrow-native.png
rtk proxy docker run --rm -v "$PWD/docs/features/image-resize-convert/_audit/feasibility-images.py:/probe.py:ro" -v /tmp/image-feasibility-fixtures:/fixtures:ro -v /tmp/image-feasibility-extra/arrow-native.png:/arrow-native.png:ro image-compressor:smoke sh -c '/usr/local/bin/python -m venv /tmp/probe-env && /tmp/probe-env/bin/python -m pip install --quiet Pillow==12.3.0 pillow-heif==1.6.0 && /tmp/probe-env/bin/python /probe.py --fixtures /fixtures --orientation-reference /arrow-native.png'
```

Both final image runs exit 0: 9 PASS each, bundled LittleCMS 2.19. Independent native PNG hash
for this run: `5a89ac8a4e46db45db464b02123c7c579dedbc9cbcd8055645c63c05e674e46a`.
Apple encoder versions may change PNG bytes; the pixel comparison is the oracle.

## Server ownership evidence

| Probe | Result |
|---|---|
| Stock partial multipart exception/disconnect/cancellation | PASS: partial spools close on exceptions. |
| Stock truncated normal EOF | CONFIRMED GAP: missing closing boundary returns incomplete FormData with an open partial spool. The probe closes it afterward. `python-multipart` finalize is a no-op in this version. |
| Guarded multipart | PASS: completion flag rejects truncated normal EOF; cleanup closes partial handles. Actual 20,000,000 file bytes pass; 20,000,001 fail before decoding. Closed descriptor checked with `os.fstat`. |
| Pixel boundary | PASS of a mechanism: actual Pillow PPM header + `load` spy permits exactly 40M and rejects 40M+1 before loading. No full 40M decode or supported-format matrix is claimed. |
| UploadFile → Pillow → response | PASS: success, decoder failure, encoder failure, ASGI send failure and cancellation close upload storage and release image/intermediate/output/response owners. Assertions use closed handles and weak references, not RSS. |
| AnyIO scope cancellation | PASS: `abandon_on_cancel=False` retains ownership until the synchronous worker completes. |
| Direct `asyncio.Task.cancel()` | CONFIRMED GAP: AnyIO alone allows caller cleanup before worker completion. Worker-owned `with source:` cleanup retains the resource until actual work ends, then closes it; PASS. No custom shield is required. |
| Actual loopback sockets | PASS: FastAPI/Uvicorn interrupted multipart closes its spool; disconnect during Pillow worker execution retains the source until actual completion and releases all owners; disconnect during a streaming response releases its output owner. |

The candidate uses version-sensitive Starlette internals and an explicit parser
completion flag. It caps actual file bytes at 20,000,000 before spooling/decoding.
Verified transport budgets: 20,065,536 total body bytes, 16,384 cumulative header
name/value bytes, one file, three scalars and 1,024 bytes per scalar. An exact
20 MB file plus all three valid scalars passes, including a 1,024-digit bound.
These budgets constrain wire representation, not the numeric dimension value.
They are probe settings; the implementation contract must explicitly document
transport limits and error mapping before exposing them. This audit changes no
public API and does not invent a product maximum dimension.

Ownership transfers to the synchronous worker before processing; an async
FormData context must not close that source while the worker still uses it.
Actual Pillow work, raw cancellation and socket interruption are exercised.
Full HEIC route integration, post-decode dimension validation and confidential
error/log behavior remain implementation acceptance obligations. The pixel
boundary probe uses a real PPM header and load spy, not a full 40M-pixel decode.
Observation deadlines are test controls, not production retention timers.

```sh
rtk proxy uv run --no-project --python 3.14 --with fastapi==0.141.1 --with starlette==1.6.0 --with pillow==12.3.0 --with python-multipart==0.0.22 --with anyio==4.15.1 --with uvicorn==0.52.4 python docs/features/image-resize-convert/_audit/feasibility-resources.py
```

For the recorded Linux run, `/tmp/image-resource-multipart` contains only the
extracted official `python_multipart-0.0.22-py3-none-any.whl`, SHA-256
`2b2cd894c83d21bf49d702499531c7bafd057d730c201782048f7945d82de155`.
To recreate the overlay, download that wheel from the URL listed by
[PyPI release metadata](https://pypi.org/pypi/python-multipart/0.0.22/json), check
the digest, and extract with Python `zipfile` into that temporary directory.

```sh
rtk proxy docker run --rm -v "$PWD/docs/features/image-resize-convert/_audit/feasibility-resources.py:/tmp/probe.py:ro" -v /tmp/image-resource-multipart:/tmp/packages:ro -e PYTHONPATH=/tmp/packages --entrypoint python image-compressor:smoke /tmp/probe.py
```

Both commands exit 0: 24 PASS plus 2 expected, asserted baseline GAP records.
Exit 0 means the experiment reproduced its findings, not that production is ready.

## Browser handoff evidence

The server returns a deterministic synthetic 1024×1024 RGB PNG, 3,147,775 bytes,
SHA-256 `241fe05d25615a6afdb954061604845e765efa521b6c213d2345426f0a063115`.
It accepts only empty synthetic POSTs and serves only the probe and fixture.
It does not resize/convert the selected file. Retained server fixture bytes are
test data, not evidence about production server cleanup.

The page waits for the complete response Blob, consumes the current operation
once, clicks a native download link and resets the form. Candidates: immediate
revocation after click; MessageChannel task revocation; explicit retention as a
positive control only. No production release timeout is chosen.

The [File API revocation rules](https://w3c.github.io/FileAPI/#dfn-revokeObjectURL)
allow already-started requests to succeed after revocation. The
[HTML download algorithm](https://html.spec.whatwg.org/multipage/links.html#downloading-resources)
starts a fetch and defines automation download hooks. Those hooks are not a
page-visible disk-save event. **Inference from these sources and observations:**
immediate revocation after native link click is the verified release boundary
for the tested desktop versions, supplemented by the owner-reported iOS smoke.
Neither a MessageChannel callback nor a successful click alone proves download
handoff across the required browser matrix.

| Browser / method | Observed artifacts and coverage |
|---|---|
| Installed Chrome 152.0.7977.82, Playwright CLI | Final 55 assertions PASS; seven main-page downloads plus one download completing after actual page closure. Two same-file conversions for each release mode; filename/operation-bound byte comparison and browser decoding; HTTP 500 and truncated-response recovery; busy duplicate submit suppression; a newly observed invalidated completion; reload during pending work; zero active object URLs after handoff/cleanup and pagehide. Download bytes also checked externally with Pillow and SHA-256. |
| Installed Safari 26.6.2, native UI | `probe-immediate-2.png`, `probe-task-4.png`, delayed `probe-immediate-mtpzobf6-2.png`; complete PNG bytes, SHA-256 and Pillow decode verified. Empty form observed after each completion; delayed operation locks controls. Safari WebDriver was disabled, so native UI was used without changing its automation setting. |
| Installed Firefox 155.0.1, native UI | `probe-immediate-2(1).png`, `probe-task-4.png`, delayed `probe-immediate-mtpzqm44-2.png`; native Downloads shows Completed, form Empty; byte/hash/decode verified. The initial task filename collided with Safari's; subsequent probe filenames include a per-page run ID. |
| iOS Safari, Chrome and Firefox | Owner reports successful downloads in all three release modes in each browser: immediate, MessageChannel task and retain control. This is owner-reported download PASS for nine browser/mode combinations. Exact versions, operation filenames, local PNG verification and additional lifecycle scenarios were not reported. |
| Android Chrome | DEFERRED by the owner on 2026-09-06 because no Android device is available. Excluded from the current gate; no Android compatibility result is claimed. |

Desktop Safari/Firefox error, stale-completion, same-native-file and closure
scenarios remain feature acceptance work. Chrome additionally proves that a
handed-off download completes after actual page closure. The diagnostic's
pagehide dispatch checks URL cleanup independently. Diagnostic invalidation
lets an old fetch finish to exercise stale completion; it is not production
cancellation policy. No cross-version universal browser guarantee is claimed.

Start the server from the repository root; default binding is loopback. The
second form is for the agreed phone checks on the same private Wi-Fi.

```sh
rtk proxy python docs/features/image-resize-convert/_audit/feasibility-download.py
rtk proxy python docs/features/image-resize-convert/_audit/feasibility-download.py --bind 0.0.0.0
```

Run only one server. During this session it listens at
`http://192.168.201.228:8765`; the address may change. Selected images remain on
the browser. The server logs no requests and exposes no repository directory.

Reproduce Chrome automation with the server running. The existing CLI wrapper
is an agent tool outside the project's npm dependencies. Prepare the synthetic
input and run from `/tmp` to keep CLI downloads and logs outside the repository:

```sh
rtk proxy python - <<'PY'
import hashlib
import subprocess
import urllib.request
from pathlib import Path

audit = Path('docs/features/image-resize-convert/_audit').resolve()
work = Path('/tmp/image-download-feasibility')
work.mkdir(exist_ok=True)
data = urllib.request.urlopen('http://127.0.0.1:8765/fixture.png').read()
assert hashlib.sha256(data).hexdigest() == '241fe05d25615a6afdb954061604845e765efa521b6c213d2345426f0a063115'
(work / 'chrome-immediate.png').write_bytes(data)
cli = str(Path.home() / '.codex/skills/playwright/scripts/playwright_cli.sh')
subprocess.run([cli, '-s=download-chrome', 'open', 'http://127.0.0.1:8765', '--browser', 'chrome', '--headed'], cwd=work, check=True)
subprocess.run([cli, '-s=download-chrome', 'snapshot'], cwd=work, check=True)
subprocess.run([cli, '-s=download-chrome', 'run-code', (audit / 'feasibility-browser.js').read_text()], cwd=work, check=True)
PY
```

## Owner device checks and closure criteria

**Owner update — 2026-09-06.** The owner confirms successful downloads on iOS
Safari, Chrome and Firefox with all three release modes in each browser.
The download smoke is recorded as owner-reported PASS for those nine
combinations. This does not infer a local PNG verification result, additional
lifecycle coverage or an Android result. OS/browser versions were not supplied.

**Owner scope update — 2026-09-06.** Android verification is deferred because
the owner has no Android device. It is not a prerequisite for the current
pre-tasks gate. Other evidence requirements remain in effect.

No further owner device check is required before tasks. Full implemented-flow
acceptance remains required by SAD §10; these synthetic checks are mechanism
proof, not a claim that the application already processes images.

## Verification and review

Final checks passed (exit 0):

- `rtk proxy uv run ruff check .`
- `rtk proxy npm --prefix frontend run lint`
- `rtk proxy node --check docs/features/image-resize-convert/_audit/feasibility-browser.js`
- `rtk git diff --check`

Both platforms pass color (9), timing (21), and resource (24 plus two asserted
baseline gaps) probes. Chrome passes 55 assertions with seven main-page downloads
and one completing after page closure. HTML inline JavaScript parses; touched
file whitespace and local audit links pass direct checks.

Independent review checked LittleCMS C signatures and ownership, HDR equations,
and the distinction between timing mechanism proof and complete production
validation. Native profile-allocation/save failure injection verifies cleanup.
Self-review corrected stale readiness/counts, clarified the tested NCLX transfer
and HDR policy, and retained every unverified implementation obligation. Earlier
review also fixed operation-unbound browser verification and a stale-event wait
that could match an earlier replay. No unresolved review finding remains.

No application build or foundation smoke run is presented as feature evidence.
The main application remains its unchanged foundation. No commit or tracker
message was created. The owner requested a `/clear` reminder before `sdd:tasks`;
no task breakdown is generated in this session.
