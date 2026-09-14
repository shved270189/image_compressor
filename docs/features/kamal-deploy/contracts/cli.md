---
status: Draft
owner: "Backend Lead"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-13"
feature_size: S
---

# CLI contract — kamal-deploy

The Project owner can already process one image on a local single-page form. The application image exists. There is no committed publish recipe, so the owner cannot run one later command to put that form on their own host when they are ready. This interface is the local Configuration check plus the documented later publish command: it proves Deploy configuration is readable and complete without contacting the production host or the container registry, and it records exactly which command the owner will run later. Live publishing is outside this step.

Interface kind: **CLI** (`sad.md` `target_surfaces: [cli]`). There is no OpenAPI document, no HTTP path, and no `events.md` (every §6 flow is synchronous; `<external-system>` is isolation-only).

## Commands

### `configurationCheck`

| | |
|---|---|
| **Invocation** | `uv run pytest` |
| **Module** | `tests/test_kamal_deploy.py` (runs as part of the existing suite) |
| **User story** | US-03, US-04 |
| **Acceptance** | AC-03, AC-04; also AC-01, AC-02, AC-08 as file invariants the check reads |
| **Sequence** | Run configuration check |
| **Mutating?** | No — reads Deploy configuration and the Secrets file |
| **Network** | Forbidden: no session or TCP to the recorded host address `138.201.118.229` or to the container registry. Must not invoke Kamal commands that can open those sockets (`bundle exec kamal config`, `bundle exec kamal deploy`, `bundle exec kamal setup`, registry login). |
| **Runtime** | Wall clock of this invocation ≤ 30 s on the Project owner's machine (spec §6). |
| **Auth** | No bearer token. Only a Project owner with the Secrets file can obtain success; absence of the required registry password is a named failure, not a prompt. |
| **Flags** | None owned by this feature. Pytest's own selector flags may narrow the run during development; they are not a second public command and must not become a mise wrapper (feature ADR 0002). |
| **Idempotency-Key** | N/A — synchronous local read; no retry actor. |

**Inputs the check reads**

| Input | Path | Required |
|---|---|---|
| Deploy configuration | `config/deploy.yml` | Yes |
| Secrets file | `.kamal/secrets` (gitignored). Tests use a throwaway fixture that is not production secrets | Yes for success; missing password is a named failure |
| Application image facts | Existing listening port `8000` and health-check path `/api/health` (foundation ADR 0002) | Yes — mismatch is `kamal_deploy.production_target_invariant_violated` |

**Success (exit 0)**

pytest reports success. Every required non-secret field below is present and has the locked value; the required registry password is present in the Secrets file (or the throwaway fixture); zero connections to the host or registry.

**Failure (exit 1)**

pytest reports failure. The failure names **each** missing required field or secret in glossary terms (Configuration check, Deploy configuration, Public site name, Secrets file, host address, image name, registry username, service name, image architecture, listening port, health-check path, registry password). It does not report success. Several gaps in one run are listed together.

**Other pytest exits (2–5)**

Interrupted, internal error, usage error, or no tests collected. Not success. Not a substitute for a named missing-field failure.

### `laterPublish` (documented, not executed this step)

| | |
|---|---|
| **Invocation** | `bundle exec kamal deploy` |
| **User story** | US-05 |
| **Acceptance** | AC-05 |
| **Sequence** | Record deploy configuration — README write |
| **Mutating?** | Yes — live publish. **This increment must not run it.** |
| **Flags** | None. No destination flag (`-d`), no extra environment. One production host. |
| **Auth** | Kamal reads the Secrets file and the machine SSH agent at publish time. SSH user is an open question (spec §8); not required for the Configuration check. |
| **Idempotency-Key** | N/A this step — command is documented only. |

The root README must contain exactly this later command and must not present the Configuration check as a publish. `bundle exec kamal setup` is out of scope (spec §3).

### Record Deploy configuration (file write, not a command)

US-01 and US-02 have no owner-facing binary. The Project owner records facts by committing `config/deploy.yml` and keeping secret values in `.kamal/secrets`. Sequence `else` branches are invariants the Configuration check (and the gitignore test) enforce:

| Sequence branch | Contract outcome |
|---|---|
| required facts present, secrets stay local, port and path match | Files on disk; `configurationCheck` exit 0 |
| secret value in committed recipe | `kamal_deploy.secret_in_committed_tree` — pytest failure; `.kamal/secrets` is gitignored |
| port or health-check path does not match the application image | `kamal_deploy.production_target_invariant_violated` — pytest failure; not success |

### Compression form (out of this surface)

US-06 / AC-06 / AC-07: the Image owner form exposes no Configuration check and no publish action. Host facts in the recipe are not a form capability. No CLI flag, HTTP path, or UI control is added for publish. Existing `POST /api/v1/images/process` is unchanged and is not part of this contract.

## Recipe fields

Every field the Configuration check requires. Names in **Glossary term** are the words failure output must use. **Kamal 2.12.0 key** is the existing-schema binding in `config/deploy.yml` (Kamal 2 configuration, not a database column). `data-model.md` is absent — legal fast-lane skip (no schema change).

| Glossary term | Kamal 2.12.0 key | Constraint | Locked value |
|---|---|---|---|
| service name | `service` | exact string; alphanumeric, hyphen, underscore | `image_compressor` (not `bondev_site`, not the registry-prefixed image name) |
| image name | `image` | Docker image name without registry host or tag | `shved270189/image_compressor` |
| host address | `servers.web` (primary role host list) | one production host; no accessory; no second destination | `138.201.118.229` |
| Public site name | `proxy.hosts` | both names required; Kamal 2 uses `hosts` (plural) when there is more than one | `image.bondev.eu` and `www.image.bondev.eu` |
| HTTPS | `proxy.ssl` | enabled for both Public site names | `true` |
| listening port | `proxy.app_port` | must match the application image | `8000` |
| health-check path | `proxy.healthcheck.path` | must match the application image | `/api/health` |
| registry username | `registry.username` | non-empty | `shved270189` |
| registry password | `registry.password` as an environment-variable **name** only | value lives in the Secrets file; name may appear in the recipe | name present; value absent from git |
| image architecture | `builder.arch` | exact | `amd64` |

Not required this step (do not fail the check for their absence): SSH user, SSH private key in the Secrets file, DNS pointing, certificates, `kamal setup`, a second environment, accessories.

Secret values that must never appear in the committed tree: registry password value, SSH private key material, any other secret value. Environment-variable names are allowed.

## Exit codes

Owned by `configurationCheck` (`uv run pytest`). pytest's documented codes, applied to this feature:

| Code | Meaning for this feature |
|---|---|
| 0 | Configuration check success (AC-03) |
| 1 | Tests failed: missing required field or secret, secret in committed tree, or production-target invariant violated. Failure text names each gap in glossary terms (AC-02, AC-04, AC-08) |
| 2–5 | pytest interrupted / internal / usage / no tests collected — not success; not a named-gap failure |

`laterPublish` has no exit-code contract in this increment because it is not run.

## Error codes

No application error registry exists in this repository. These codes are the contract's proposal for implementers (assertion ids / test names). **User-visible failure text uses glossary terms**, not these tokens.

Envelope analog (pytest assertion message, not JSON): name every missing item; optional `details` as the list of glossary terms.

| code | When | Sequence branch |
|---|---|---|
| `kamal_deploy.missing_host_address` | host address absent from Deploy configuration | required field or secret missing |
| `kamal_deploy.missing_public_site_name` | either Public site name absent | required field or secret missing |
| `kamal_deploy.missing_image_name` | image name absent | required field or secret missing |
| `kamal_deploy.missing_registry_username` | registry username absent | required field or secret missing |
| `kamal_deploy.missing_https` | HTTPS not enabled | required field or secret missing |
| `kamal_deploy.missing_service_name` | service name absent or not `image_compressor` | required field or secret missing |
| `kamal_deploy.missing_image_architecture` | image architecture absent or not amd64 | required field or secret missing |
| `kamal_deploy.missing_listening_port` | listening port absent | required field or secret missing |
| `kamal_deploy.missing_health_check_path` | health-check path absent | required field or secret missing |
| `kamal_deploy.missing_registry_password` | required registry password absent from the Secrets file | required field or secret missing |
| `kamal_deploy.secret_in_committed_tree` | a secret value is present in git | secret value in committed recipe |
| `kamal_deploy.production_target_invariant_violated` | reverse-proxy target port is not 8000 or health-check path is not `/api/health` | port or health-check path does not match |

## Examples

Placeholder secret only. Host address, Public site names, image name and registry username are the interview facts the recipe must commit (spec §1); they are internal facts that become public in git, not personal data.

### Success — complete recipe and throwaway Secrets file

```text
$ uv run pytest
============================= test session starts ==============================
tests/test_kamal_deploy.py::test_configuration_check_succeeds_offline PASSED
============================== 1 passed in 0.40s ===============================
```

Exit 0. No connection to `138.201.118.229` or the container registry.

Throwaway Secrets file fixture (not production secrets, not committed):

```text
KAMAL_REGISTRY_PASSWORD=test-registry-password
```

The environment-variable **name** may appear in `config/deploy.yml`; the value above must not.

### Error — missing Secrets file / registry password

```text
$ uv run pytest
tests/test_kamal_deploy.py::test_configuration_check_names_missing_secrets FAILED
E   AssertionError: Configuration check failed: missing registry password from Secrets file
============================== 1 failed in 0.20s ===============================
```

Exit 1. Message uses the glossary terms Secrets file and registry password. Not success.

### Error — missing required recipe field

```text
$ uv run pytest
tests/test_kamal_deploy.py::test_configuration_check_names_missing_fields FAILED
E   AssertionError: Configuration check failed: missing host address, missing Public site name
============================== 1 failed in 0.20s ===============================
```

Exit 1. Each gap named in glossary terms.

### Later publish (documentation only)

Root README contains exactly:

```sh
bundle exec kamal deploy
```

This increment does not execute that line.
