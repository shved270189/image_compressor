# Image compressor

Resize, convert and optionally compress one static JPEG, PNG, WebP or HEIC
image to JPEG, PNG or WebP. FastAPI serves `POST /api/v1/images/process` and
the built React frontend.

## Image workflow

1. Select a non-empty image up to 20,000,000 bytes. Preview stays local and is
   optional when the browser cannot display the format. Choosing another file
   resets dimensions, Size limit, format, errors and miss facts.
2. Optionally set maximum width and height, an optional Size limit, and an
   output format (JPEG by default). Size limit is a positive decimal with a
   native Mb/Kb select to the right of the number (Mb initially; empty means
   no result byte bound). Width, height and Size limit are independent; any
   supplied constraint is enough to process, including Size limit alone.
   Empty dimensions impose no bound. Images never enlarge, crop or stretch.
   A supplied Size limit is the primary constraint: encoding may shrink below
   those maxima and below the original until the file fits. 1 Mb = 1,000,000
   bytes; 1 Kb = 1,000 bytes; 0.5 Mb is 500,000 bytes. Size limit is not the
   20,000,000-byte upload cap.
3. Process the image. File selection and transformation controls stay locked
   until the complete response arrives, with a truthful busy state and no
   fabricated percentages. When Size limit is omitted or met, one result
   downloads automatically and the form clears. When the bound cannot be met,
   the smallest chosen-format file still downloads, the form stays, and the
   page shows the actual size plus that the limit was exceeded so you can
   change settings and retry. Zero, negative or non-positive Size limit is
   rejected locally; the selected image is kept.

The server also enforces 40,000,000 decoded pixels, including equality. Dimensions
must be positive whole pixel counts. Output sides above WebP's 16,383 or JPEG's
65,500 pixel limit produce an explanatory error: reduce a bound and retry.
There is no automatic extra reduction to those codec limits.

JPEG composites transparency onto white; PNG and WebP preserve alpha. Orientation
is applied before removing EXIF, GPS, camera and textual metadata. Compatible
color interpretation is preserved. HEIC uses the primary static image, omits extra
images and converts HDR to ordinary 8-bit output. Animated inputs are rejected.
Results are not guaranteed smaller or byte-identical, including same-format conversion.

Errors retain the current selection and settings for an explicit retry. Successful
download handoff or page closure releases browser resources. Closing or reloading
restores neither input nor result. The server retains no original or result for
later retrieval; upload spools and image buffers are operation-scoped. Native work
already running may finish before cleanup.

The contract is [OpenAPI](docs/features/image-size-limit/contracts/openapi.yaml).
Optional fields are `max_width`, `max_height`, `size_limit`, `size_unit` (`mb` or
`kb`) and `output_format`. A supplied Size limit adds `X-Result-Bytes` and
`X-Size-Limit-Met` on the 200 response. Multipart transport also limits the body
to 20,065,536 bytes, cumulative part header names/values to 16,384 bytes and each
text field to 1,024 bytes.

Implementation checks are recorded in the [task tracker](docs/features/image-size-limit/tasks/tracker.md).
Size limit, miss keep-form and 360/1280 checks are in
[image-size-limit browser acceptance](docs/features/image-size-limit/_audit/browser-acceptance.md).
The owner confirmed download/reset in iOS and desktop Safari/Firefox and accepted
phone/desktop readability. Independent Security Lead technical review passed.
Firefox/WebKit engine checks and native Safari server-error retry passed. The
owner also confirmed real iPhone Safari network-failure/retry and form reset.

## Local development

Install and activate [mise](https://mise.jdx.dev/getting-started.html) in your shell.
Run all commands from the repository root. `mise.toml` pins Python, Node.js, uv and
Ruby. uv uses mise's Python and manages the root `.venv`.

```sh
mise trust
mise install
mise run setup
mise run dev
```

The owner runs setup to install locked Python, frontend and Kamal dependencies in
sequence. A failure stops the remaining installs. Dev does not run setup.

Open <http://localhost:5173>. Vite proxies `/api` to <http://127.0.0.1:8000>.
Backend reload and frontend HMR are enabled. One Ctrl+C stops both servers and
their children. mise can report an interrupted task as an error on Ctrl+C.

## Checks

Build first: the smoke test checks real HTML/assets, health, image conversion and API 404s.

```sh
npm --prefix frontend run build
uv run pytest
uv run ruff check .
npm --prefix frontend run lint
bundle check
bundle exec kamal version
```

To serve the build directly, run `uv run uvicorn backend.main:app --port 8000` and
open <http://127.0.0.1:8000>. The API starts without a frontend build. Restart the
backend after creating the first build so it registers frontend serving.

## Container

With a Docker engine running:

```sh
docker build -t image-compressor:smoke .
docker run --rm --name image-compressor-smoke -p 127.0.0.1:8000:8000 image-compressor:smoke
```

In a second terminal, run:

```sh
SMOKE_BASE_URL=http://127.0.0.1:8000 uv run pytest
```

The image runs as UID 10001 on port 8000 without reload. It contains locked runtime
dependencies and built assets; Node.js, Ruby, uv and test tools stay outside the
runtime image. GitHub Actions runs the checks and the same container smoke test.

## Scope and decisions

See [architecture map](docs/architecture-map.md), [ADRs](docs/adr/), and
[scaffold evidence](docs/features/_scaffold/tasks.json).

There is no database or migration tool; migration checks are N/A. Kamal lives in
`Gemfile` and runs through `bundle exec kamal`. The later publish command is
exactly:

```sh
bundle exec kamal deploy
```

Do not run that command until you are ready to publish. It is not a
Configuration check; local checks stay `uv run pytest`. The recipe is
`config/deploy.yml`. The proxy target is port 8000 and health path
`/api/health`.
