# Image compressor

Runnable foundation for a single-image preparation app. FastAPI serves the health
endpoint and built React frontend. Image processing is not implemented yet.

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

Build first: the smoke test checks the real HTML, emitted JS/CSS, health and API 404s.

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
