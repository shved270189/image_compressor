# ADR 0003: Process images without persistent storage

Status: Accepted

Date: 2026-09-05

## Context

The product handles one image at a time. The brief excludes history and later retrieval, permits server processing, and requires removal of server-side images after transfer. See `docs/idea-brief.md:28` and `docs/idea-brief.md:41`.

## Decision

- Use Pillow for image decoding, resizing and encoding. Supported product formats are decided in the feature specification; Pillow support does not automatically expose every codec to users.
- Accept input through FastAPI `UploadFile`. Its spooled storage can use memory or a temporary file; this is request-scoped storage, not a persistent image repository.
- Keep encoded results in memory for the current response. Close upload handles and image resources and release result references after response completion or interruption, including error paths. Do not log image contents.
- Do not add a database, migrations, object storage, persistent image IDs or a background job queue. No migration task is applicable to this foundation.
- Specify accepted formats, upload byte and pixel limits, minimum quality and dimensions, unattainable target behavior, and interruption handling before implementing the processing endpoint. Apply input limits before expensive image decoding.

## Consequences

There is no image to retrieve after the request lifecycle ends. The processing endpoint must bound resource use and preserve Pillow's protections against excessive decoded image size.

Width, height and file-size constraints remain independently optional. Preserve aspect ratio; width and height are maximum bounds. Reducing dimensions to meet a file-size target is allowed. No cropping, stretching, batch processing or saved presets are part of the agreed product. See `docs/idea-brief.md:28` and `docs/idea-brief.md:43`.

## Sources

- [Product brief](../idea-brief.md).
- [FastAPI UploadFile](https://fastapi.tiangolo.com/tutorial/request-files/).
- [Pillow documentation](https://pillow.readthedocs.io/en/stable/).
