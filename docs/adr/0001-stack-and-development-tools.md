# ADR 0001: Application stack and development tools

Status: Accepted

Date: 2026-09-05

## Context

The project is a single-page image preparation tool. The owner selected Python with FastAPI and uv for the backend, and React with Vite, TypeScript and Tailwind for the frontend. Local setup and startup must each take one command from the repository root.

## Decision

- Use Python 3.14, FastAPI, Uvicorn and Pillow in `backend/`. Keep the uv project and its `pyproject.toml` at the repository root.
- Use React, Vite, TypeScript and Tailwind in `frontend/`. Use npm and the official Tailwind Vite integration.
- Use root `mise.toml` for Python, Node.js 24 LTS, uv and Ruby versions. Resolve and pin compatible patch versions during scaffold; use the same tool versions in CI. Do not add separate runtime version files.
- Let uv manage Python application and development packages and `.venv`. Point `UV_PYTHON` at the Python installation selected by mise. Let npm manage frontend packages. Commit `uv.lock` and `frontend/package-lock.json`.
- Declare `gem "kamal"` in the root `Gemfile`, install with `bundle install`, and commit `Gemfile.lock`. Run Kamal through `bundle exec kamal`. Do not install Kamal through mise or add `gem:kamal` to `mise.toml`.

## Local workflow

After initial scaffold has generated the manifests and lockfiles, the owner runs `mise run setup` from the repository root. Its sequential commands are `uv sync --locked`, `npm --prefix frontend ci --include=dev`, and `bundle install`. Stop on the first failed command. The owner runs setup; survey does not install dependencies. Do not wrap these commands in `mise exec`.

The owner runs `mise run dev` from the repository root to start the backend and frontend together in one terminal. Define `dev` with parallel dependencies `dev:backend` and `dev:frontend`:

- `dev:backend`: `uv run uvicorn backend.main:app --reload --reload-dir backend --port 8000`.
- `dev:frontend`: `npm --prefix frontend run dev -- --port 5173 --strictPort`.

Use normal prefixed task output, not raw or interactive tasks, so both servers can run concurrently. Ensure at least two task slots. Verify that one Ctrl+C stops both servers and their reload children and releases both ports. Setup and dev remain separate tasks; dev must not run `bundle install` implicitly.

## Consequences

Each ecosystem keeps its normal package manager. mise selects tools and runs the two root commands; it does not replace uv, npm or Bundler. Ruby and Kamal are deployment tooling, not application runtime dependencies.

Use pytest with HTTPX for backend checks, Ruff for Python lint, and TypeScript and ESLint for frontend checks. Keep all Python development dependencies in the default `dev` group. The frontend build runs the TypeScript check before Vite. Start with the skeleton smoke test; introduce component test tooling only when feature behavior needs it.

## Sources

- [Product brief](../idea-brief.md).
- [mise tasks](https://mise.jdx.dev/tasks/running-tasks.html).
- [mise and uv](https://mise.jdx.dev/lang/python.html#mise-uv).
- [uv dependency syncing](https://docs.astral.sh/uv/concepts/projects/sync/).
- [Tailwind Vite integration](https://tailwindcss.com/docs/installation/using-vite).
