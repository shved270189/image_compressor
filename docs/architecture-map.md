---
status: current
mode: current
updated_at: "2026-09-13"
reflects_commit: "3236057"
language: "Python 3.14 + TypeScript"
build_cmd: "npm --prefix frontend run build"
test_cmd: "uv run pytest"
lint_cmd: "uv run ruff check . && npm --prefix frontend run lint"
migration_tool: ""
frontend: "React + Vite + TypeScript + Tailwind"
---

# Architecture map — image-compressor

Incremental re-survey of `787a257`..`3236057` (backend, frontend, tests, README) plus the `kamal-deploy` surface. The foundation, image-resize-convert, and image-size-limit implementations are materialized. [Feature tracker](features/image-size-limit/tasks/tracker.md) records the optional Size limit work and browser acceptance. [Scaffold tasks](features/_scaffold/tasks.json) retain setup evidence. Hosted GitHub Actions and public deployment remain unverified. `config/deploy.yml` records the production recipe.

## Stack

- Python 3.14, FastAPI, Uvicorn, Pillow 12.3.0 and pillow-heif 1.6.0. Starlette 1.6.0 and python-multipart 0.0.22 are pinned for bounded parsing; Pillow bundles the LittleCMS binding used for color profiles. uv owns the root project and default development dependencies — `pyproject.toml:1` and `uv.lock`.
- React, Vite, TypeScript and Tailwind use npm — `frontend/package.json:1` and `frontend/package-lock.json`. TypeScript stays on 6.0.x to satisfy typescript-eslint peer requirements.
- mise pins Python 3.14.6, Node.js 24.18.1, uv 0.12.9 and Ruby 4.0.5 — `mise.toml:1`. `UV_PYTHON` points to mise's interpreter; uv owns `.venv` — `mise.toml:7`.
- Kamal is declared in `Gemfile:3` and locked to 2.12.0. Ruby and Bundler are deployment tools, outside the application runtime.
- Build, test and lint commands in frontmatter match README checks. Build the frontend before pytest; the smoke test requires emitted assets — `README.md:85` and `tests/test_smoke.py:69`.

## C4 — system as it is

The application image exists and runs locally. Image resizing and conversion are implemented; browser/security acceptance is recorded in the feature audits. The public proxy and deployment below remain the target topology.

```mermaid
C4Context
    title Image compressor foundation
    Person(user, "Image owner", "Prepares one image for size and format requirements")
    System(compressor, "Image compressor", "Single-image resizing and format conversion")
    Rel(user, compressor, "Opens the application", "HTTP locally; HTTPS after deployment")
```

```mermaid
C4Container
    title Application image and target deployment
    Person(user, "Image owner", "Uses the browser")
    Container(ui, "Browser UI", "React and TypeScript", "Local selection, optional preview, settings and automatic download")
    Container(proxy, "kamal-proxy", "Future reverse proxy", "Routes public traffic after deployment")
    Container(app, "Application", "FastAPI and Pillow", "Serves health, processing API and built frontend")
    Rel(user, ui, "Uses")
    Rel(ui, proxy, "Requests assets and processing API", "HTTPS")
    Rel(proxy, app, "Forwards requests", "HTTP port 8000")
```

One image contains backend code and built frontend assets. The browser UI is a logical client, not a second deployed service. Local checks access the application directly without a proxy — `Dockerfile:17` and `docs/adr/0002-single-service-and-kamal.md:29`.

## Module inventory

| Module | Path | Wired at | Responsibility |
|---|---|---|---|
| Backend | `backend/` | `backend/main.py:19` | HTTP validation, bounded multipart, safe errors, response ownership and frontend serving |
| Image functions | `backend/images.py` | `backend/main.py:191` | Static decoding, HEIF timelines, resize, color normalization and encoding |
| Frontend | `frontend/` | `frontend/src/main.tsx:6` | Local selection/preview, one current request, download/reset and error retry |
| Development tooling | Repository root | `mise.toml:13` | Sequential setup and concurrent dev servers |
| Container delivery | Repository root | `Dockerfile:17` | One non-root application image |
| Deployment tooling | Repository root | `Gemfile:3` | Locked Kamal CLI and `config/deploy.yml` recipe |
| Verification | `tests/`, `.github/workflows/` | `tests/test_smoke.py:58`, `.github/workflows/ci.yml:1` | Shared in-process and live-container smoke scenarios |

## Conventions

- **Module wiring:** FastAPI entry point — `backend/main.py:19`. Health handler — `backend/main.py:167`. The processing handler calls ordinary functions in `backend/images.py` from a shielded executor — `backend/main.py:191` and `docs/adr/0002-single-service-and-kamal.md:13`.
- **HTTP errors:** validate multipart fields manually at the HTTP boundary and return safe FastAPI errors. `POST /api/v1/images/process` returns complete binary output with attachment headers and, when a Size limit was supplied, `X-Result-Bytes` and `X-Size-Limit-Met` — `backend/main.py:223`. Size limit uses decimal SI units (`1 Mb = 1_000_000` bytes, `1 Kb = 1000`) — `backend/main.py:149`. Its contract is `docs/features/image-size-limit/contracts/openapi.yaml`.
- **Frontend serving:** `app.frontend` serves the build with fallback disabled, preserving API 404s — `backend/main.py:235`. Registration is conditional on the build directory so the API boots before a build exists. Restart the backend after the first build.
- **Tests:** pytest and HTTPX check health, built HTML, emitted JS/CSS, a PNG→WebP process call without miss headers, a size_limit-only JPEG, and unknown API paths with JSON and HTML Accept headers — `tests/test_smoke.py:58`. `test_heic_notice_copy` and `test_size_limit_form_copy` pin form copy, including a native Mb/Kb select rather than radios — `tests/test_smoke.py:22`. `oriented-exif6.jpg` is the Preview/download orientation control — `tests/fixtures/images/README.md:18`. `SMOKE_BASE_URL` runs the same scenarios against a live container. Ruff, TypeScript and ESLint provide static checks.
- **UI communication:** browser processing uses relative `/api/v1/images/process` fetch calls — `frontend/src/App.tsx:123`. Vite proxies `/api` to the backend — `frontend/vite.config.ts:8`. Use React local state; no global store, server-cache library or client router.
- **IDs / persistence:** no image IDs, datastore or migration tool. Attachment name is `result.{jpg|png|webp}` — `backend/main.py:222`. `migration_tool: ""` means N/A.

## Datastores

No persistent datastore, image IDs, object store, queue or migration tool exists. `migration_tool: ""` means N/A, not a missing command — `docs/adr/0003-transient-image-processing.md:16`.

Uploads use request-scoped spooled `UploadFile` storage. Parsing limits file bytes to 20,000,000 and decoding limits pixels to 40,000,000. A shielded executor operation owns the upload until native work finishes; ExitStack closes decoded/intermediate images. The response clears encoded bytes after completion or send failure. No image or filename is logged; parser diagnostics are disabled — `docs/adr/0003-transient-image-processing.md:13`.

## Frontend / UI foundation

- **Closest precedent:** `frontend/src/App.tsx` owns the single form with independently optional dimension limits, optional Size limit (native Mb/Kb `<select>` to the right of the decimal number) and JPEG/PNG/WebP selection — `frontend/src/App.tsx:216`. Local preview URLs are revoked on replacement, failure, success and teardown. A miss keeps the form and shows actual bytes; a met or omitted bound downloads once then resets. The HEIC primary-image/HDR disclaimer sits under the format field — `frontend/src/App.tsx:227`.
- **Components:** native accessible controls and React local state. Shared class `.field` — `frontend/src/index.css:37`. Extract shared components only for actual reuse; no third-party component kit — `docs/adr/0002-single-service-and-kamal.md:25`.
- **Styling:** Tailwind Vite plugin — `frontend/vite.config.ts:6`. Typography, canvas, ink, muted and accent tokens live in `@theme` — `frontend/src/index.css:3`. Surface, line and danger tokens are a second `@theme` block — `frontend/src/index.css:30`. The feature must retain deliberate spacing and a clear primary action, with the form as the focus — `docs/idea-brief.md:47`.
- **Motion:** CSS entry motion runs only under `prefers-reduced-motion: no-preference` — `frontend/src/index.css:17`. `overflow-anchor: none` on `main` prevents enter `translateY` from accumulating scroll on reload — `frontend/src/index.css:20`. `prefers-reduced-motion: reduce` disables animation and transition — `frontend/src/index.css:47`. Controls use native labels, keyboard focus and a truthful busy state without percentages. One AbortController identifies the current request; choosing another file aborts in-flight work — `frontend/src/App.tsx:65`. Complete Blob handoff happens once, then the result URL is revoked and the native file input resets. Recoverable errors preserve selection; pagehide invalidates work — `docs/idea-brief.md:49` and `docs/adr/0002-single-service-and-kamal.md:25`.
- **Acceptance:** Chrome flow checks and native Safari/Firefox downloads are recorded in [browser acceptance](features/image-resize-convert/_audit/browser-acceptance.md). Size limit, miss keep-form and 360/1280 overflow are recorded in [image-size-limit browser acceptance](features/image-size-limit/_audit/browser-acceptance.md). The owner confirmed download/reset on iOS and desktop Safari/Firefox and accepted phone/desktop readability. Firefox/WebKit engine failure/retry/interruption checks and native Safari server-error retry pass; the owner confirmed real iPhone Safari network-failure/retry and form reset.

## Root development commands

The owner runs `mise run setup` after installing the pinned tools. Setup sequentially runs `uv sync --locked`, `npm --prefix frontend ci --include=dev` and `bundle install` — `mise.toml:13`. Both successful runs in a disposable repository copy preserved all lockfile hashes. An invalid uv.lock stopped execution before npm or Bundler.

`mise run dev` starts both dependency tasks with two task slots — `mise.toml:10` and `mise.toml:20`:

```sh
uv run uvicorn backend.main:app --reload --reload-dir backend --port 8000
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Open <http://localhost:5173>. Vite proxies `/api` to <http://127.0.0.1:8000>. Root startup, prefixed logs, backend reload and browser HMR passed. One Ctrl+C stopped both servers and reload children and released ports 8000 and 5173. mise reports an interrupted task as an error; process cleanup still passed. Dev never invokes setup. Commands use no `mise exec` wrappers.

## Container and CI

`Dockerfile:1` builds the frontend with Node.js 24 and installs locked Python runtime dependencies in a separate stage. `Dockerfile:17` runs Python 3.14 as UID 10001, serves built assets and starts Uvicorn on port 8000 without reload. `.dockerignore:1` allowlists build inputs and excludes local dependencies and environment files.

`docker build -t image-compressor:smoke .` passed on Linux arm64. Live-container `SMOKE_BASE_URL=http://127.0.0.1:8000 uv run pytest` passed. Runtime inspection confirmed Node.js, npm, Ruby, uv, Ruff and pytest are absent.

`.github/workflows/ci.yml:1` uses mise and locked dependencies for build, pytest, Ruff, ESLint, Bundler checks and the same container smoke scenarios. CI also runs `bundle check && bundle exec kamal version` — `.github/workflows/ci.yml:24`. actionlint passed. Hosted execution is unverified. CI has no deploy job, registry login, or `kamal deploy`.

Kamal 2.12.0 is locked in `Gemfile.lock` and invoked only as `bundle exec kamal` — `Gemfile:3` and `docs/adr/0001-stack-and-development-tools.md:17`. Ruby 4.0.5 is a mise pin for that CLI; do not add `gem:kamal` to `mise.toml`. `config/deploy.yml` is the committed production recipe: host `138.201.118.229`, Public site names `image.bondev.eu` and `www.image.bondev.eu`, image `shved270189/image_compressor`, registry username `shved270189`, HTTPS on, service `image_compressor`, `builder.arch: amd64`, `proxy.app_port: 8000`, and `proxy.healthcheck.path: /api/health`. Secret values stay in gitignored `.kamal/secrets`. Accessories, destination files, and a Docker `HEALTHCHECK` instruction remain absent. The later publish command is `bundle exec kamal deploy`; this map does not run it. CI has no deploy job.

## Implemented scope and remaining acceptance

- One image and one form; no batch processing, history, presets, cropping or stretching — `docs/idea-brief.md:28`.
- Width and height are independently optional; preserve aspect ratio with no enlargement. Roadmap step 3 [`image-size-limit`](roadmap.md) (size S, materialized) extends the same form and `POST /api/v1/images/process` with an optional Size limit. A supplied bound may shrink below those maxima to meet the byte budget; encoder-limit 422 is unchanged. Size limit is a positive decimal with `mb`/`kb`; `1 Mb = 1,000,000` bytes and `1 Kb = 1,000` bytes — `backend/main.py:149` and `README.md:19`. D2 is closed — `docs/roadmap.md:44` and `docs/features/image-size-limit/spec.md`.
- Static JPEG/PNG/WebP/HEIC input becomes JPEG/PNG/WebP output. JPEG uses white behind alpha; metadata is stripped after orientation. HEIC primary-image selection and HDR-to-SDR normalization are implemented. Codec output dimensions above WebP 16,383 or JPEG 65,500 return actionable 422, as approved in the feature amendment.
- Independent Security Lead technical review passed. Hosted CI and public deployment remain unverified; real iPhone Safari network-failure/retry is owner-confirmed. Android is owner-deferred; migrations are N/A.

## Reconciliation

The [idea brief](idea-brief.md) and accepted [ADRs](adr/) remain authoritative for product and foundation decisions. There is no hand-maintained `docs/architecture.md`. `README.md` documents the runnable commands; `CLAUDE.md` records project conventions. The local SDD settings remain unchanged.

[ADR 0002](adr/0002-single-service-and-kamal.md) already chose one application container behind kamal-proxy. The [roadmap](roadmap.md) still marks public hosting and Kamal deployment as out of scope and lists image-size-limit as `spec'd`; the Size limit tracker is fully `done` and the code is on HEAD. This map records that drift; it does not rewrite the roadmap.

Commit `1cd6142` records the brief; `5e334ab` establishes the foundation; `616dca8` adds visual requirements; `86ac0c5` ships the image-resize-convert changelog and marks that roadmap step shipped. The image feature extends that foundation without new service or datastore boundaries. `_scaffold` is a repository stage with no feature size or pipeline route. This map is a brownfield incremental re-survey of the materialized system (`mode: current`).
