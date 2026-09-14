---
id: T1
title: "Ignore the Secrets file in git"
layer: "infra"
deps: []
blocks: ["T3", "T6"]
acs: ["AC-02"]
files_hint: [".gitignore"]
owner: "Tech Lead"
estimate: "S"
context_budget: "S"
status: "todo"
---

# T1 — Ignore the Secrets file in git

## Place in the sequence

- **Blocked by:** none · **Blocks:** T3 — Add a throwaway Secrets file fixture, T6 — Reject committed secrets and production-target mismatch · **Wave:** 1, with T2. Land this before any real Secrets file exists.
- **Lane:** own lane (`.gitignore`).

## Why (user story)

> **As a** Project owner
> **I want** registry password, SSH private key and other secret values kept only in the Secrets file, while the committed recipe may contain environment-variable names
> **So that** the committed repository never contains those values.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task adds the git ignore for `.kamal/secrets` so a later Secrets file cannot enter the committed tree.

## Inlined context

> `.kamal/secrets` Secrets file (gitignored; throwaway fixture in tests). `.gitignore` does not yet ignore `.kamal/secrets`; implementation must add that ignore.
>
> — `sad.md §5, Internal decomposition, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Secret values only in `.kamal/secrets`, which git ignores; recipe may contain environment-variable names.
>
> — `sad.md §8, Secrets, verbatim` · full text: [sad.md](../sad.md)

> `.gitignore` does not yet ignore `.kamal/secrets` — Implementation adds the ignore before any real Secrets file is created.
>
> — `sad.md §11, RISK gitignore, abridged` · full text: [sad.md](../sad.md)

> Secret leakage: 0 secret values in committed files; environment-variable names are allowed.
>
> — `spec.md §6, Secret leakage, verbatim` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-02 — domain invariant

> **Given** Deploy configuration is recorded,
> **When** anyone inspects the committed repository,
> **Then** no registry password value, SSH private key or other secret value is present; environment-variable names may appear; secret values exist only in the Project owner's Secrets file, which git ignores.
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `.kamal/secrets` to `.gitignore`
- [ ] Confirm `git check-ignore -q .kamal/secrets` succeeds from the repository root
- [ ] Do not create a real Secrets file in this task

## Edge cases

| Case | Behaviour |
|---|---|
| `.kamal/secrets` is created later on the owner's machine | git ignores it; it is not staged |
| Recipe later contains an environment-variable name such as `KAMAL_REGISTRY_PASSWORD` | Allowed; only values are forbidden |
| SSH private key material | Must not appear in git; the key is not required in the Secrets file |

## Definition of Done

- [ ] `git check-ignore -q .kamal/secrets` exits 0
- [ ] `.gitignore` lists `.kamal/secrets`
- [ ] no `.kamal/secrets` file is committed
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
