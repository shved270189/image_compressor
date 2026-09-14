---
status: Draft
owner: "Project owner"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-13"
feature_size: S
---

# Spec — kamal-deploy

> **Glossary:** [CONTEXT.md](./CONTEXT.md)
> **Sources:** [Idea brief](../../idea-brief.md), [roadmap](../../roadmap.md), [architecture map](../../architecture-map.md), [ADR 0002](../../adr/0002-single-service-and-kamal.md), [ADR 0001](../../adr/0001-stack-and-development-tools.md), [README](../../../README.md), `Gemfile`, `Dockerfile`, `.github/workflows/ci.yml`, `.gitignore`, confirmed interview, clarify sweep.
> **Route:** quick.

## 1. Context

The Project owner can already process one image on a local single-page form. The application image exists. There is no committed publish recipe, so the owner cannot run one later command to put that form on their own host when they are ready. Live publishing and buying a host are outside this step.

The trigger is that the local-only roadmap left public hosting out of scope, while the owner now wants the repository to be publish-ready. There is no launch deadline for going live.

The committed approach is a complete self-host publish recipe in the repository, with real non-secret host facts, secret values only in the local ignored Secrets file, a later publish command documented in the root README, and a local Configuration check that reads the recipe without contacting the production host or the container registry. Adjacent tools offer dry-run or plan-without-apply on managed hosts; they do not treat “recipe plus offline check for a future owner-supplied host” as the finished deliverable. A green Configuration check does not prove the first live publish will succeed; that residual risk is accepted.

Traceability: interview facts are host `138.201.118.229`, Public site names `image.bondev.eu` and `www.image.bondev.eu`, image `shved270189/image_compressor`, registry username `shved270189`, HTTPS on, image architecture amd64, service name exactly `image_compressor` (not `bondev_site` and not the registry-prefixed image name). The already-accepted one-application-service production decision fixes the reverse-proxy target port at 8000 and the health-check path at `/api/health` (a pasted 3000 and `/` were rejected). The committed recipe may contain environment-variable names, including the registry-password name; secret values live only in `.kamal/secrets`, which this step ignores in git. The later publish command is `bundle exec kamal deploy`. CI gains no new job; the existing test suite may cover the Configuration check with a throwaway secrets fixture. The compression form does not change.

## 2. Goals

- Give the Project owner a complete Deploy configuration with the real non-secret host facts so a later publish command has somewhere to aim.
- Prove that recipe locally with a Configuration check that does not contact the production host or the container registry.
- Keep secret values and live publish out of this step and out of the committed repository.

## 3. Non-goals

- Running the live publish, buying or provisioning the host, pointing DNS, or issuing certificates — the owner chose configuration-only.
- Bootstrapping Docker or the reverse proxy on the host (`kamal setup`) — the later command is deploy only.
- Adding a CI job for the Configuration check or auto-publishing after a green check — existing CI stays as it is. The existing test suite may still cover the check with a throwaway secrets fixture that is not production secrets.
- A second environment, extra sidecar services, or a second publish recipe.
- Changing the Image owner's form, processing limits, download behaviour, or cleanup.
- Pushing the application image to the registry in this step.

## 4. User stories

### US-01: Record deploy configuration
**As a** Project owner
**I want** Deploy configuration to record the known host, both Public site names, image name, registry username, HTTPS, service name `image_compressor`, image architecture amd64, the application's existing listening port, and the application's existing health-check path
**So that** a later publish command has a complete non-secret recipe.

### US-02: Keep secrets local
**As a** Project owner
**I want** registry password, SSH private key and other secret values kept only in the Secrets file, while the committed recipe may contain environment-variable names
**So that** the committed repository never contains those values.

### US-03: Run configuration check
**As a** Project owner
**I want** to run the Configuration check on my machine
**So that** I know the recipe is readable and complete without contacting the production host or the container registry.

### US-04: See a missing-field failure
**As a** Project owner
**I want** the Configuration check to fail and name each missing required field or secret in glossary terms
**So that** I never treat an incomplete recipe as ready.

### US-05: Read the later publish command
**As a** Project owner
**I want** the root README to document exactly `bundle exec kamal deploy` as the later command
**So that** this step does not itself publish, but I know what to run later.

### US-06: Leave the compression form unchanged
**As an** Image owner
**I want** the single-image form to keep today's selection, limits, download and cleanup behaviour
**So that** preparing Deploy configuration does not change compress-and-download.

## 5. Acceptance criteria

### AC-01 (US-01) — happy
**Given** the Project owner knows the production host address, both Public site names, image name and registry username,
**When** they record Deploy configuration,
**Then** the recipe names those facts, enables HTTPS for both Public site names, sets service name to `image_compressor`, sets image architecture to amd64, uses the application's existing listening port and existing health-check path, and the Project owner can see those values in the repository.

### AC-02 (US-02) — domain invariant
**Given** Deploy configuration is recorded,
**When** anyone inspects the committed repository,
**Then** no registry password value, SSH private key or other secret value is present; environment-variable names may appear; secret values exist only in the Project owner's Secrets file, which git ignores.

### AC-03 (US-03) — happy
**Given** Deploy configuration is complete and the Secrets file is present with the required registry password,
**When** the Project owner runs the Configuration check,
**Then** the check reports success and does not contact the production host or the container registry.

### AC-04 (US-04) — error
**Given** a required recipe field is missing (host address, either Public site name, image name, registry username, HTTPS enabled, service name `image_compressor`, image architecture amd64, listening port, or health-check path) or the required registry password is missing from the Secrets file,
**When** the Project owner runs the Configuration check,
**Then** the check fails and names each missing required field or secret in glossary terms; it does not report success.

### AC-05 (US-05) — happy
**Given** Deploy configuration exists,
**When** the Project owner reads the root README,
**Then** they see exactly one later publish command, `bundle exec kamal deploy`, and this step does not itself publish.

### AC-06 (US-06) — authorization
**Given** an Image owner using the compression form, or anyone without the Secrets file,
**When** they look for a publish or Configuration check action on that form,
**Then** the application provides no such action; host facts in the recipe are not a capability of the form.

### AC-07 (US-06) — cross-context
**Given** the existing single-image form and processing path,
**When** Deploy configuration is added,
**Then** Image owner still processes one image per operation with the same selection, limits, download and cleanup behaviour; no persistent image store is added.

### AC-08 (US-01) — domain invariant
**Given** the already-built application image uses its established listening port and health-check path,
**When** Deploy configuration is recorded,
**Then** the recipe's reverse-proxy target port and health-check path match that image; a different port or path violates the production-target invariant.

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Configuration check runtime | ≤ 30 s on the Project owner's machine | wall clock of the documented check command |
| Host and registry contact during check | 0 connections to the production host and 0 connections to the container registry | no session or TCP to the recorded host address or the registry while the check runs |
| Secret leakage | 0 secret values in committed files; environment-variable names are allowed | committed tree contains no password values or private-key material; the registry-password name may appear |
| Recipe completeness | 100% of required non-secret fields and the required registry password present or the check is not successful | Configuration check outcome |

Application form latency, throughput and public uptime are N/A: this step does not publish the site.

## 6.1 Security / privacy

- **Data classification:** internal for host address, Public site names, image name, service name and image architecture (they become public in git); confidential for registry password and SSH private key.
- **Personal data touched:** none new in the form; no accounts.
- **AuthZ/AuthN impact:** only a Project owner with the Secrets file can run the Configuration check and the later publish; the Image owner form gains no publish capability.
- **Abuse cases:**
  - Pre-launch targeting of the committed host address before live hardening — accepted residual; this step does not harden the host.
  - A green Configuration check treated as proof that DNS, certificates or image pull will work — the check must not claim that; first live publish may still fail.
  - Secrets present on the machine that wrote the recipe but absent on the machine that later publishes — the later command fails loudly; this step does not copy secrets. SSH private key is not required in the Secrets file; a missing key on the publishing machine is this same class of failure.
- **Security review:** N/A — no new application account boundary or new PII; public host facts in git are an accepted residual.

## 7. Metrics / KPIs

Acceptance indicators rather than usage analytics. Baseline for each new check is 0. All targets are due before this feature is declared complete.

- Configuration check success — target: 1 passing run in the existing test suite with a throwaway secrets fixture present.
- Configuration check missing-secrets failure — target: 1 failing run in that suite that names the gap when the Secrets file is absent.
- Existing image-processing smoke — target: unchanged pass after this increment.
- Secret leakage — target: 0 secret values in committed files.

No analytics collection is added. No new CI job is added.

## 8. Open questions

- [ ] Which SSH user will the later publish use on `138.201.118.229`? Default now: not required for the Configuration check. — owner: Project owner, due: before first live publish
- [ ] Do both Public site names already point at that host, and will certificates be issued only at publish time? Default now: not verified in this step. — owner: Project owner, due: before first live publish

## Test plan

Deploy configuration for the existing one-service image, local Configuration check, no live publish. Size S and route quick from `.size` / `.route`. Levels: unit, integration, contract, e2e-through-UI. No component, visual-regression or load suite. Configuration check tests run in the existing pytest suite with a throwaway secrets fixture; they add no new CI job.

### AC coverage

| AC (spec.md §5) | Test name (intent-based) | Level | Expected outcome |
|---|---|---|---|
| AC-01 | recipe records host, both site names, image, registry username, HTTPS, service name, arch, port and health path | contract | Values match the interview facts, service name `image_compressor`, arch amd64, and the established image port/health path |
| AC-02 | committed tree contains no secret values | integration | Secrets file is gitignored; password values and private-key material absent from git; environment-variable names may appear |
| AC-03 | configuration check succeeds without contacting the host or registry | integration | Success reported; no connection to the recorded host or the container registry |
| AC-04 | missing secret or required field fails the check with a named gap | integration | Failure names each missing field or secret in glossary terms; not success |
| AC-05 | root README documents exactly one later publish command | contract | The command is `bundle exec kamal deploy`; this increment does not publish |
| AC-06 | compression form exposes no publish action | e2e-through-UI | Form still only selects, sets limits, processes and downloads |
| AC-07 | existing image-processing smoke still passes | integration | Health, page, assets and process behaviour unchanged |
| AC-08 | recipe port and health path match the application image | contract | A different port or path is not accepted as the production target |
