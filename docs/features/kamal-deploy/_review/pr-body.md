## Summary

Records a complete self-host Kamal recipe and a local Configuration check so the Project owner can later publish with one documented command. Secret values stay out of git. This PR does not publish. See [spec](docs/features/kamal-deploy/spec.md).

## Acceptance criteria

- AC-01 — recipe records host, both Public site names, image, registry username, HTTPS, service `image_compressor`, arch amd64, port 8000 and `/api/health` ✓
- AC-02 — committed tree has no secret values; `.kamal/secrets` is gitignored; environment-variable names may appear ✓
- AC-03 — Configuration check succeeds without contacting the production host or the container registry ✓
- AC-04 — missing required field or registry password fails the check and names each gap in glossary terms ✓
- AC-05 — root README documents exactly one later publish command, `bundle exec kamal deploy` ✓
- AC-06 — compression form exposes no publish or Configuration check action ✓
- AC-07 — existing single-image process path (selection, limits, download, cleanup) is unchanged ✓
- AC-08 — recipe reverse-proxy port and health path match the application image; a different port or path is rejected ✓

## Design

- Spec: `docs/features/kamal-deploy/spec.md`
- Architecture: `docs/features/kamal-deploy/sad.md`
- Decisions: `docs/features/kamal-deploy/adr/`
- Data model: N/A (no schema change; files stand in for a store)
- API: `docs/features/kamal-deploy/contracts/cli.md` (CLI surface; no OpenAPI)

## Tasks (SDD-Task trailers)

- T1 `13ade69` feat(kamal-deploy): ignore the Secrets file in git
  - `SDD-Task: T1` / `SDD-AC: AC-02`
- T2 `b895786` feat(kamal-deploy): record locked host facts in deploy.yml
  - `SDD-Task: T2` / `SDD-AC: AC-01, AC-08`
- T3 `5e897ec` test(kamal-deploy): add throwaway registry password fixture
  - `SDD-Task: T3` / `SDD-AC: AC-03`
- T4 `5f94f44` test(kamal-deploy): prove recipe offline without Kamal
  - `SDD-Task: T4` / `SDD-AC: AC-01, AC-03, AC-08`
- T5 `fb7f9dc` test(kamal-deploy): name missing recipe fields and secrets
  - `SDD-Task: T5` / `SDD-AC: AC-04`
- T6 `364bb18` test(kamal-deploy): reject secrets and target mismatch
  - `SDD-Task: T6` / `SDD-AC: AC-02, AC-08`
- T7 `25f4872` docs(kamal-deploy): document later publish command
  - `SDD-Task: T7` / `SDD-AC: AC-05`
- T8 `197e6b5` test(kamal-deploy): keep compression form free of publish
  - `SDD-Task: T8` / `SDD-AC: AC-06, AC-07`

## Verification

- Unit: `uv run pytest` — 223 passed
- Integration: same pytest suite (Configuration check + smoke). No separate `-m integration`. Docker daemon reachable; container smoke **not** re-run — this increment does not change the application image, Dockerfile, backend or frontend.
- Lint + vet: `uv run ruff check .` pass; `npm --prefix frontend run lint` pass; `npm --prefix frontend run build` (`tsc --noEmit` + Vite) pass; `bundle check` pass; `bundle exec kamal version` → 2.12.0
- Ran the feature (offline Configuration check against committed `config/deploy.yml` + throwaway fixture, not Kamal):
  - AC-01: recipe on disk has host `138.201.118.229`, `image.bondev.eu` + `www.image.bondev.eu`, image `shved270189/image_compressor`, username `shved270189`, `ssl: true`, service `image_compressor`, arch `amd64`
  - AC-02: `git check-ignore -q .kamal/secrets` exit 0; committed password is the name `KAMAL_REGISTRY_PASSWORD` only
  - AC-03: `run_configuration_check` → `Configuration check success` in 0.0002 s; check module does not invoke Kamal or open sockets
  - AC-04: absent Secrets file → `missing registry password from Secrets file`; incomplete recipe names host address, Public site name, image name, registry username, HTTPS, service name, listening port, health-check path
  - AC-05: README contains exactly `bundle exec kamal deploy` and no `kamal setup`
  - AC-06: `frontend/src/App.tsx` has no publish / configuration check / kamal / deploy action
  - AC-07: smoke path still passes inside the 223 pytest run (health, page, assets, process)
  - AC-08: `app_port: 8000` and `path: /api/health`; `app_port: 3000` → `listening port does not match the application image`

## Operational notes

- Migration: none.
- Feature flag / config: none. Recipe is `config/deploy.yml`. Secrets file is `.kamal/secrets` (gitignored).
- Rollback: revert the feature commits. This increment does not run `bundle exec kamal deploy`.
- Residual: a green Configuration check does not prove DNS, certificates or image pull. SSH user remains an open question until first live publish.
