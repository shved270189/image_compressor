---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-06"
feature_size: M
ticket: "N/A"
---

# 0002 — Load HEIC through the Pillow plugin

- **Status:** Accepted
- **Date:** 2026-09-06
- **Deciders:** Project owner and Tech Lead

## Context

The spec requires static JPEG, PNG, WebP and HEIC input, including the designated HEIC primary image and ordinary 8-bit HDR output. The installed Pillow 12.3.0 environment has no registered HEIC decoder. HEIC support must fit the existing Pillow transformation pipeline and local application image.

## Decision drivers

- Cover all required input formats without a separate processing service.
- Select the primary image without mistaking additional HEIC images for animation.
- Verify decoder behavior and packaging before tasks.

## Considered options

1. Register pillow-heif as a Pillow plugin and reuse the common Pillow pipeline.
2. Use pillow-heif directly in a separate HEIC loader, then pass the selected decoded image into Pillow.

## Decision outcome

Use the pillow-heif Pillow plugin. Register and configure it at application initialization, retain a strict accepted-format boundary, and process only the primary static image. HEIC validation must distinguish additional still images from animation rather than blindly rejecting the plugin's multi-frame flag. Disable unused thumbnail, depth and auxiliary handling without removing alpha needed by the primary image.

## Consequences

**Positive.** JPEG, PNG, WebP and HEIC use one image-processing pipeline and the existing Pillow APIs.

**Negative.** Plugin-specific primary-image, orientation, multi-image and native-resource behavior needs explicit verification. Native decoder packaging becomes part of the application image's dependency checks.

**Neutral.** The direct-loader alternative remains technically viable but adds a distinct loading path. It was not selected. Package availability does not prove HDR, color or cleanup behavior.

**ADR gate.** Legitimate alternatives and cross-module delivery impact: image-processing behavior and the native dependencies shipped in the application image.

## Links

- [Spec](../spec.md), AC-07, AC-09, AC-10 and AC-12.
- [SAD](../sad.md), §4, §7 and §11.
- [ADR 0003](./0003-preserve-compatible-color-profiles.md).
- [Pillow plugin documentation](https://pillow-heif.readthedocs.io/en/latest/pillow-plugin.html).
- [Plugin source](https://pillow-heif.readthedocs.io/en/latest/_modules/pillow_heif/as_plugin.html).
- [Published 1.6.0 packages](https://pypi.org/project/pillow-heif/1.6.0/).
