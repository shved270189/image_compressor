---
id: T2
title: "Record Deploy configuration with locked host facts"
layer: "infra"
deps: []
blocks: ["T4", "T7", "T8"]
acs: ["AC-01", "AC-08"]
files_hint: ["config/deploy.yml"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
---

# T2 — Record Deploy configuration with locked host facts

## Place in the sequence

- **Blocked by:** none · **Blocks:** T4 — Implement the offline Configuration check success path, T7 — Document the later publish command, T8 — Keep the compression form and existing smoke unchanged · **Wave:** 1, parallel with T1.
- **Lane:** own lane (`config/deploy.yml`). Do not write secret values into this file.

## Why (user story)

> **As a** Project owner
> **I want** Deploy configuration to record the known host, both Public site names, image name, registry username, HTTPS, service name `image_compressor`, image architecture amd64, the application's existing listening port, and the application's existing health-check path
> **So that** a later publish command has a complete non-secret recipe.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task commits `config/deploy.yml` with those locked non-secret facts.

## Inlined context

> Interview facts, committed as non-secret recipe values: host `138.201.118.229`, Public site names `image.bondev.eu` and `www.image.bondev.eu`, image `shved270189/image_compressor`, registry username `shved270189`, HTTPS on, service name exactly `image_compressor`, image architecture amd64.
>
> — `sad.md §2, Technical constraints, abridged` · full text: [sad.md](../sad.md)

> Commit real non-secret host facts in `config/deploy.yml`; keep secret values only in the gitignored Secrets file. The recipe may contain environment-variable names, including the registry-password name. Values live in `.kamal/secrets`. SSH private key is not required in that file. No second destination file, accessory or extra service.
>
> — `sad.md §4, strategic choice 2, abridged` · full text: [sad.md](../sad.md)

> The recipe points kamal-proxy at port 8000 and health path `/api/health`, sets service name `image_compressor`, enables HTTPS for both Public site names, and builds amd64.
>
> — `sad.md §4, strategic choice 4, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Do not add `gem:kamal` to `mise.toml`. Run Kamal only as `bundle exec kamal`. No datastore, queue, accessory or second environment. Foundation ADR 0002 already fixes `proxy.app_port: 8000` and `proxy.healthcheck.path: /api/health`.
>
> — `sad.md §2, Technical and Conventions, abridged` · full text: [sad.md](../sad.md)

> Recipe builds amd64 while a local Docker check previously ran on arm64 — Record `builder.arch: amd64` in Deploy configuration.
>
> — `sad.md §11, amd64 risk, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Record Deploy configuration is a file write, not a command. Required Kamal 2.12.0 keys in `config/deploy.yml`:

| Glossary term | Key | Locked value |
|---|---|---|
| service name | `service` | `image_compressor` |
| image name | `image` | `shved270189/image_compressor` |
| host address | `servers.web` | `138.201.118.229` |
| Public site name | `proxy.hosts` | `image.bondev.eu` and `www.image.bondev.eu` |
| HTTPS | `proxy.ssl` | `true` |
| listening port | `proxy.app_port` | `8000` |
| health-check path | `proxy.healthcheck.path` | `/api/health` |
| registry username | `registry.username` | `shved270189` |
| registry password | `registry.password` as an environment-variable **name** only | name present; value absent from git |
| image architecture | `builder.arch` | `amd64` |

Not required this step: SSH user, SSH private key in the Secrets file, DNS, certificates, accessories, a second environment.

— `contracts/cli.md, Recipe fields, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-01 — happy

> **Given** the Project owner knows the production host address, both Public site names, image name and registry username,
> **When** they record Deploy configuration,
> **Then** the recipe names those facts, enables HTTPS for both Public site names, sets service name to `image_compressor`, sets image architecture to amd64, uses the application's existing listening port and existing health-check path, and the Project owner can see those values in the repository.
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — domain invariant

> **Given** the already-built application image uses its established listening port and health-check path,
> **When** Deploy configuration is recorded,
> **Then** the recipe's reverse-proxy target port and health-check path match that image; a different port or path violates the production-target invariant.
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Create `config/deploy.yml` with the locked keys and values from the contract table
- [ ] Set `registry.password` to an environment-variable name only (example name `KAMAL_REGISTRY_PASSWORD`); do not write a password value
- [ ] Do not add accessories, a second destination, or an SSH user
- [ ] Do not run `bundle exec kamal deploy` or `bundle exec kamal setup`

## Edge cases

| Case | Behaviour |
|---|---|
| Secret value written into `config/deploy.yml` | Reject — secret values belong only in the Secrets file (T6 asserts) |
| `proxy.app_port` other than 8000 or health path other than `/api/health` | Violates the production-target invariant (T6 asserts) |
| Service name `bondev_site` or the registry-prefixed image name | Not accepted; service name is exactly `image_compressor` |
| Local machine is arm64 | Recipe still records `builder.arch: amd64` |

## Definition of Done

- [ ] committed `config/deploy.yml` contains host `138.201.118.229`, both Public site names, image `shved270189/image_compressor`, registry username `shved270189`, `proxy.ssl` enabled, service `image_compressor`, `builder.arch: amd64`, `proxy.app_port: 8000`, and `proxy.healthcheck.path: /api/health`
- [ ] the file contains no password value or private-key material
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
