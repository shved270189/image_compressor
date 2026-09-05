---
status: Accepted
owner: "Tech Lead"
reviewers: []
updated_at: "2026-09-06"
feature_size: M
ticket: "N/A"
---

# 0003 — Preserve compatible color profiles

- **Status:** Accepted
- **Date:** 2026-09-06
- **Deciders:** Project owner and Tech Lead

## Context

The spec requires removal of identifying service metadata while retaining information needed to interpret color correctly. Supported inputs may carry ICC profiles or other color information. A profile describing source pixels can become incorrect after changing their color model.

## Decision drivers

- Preserve the agreed visible color interpretation while removing service metadata.
- Avoid unnecessary loss of colors representable by the input and chosen output.
- Keep the implementation within Pillow and its existing ImageCms capability.

## Considered options

1. Preserve compatible source color profiles, performing a color transformation when the output pixel model requires it.
2. Convert every image into sRGB and emit a matching sRGB profile.

## Decision outcome

Preserve compatible color interpretation instead of converting every image to sRGB. When a pixel color model must change, use ImageCms where applicable and attach only a profile matching the resulting pixels. Apply orientation before removing orientation/service metadata. Remove GPS, camera, EXIF, XMP and textual service metadata. Composite transparency onto white for JPEG and retain alpha for PNG and WebP.

## Consequences

**Positive.** Compatible wide-gamut input does not undergo an unnecessary universal sRGB conversion.

**Negative.** Correctness requires verification across color modes and profile representations. HEIC NCLX-only color information and PNG color information without ICC cannot be silently discarded or falsely relabeled.

**Neutral.** This choice does not promise preservation of the original HDR appearance. Ordinary 8-bit HEIC output remains required. The exact supported color transformations must be proved at the pre-tasks feasibility gate; the gate cannot waive the color requirement.

**ADR gate.** Legitimate alternatives and a shared normalization contract: HEIC decoding and the common image pipeline must agree on the meaning of the pixels and attached color information.

## Links

- [Spec](../spec.md), AC-08–AC-10.
- [SAD](../sad.md), §4, §6, §10 and §11.
- [ADR 0002](./0002-load-heic-through-pillow-plugin.md).
- [Pillow ImageCms](https://pillow.readthedocs.io/en/stable/reference/ImageCms.html).
