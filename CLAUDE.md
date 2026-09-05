# Project conventions

Read `docs/architecture-map.md` before changing module boundaries or tooling. Read
`docs/idea-brief.md` and the feature specification before implementing image processing.

- Keep HTTP validation in `backend/main.py`. Add ordinary image functions in
  `backend/images.py` only when the feature needs them.
- Preserve `/api` 404 responses when changing frontend serving. The backend must
  start before `frontend/dist` exists; restart it after the first production build.
- Use React local state, relative `/api` fetch calls, native accessible controls and
  Tailwind. Keep theme tokens in `frontend/src/index.css` and respect reduced motion.
- Keep uploads and results request-scoped. Specify resource limits and cleanup
  before adding processing; no datastore or migrations belong to this foundation.
- Use root mise tasks and the existing uv, npm and Bundler lockfiles. The owner runs
  `mise run setup`; `mise run dev` starts both servers. Run Kamal with `bundle exec kamal`.

Build the frontend before `uv run pytest`; the smoke test requires real emitted assets.
Use `SMOKE_BASE_URL` to run the same smoke test against a container. Run both lint
commands from `README.md` after code changes. Extend the existing smoke test for
structural regressions; add feature tests only for specified behavior.
