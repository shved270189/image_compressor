---
status: Living
updated_at: "2026-09-13"
---

# Domain Context — image-size-limit

## Glossary

- Image owner — The person processing their selected image. NOT an application account or permission role.
- Size limit — Independently optional upper bound on Result file size, entered as a positive float with unit Mb (default) or Kb (1 Mb = 1,000,000 bytes, 1 Kb = 1,000 bytes). NOT the 20,000,000-byte upload cap on Original.
- Maximum dimensions — Independently optional upper width and height bounds in pixels. NOT exact dimensions, cropping or stretching.
- Original — The image file selected for the current operation. NOT a file overwritten by processing.
- Preview — An optional frontend-only representation of the selected original above the form when the browser can display it. NOT the processed result or a server-generated image.
- Result — The processed file ready to download for the current operation. NOT the original or a persistent server file.
