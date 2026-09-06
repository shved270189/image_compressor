# Image compressor

Resize and convert one static JPEG, PNG, WebP or HEIC image to JPEG, PNG or WebP.
FastAPI serves the processing endpoint and built React frontend.

## Image workflow

1. Select a non-empty image up to 20,000,000 bytes. Preview stays local and is
   optional when the browser cannot display the format.
2. Optionally set maximum width and height, and choose an output format (JPEG by
   default). Empty dimensions impose no bound; images never enlarge or crop.
3. Process the image. Controls stay locked until the complete response arrives.
   One result downloads automatically; the form clears for the next image.

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
download handoff or page closure releases browser resources. The server retains
no original or result for later retrieval; upload spools and image buffers are
operation-scoped. Native work already running may finish before cleanup.

The contract is [OpenAPI](docs/features/image-resize-convert/contracts/openapi.yaml).
Multipart transport also limits the body to 20,065,536 bytes, cumulative part
header names/values to 16,384 bytes and each text field to 1,024 bytes.

Implementation checks are recorded in the [task tracker](docs/features/image-resize-convert/tasks/tracker.md).
The owner confirmed download/reset in iOS and desktop Safari/Firefox and accepted
phone/desktop readability. Independent Security Lead technical review passed.
Firefox/WebKit engine checks and native Safari server-error retry passed; final
real iPhone network-failure/retry acceptance remains open.

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
`Gemfile` and runs through `bundle exec kamal`. Server addresses, registry, secrets,
domain and live deployment require a later deployment task. The future proxy uses
port 8000 and health path `/api/health`.
