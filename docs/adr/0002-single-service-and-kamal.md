# ADR 0002: One application service deployed with Kamal

Status: Accepted

Date: 2026-09-05

## Context

The owner selected one service for the backend and built frontend, and Kamal for deployment. The project has no source code or deployment configuration yet.

## Decision

- Organize the repository into `backend/` and `frontend/`. Use `backend/main.py` as the FastAPI entry point. Add image processing functions in `backend/images.py` when implementing the compression feature, not as an empty scaffold abstraction.
- Browser code calls relative `/api` paths using fetch. In development, Vite proxies `/api` to `http://127.0.0.1:8000`. Use the Vite page at `http://localhost:5173`.
- Serve built `frontend/dist/` using FastAPI's frontend support in production. Allow the backend API to start before a frontend build exists in development. Do not add a separate production frontend server or client-side router for a single page.
- Build a single multi-stage Docker image: Node.js builds the frontend, then a Python runtime image contains the backend, its locked runtime dependencies, and the frontend build. Run as a non-root user. Start Uvicorn on `0.0.0.0:8000`; development reload is disabled in production. Logs go to stdout/stderr.
- Deploy with the Kamal gem declared in `Gemfile`. The future `config/deploy.yml` sets `proxy.app_port: 8000` and `proxy.healthcheck.path: /api/health`. Server addresses, domain, registry and credentials belong to a separate deployment configuration stage. Do not invent values or deploy during survey or scaffold.

## Interfaces and conventions

The skeleton exposes `GET /api/health`, returning status 200 with `{"status":"ok"}`. Unknown `/api` paths return 404 rather than the frontend page. The health endpoint serves the local smoke test and the Kamal proxy check.

HTTP validation belongs at the FastAPI boundary. Use Pydantic input validation and standard FastAPI HTTP errors. Keep image transformation functions independent of HTTP request and response objects. Define the actual upload and compression contract in the feature specification.

React components use local state, native accessible form controls and Tailwind utilities. Use Tailwind's default tokens initially and keep any application theme tokens in the frontend's single CSS entry point. Do not add a component library, global state store or duplicate styling system to the skeleton.

## Consequences

Production requires one application container behind kamal-proxy. Node.js, Ruby and Kamal are not required in the final application image. Docker and registry access are deployment prerequisites, not Python or frontend packages.

The scaffold must prove the built image serves the health endpoint, page and assets. Provisioning infrastructure and a live Kamal deployment are outside scaffold. CI runs build, tests, lint and the container smoke check; it does not deploy automatically.

## Sources

- [FastAPI frontend support](https://fastapi.tiangolo.com/tutorial/frontend/).
- [Kamal installation](https://kamal-deploy.org/docs/installation/).
- [Kamal proxy configuration](https://kamal-deploy.org/docs/configuration/proxy/).
