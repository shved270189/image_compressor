---
status: Draft
owner: "Project owner"
updated_at: "2026-09-05"
depth: medium
---

# Idea brief — image-compressor

## 1. Raw idea

A one-page site where a user can compress a single image, change its size (height and width), set a limit on the new file size (MB), and optionally convert it to another format.

## 2. Problem

The image needs to be prepared to the chosen width, height, file-size, and format requirements. If the user sets a file-size limit, meeting that limit is the top priority.

## 3. Users

The project owner uses the site for their own work. Usage frequency is not yet defined.

## 4. Why now

There is a personal need for this tool. No separate occasion or launch deadline was named.

## 5. Out of scope

- Batch processing: the user works with one image.
- Cropping and stretching: proportions are preserved.
- History and re-download from the server: the result is needed only for the current operation.
- Saved parameter presets: a single ordinary form was chosen.

## 6. Risks

- Weakest point: a very small limit can make the image unusable. Minimum acceptable quality and dimensions are not yet defined.
- Specified width and height mean maximum bounds. The user may mistakenly expect exact dimensions.
- Deleting server files after delivery needs a separate rule for an interrupted download.

## 7. Recommendation

One page with a form: the image, the required parameters, and a process button. Keep proportions without cropping; allow automatic dimension reduction to meet a file-size limit. Show actual dimensions, file size, and a download button for the result. Server-side processing is allowed; the original and the result are deleted after delivery.

File-size limit in MB, maximum height, and maximum width are independent optional parameters. The user may set any combination of them or skip all three. An omitted parameter imposes no constraint; image proportions are preserved even when only width or only height is set.

Alternatives considered: a step-by-step form and a form with saved presets. An ordinary form was chosen.

The page and form should feel modern and easy to use. They need a clear composition, quality typography, a coherent palette, considered spacing, and a clear primary action. "Ordinary form" means one screen without a step wizard, not a basic or bland design. The form remains the main element of the page.

Animations are part of the experience: page appearance, button and field reactions, image selection, processing state, and result appearance. Motion emphasizes action and state change. Animations must not delay input or result download, must not cause layout jumps, and must not show fabricated progress.

The design must be equally usable on phone and computer. Required: understandable labels and errors, readable contrast, keyboard control, and a visible focus. With `prefers-reduced-motion`, remove decorative motion while keeping understandable state changes. Before finishing the UI, check appearance, animations, and the full path from image selection to result at both screen sizes.

## 8. Open questions

- Project owner: which input and output formats are needed?
- Project owner: what is the largest input file that must be processed?
- Project owner: what minimum quality and dimensions are acceptable for the sake of the limit?
- Project owner: what should happen when the limit is unattainable or the download is interrupted?
