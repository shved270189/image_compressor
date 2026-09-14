---
id: T8
title: "Keep the compression form and existing smoke unchanged"
layer: "tests"
deps: ["T2"]
blocks: []
acs: ["AC-06", "AC-07"]
files_hint: ["tests/test_smoke.py"]
owner: "Tech Lead"
estimate: "S"
context_budget: "M"
status: "todo"
---

# T8 — Keep the compression form and existing smoke unchanged

## Place in the sequence

- **Blocked by:** T2 — Record Deploy configuration with locked host facts · **Blocks:** none · **Wave:** 2, parallel with T3 and T7 once the recipe exists.
- **Lane:** own lane (`tests/test_smoke.py`). Do not edit `frontend/` or `backend/`.

## Why (user story)

> **As an** Image owner
> **I want** the single-image form to keep today's selection, limits, download and cleanup behaviour
> **So that** preparing Deploy configuration does not change compress-and-download.
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task proves the form gained no publish or Configuration check action and that existing processing smoke still passes.

## Inlined context

> **Chosen:** Declare `target_surfaces: [cli]`. The Image owner form and the FastAPI application are unchanged, so this feature does not add `web-frontend` or `backend-service`.
>
> — `adr/0001-declare-cli-surface-for-configuration-check.md, Decision outcome, abridged` · full text: [adr/0001-declare-cli-surface-for-configuration-check.md](../adr/0001-declare-cli-surface-for-configuration-check.md)

> The existing `backend/` and `frontend/` trees are out of scope.
>
> — `sad.md §5, Internal decomposition, abridged` · full text: [sad.md](../sad.md)

> alt Image owner processes one image → select image, set limits, process; no persistent image store; download result with existing limits and cleanup. else anyone looks for a publish or Configuration check action on the form → no such action, host facts are not a form capability.
>
> — `sad.md §6, Cross-cutting: form has no publish action, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** HTTP validation stays in `backend/main.py`; this feature does not add image functions or frontend behaviour. Changing the Image owner's form, processing limits, download behaviour, or cleanup is a non-goal. No persistent image store is added.
>
> — `sad.md §2, Conventions` and `spec.md §3, Non-goals, abridged` · full text: [sad.md](../sad.md)

> US-06 / AC-06 / AC-07: the Image owner form exposes no Configuration check and no publish action. No CLI flag, HTTP path, or UI control is added for publish. Existing `POST /api/v1/images/process` is unchanged and is not part of this contract.
>
> — `contracts/cli.md, Compression form, abridged` · full text: [cli.md](../contracts/cli.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [cli.md](../contracts/cli.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. The compression form is out of this CLI surface. Do not add a publish command, flag, or HTTP path.

## Acceptance criteria

### AC-06 — authorization

> **Given** an Image owner using the compression form, or anyone without the Secrets file,
> **When** they look for a publish or Configuration check action on that form,
> **Then** the application provides no such action; host facts in the recipe are not a capability of the form.
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — cross-context

> **Given** the existing single-image form and processing path,
> **When** Deploy configuration is added,
> **Then** Image owner still processes one image per operation with the same selection, limits, download and cleanup behaviour; no persistent image store is added.
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Extend `tests/test_smoke.py` to assert `frontend/src/App.tsx` has no publish, Configuration check, or Kamal deploy action
- [ ] Keep existing smoke cases: health, page, assets, process behaviour, Size limit copy
- [ ] Do not modify `frontend/` or `backend/`
- [ ] Do not add a datastore or image-result lookup

## Edge cases

| Case | Behaviour |
|---|---|
| Form control labelled publish / deploy / Configuration check | Must not exist |
| Anyone without the Secrets file | Still no publish action on the form |
| Existing Size limit and HEIC copy tests | Still pass |
| Persistent image store | Must not be added |

## Definition of Done

- [ ] `uv run pytest tests/test_smoke.py` passes, including a new assertion that the form exposes no publish or Configuration check action
- [ ] existing health, page, assets and process smoke behaviour is unchanged
- [ ] `frontend/` and `backend/` are untouched
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
