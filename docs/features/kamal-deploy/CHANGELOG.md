# Changelog — kamal-deploy

## kamal-deploy — record a self-host publish recipe and prove it offline

**What:** The repository now holds a complete Kamal Deploy configuration with the real non-secret host facts, and a local Configuration check that proves that recipe is readable and complete. Secret values stay in the ignored Secrets file. Live publish is documented, not executed.

**Why:** The local-only roadmap left public hosting out of scope, so there was no committed recipe to aim a later command at ([spec](./spec.md) §1–§2). This increment records that recipe without contacting the production host or the container registry. The Configuration check is a CLI-only surface ([ADR-0001](./adr/0001-declare-cli-surface-for-configuration-check.md)) implemented as an offline pytest module so it cannot open those sockets ([ADR-0002](./adr/0002-prove-recipe-with-offline-pytest-check.md)).

**How to use:** Record non-secret facts in `config/deploy.yml` and keep the registry password in `.kamal/secrets`. Prove the recipe with the Configuration check:

```sh
uv run pytest
```

The later publish command, when you are ready, is exactly:

```sh
bundle exec kamal deploy
```

Do not run that command as part of this increment. The check is not a publish ([cli.md](./contracts/cli.md)).

**Operational notes:**
- Migration: none. There is no datastore.
- Feature flag / config: none. Host facts are committed in `config/deploy.yml`. Registry password lives only in `.kamal/secrets` (gitignored); tests use `tests/fixtures/kamal/secrets`, which is not production secrets.
- Rollback: revert the feature commits. This increment does not publish, so there is no production deploy to undo.
- Runtime: Kamal stays 2.12.0 via Bundler. The reverse-proxy target remains port 8000 and `/api/health`. CI gains no new job; the existing pytest suite covers the check.
- Scope: configuration-only. Host provisioning, DNS, certificates, `kamal setup` and the first live publish stay later. SSH user is still an open question (spec §8).

**Acceptance criteria delivered:** AC-01 … AC-08 — locked host facts in the recipe, secrets absent from git, offline Configuration check success and named-gap failure, README later command `bundle exec kamal deploy`, unchanged compression form and processing path, production-target port/path invariant.
