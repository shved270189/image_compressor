# Changelog — image-resize-convert

## image-resize-convert — resize and convert one static image

**What:** A local single-page form now resizes and converts one static JPEG, PNG, WebP or HEIC image to JPEG, PNG or WebP. Optional maximum width and height keep aspect ratio without cropping or enlargement. Successful processing downloads the result automatically and resets the form.

**Why:** The foundation had no image-processing behavior. The owner needed one local workflow to prepare a picture under independently optional dimension limits and a chosen format ([spec](./spec.md) §1–§2). Processing stays on the existing web frontend and backend service ([ADR-0001](./adr/0001-extend-web-frontend-and-backend-service.md)), HEIC uses the Pillow plugin ([ADR-0002](./adr/0002-load-heic-through-pillow-plugin.md)), compatible color interpretation is preserved ([ADR-0003](./adr/0003-preserve-compatible-color-profiles.md)), and the result is returned in the current operation with no lookup ([ADR-0004](./adr/0004-return-results-within-the-current-operation.md)).

**How to use:** Open the app, choose a non-empty image up to 20 MB, optionally set maximum width and/or height, choose JPEG (default), PNG or WebP, then process. Preview stays local. The server contract is `POST /api/v1/images/process` ([openapi.yaml](./contracts/openapi.yaml)).

**Operational notes:**
- Migration: none. There is no datastore.
- Feature flag / config: none. Limits are compiled into the application (20,000,000 file bytes, 40,000,000 decoded pixels, multipart body 20,065,536 bytes).
- Rollback: revert the deploy or the feature commits. No stored originals or results to purge.
- Runtime: the application image includes Pillow 12.3.0 and pillow-heif 1.6.0. Restart the backend after the first production frontend build so it serves `frontend/dist`.
- Scope: local use. Public hosting and Kamal live deployment remain out of this increment.

**Acceptance criteria delivered:** AC-01 … AC-16 — selection and local preview, proportional bounds, format conversion, HEIC primary/HDR notice, validation and content rejection, one automatic download with form reset, and no later retrieval of originals or results.
