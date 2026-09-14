---
id: T7
title: "Document the later publish command"
layer: "docs"
deps: ["T2"]
blocks: []
acs: ["AC-05"]
files_hint: ["README.md", "docs/architecture-map.md"]
owner: "Tech Lead"
estimate: "S"
context_budget: "S"
status: "todo"
---

# T7 — Document the later publish command

## Place in the sequence

- **Blocked by:** T2 — Record Deploy configuration with locked host facts · **Blocks:** none · **Wave:** 2, parallel with T3 after the recipe exists.
- **Lane:** own lane (`README.md`, `docs/architecture-map.md`). Do not run the documented command.

## Why (user story)

> **As a** Project owner
> **I want** the root README to document exactly `bundle exec kamal deploy` as the later command
> **So that** this step does not itself publish, but I know what to run later.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task writes that later command into the root README and records that the recipe now exists.

## Inlined context

> The root README must contain exactly this later command and must not present the Configuration check as a publish. `bundle exec kamal setup` is out of scope (spec §3).
>
> — `contracts/cli.md, laterPublish, abridged` · full text: [cli.md](../contracts/cli.md)

> README documents `bundle exec kamal deploy` only as the later publish command, not as the check.
>
> — `adr/0002-prove-recipe-with-offline-pytest-check.md, Decision outcome, abridged` · full text: [adr/0002-prove-recipe-with-offline-pytest-check.md](../adr/0002-prove-recipe-with-offline-pytest-check.md)

> **Hard rule:** Running the live publish, buying or provisioning the host, pointing DNS, or issuing certificates — the owner chose configuration-only. Bootstrapping Docker or the reverse proxy on the host (`kamal setup`) — the later command is deploy only.
>
> — `spec.md §3, Non-goals, abridged` · full text: [spec.md](../spec.md)

> Today's README still says server addresses, registry, secrets, domain and live deployment require a later deployment task. Architecture map still says `config/deploy.yml` is absent.
>
> — `README.md, Scope and decisions` and `docs/architecture-map.md, intro, abridged` · full text: [README.md](../../../../README.md) · [architecture-map.md](../../../architecture-map.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

- `laterPublish` → invocation `bundle exec kamal deploy`. Mutating: Yes — live publish. **This increment must not run it.** Flags: none. No destination flag (`-d`), no extra environment. One production host.
- `laterPublish` has no exit-code contract in this increment because it is not run.
- The Configuration check remains `uv run pytest`; it is not a publish.

— `contracts/cli.md, command laterPublish, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-05 — happy

> **Given** Deploy configuration exists,
> **When** the Project owner reads the root README,
> **Then** they see exactly one later publish command, `bundle exec kamal deploy`, and this step does not itself publish.
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Update `README.md` so the later publish command is exactly `bundle exec kamal deploy`
- [ ] Do not document `kamal setup` as this step's command
- [ ] Do not present `uv run pytest` as a publish
- [ ] Replace the architecture-map claim that `config/deploy.yml` is absent with the committed recipe
- [ ] Do not execute `bundle exec kamal deploy`

## Edge cases

| Case | Behaviour |
|---|---|
| README lists several publish commands | Forbidden — exactly one later command |
| README treats the Configuration check as going live | Forbidden |
| `bundle exec kamal setup` documented as required now | Out of scope |

## Definition of Done

- [ ] root `README.md` contains exactly `bundle exec kamal deploy` as the later publish command
- [ ] this increment does not run that command
- [ ] `docs/architecture-map.md` no longer claims `config/deploy.yml` is absent
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
