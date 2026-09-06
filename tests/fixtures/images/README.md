# Image fixtures

Immutable decoder controls copied from the pinned, hash-verified feasibility fixtures. Source URLs and original hashes are recorded in `docs/features/image-resize-convert/_audit/feasibility-images.py`. `arrow-native.png` is the independent Apple ImageIO orientation reference documented in the feasibility audit. No fixture is user-uploaded data.

| File | SHA-256 |
|---|---|
| DEMO_BT2100_HLG.heic | `75481b8fa596cedcdc782f593d946624c34a96196c02eb1ee4abaab8db45175e` |
| RGBA_10__128x128.heif | `ca7bc70f1d8b1103e7094c3758a70991ad31e2cbcabb02f4ec7e79e5a6d4bc5f` |
| RGB_10__128x128.heif | `7fbf1573c1e5c1693953b31bb287327c53eaefa74a6f1324e7391a08b3ed1e73` |
| RGB_12__128x128.heif | `92c048d4bead7eebd3e0da5cb13a2e286cccbde3acb23580ee9c5f6b4cfde812` |
| arrow-native.png | `5a89ac8a4e46db45db464b02123c7c579dedbc9cbcd8055645c63c05e674e46a` |
| arrow.heic | `73f604d7353df4848505a1f45a5517f736857fe047372f95c2f3d671df92c22c` |
| guitar_cw90.hif | `f0d5e88be07b9d70a3715218ca612ccf45b126e5b4b42172dce14a62d2099932` |
| starfield_animation.heic | `fbf31cd9aa6fc4c997d7eb2ea05541627bf3dbcb4115b7d453f63dcd1ec4fb26` |
| zPug_3.heic | `daf1515c651e15968ad6ec142e443759156fee76c65715e4f5713cf1ad072774` |
| oriented-exif6.jpg | `5bf18f02508f59dc92ce04a4988719103911ab8b438032c1d6c11d5a11d3203e` |

`oriented-exif6.jpg` is a synthetic 12×8 JPEG with EXIF orientation 6 (left strip cyan, remainder red). Pillow/libjpeg decode it to 8×12 with the cyan strip on top. It is a browser Preview/download orientation control, not a camera file.

## Generated track controls

`generate_timelines.py` uses installed FFmpeg/libx265 to encode three independent test-pattern samples. It appends their movie/fragments to a static HEIC primary and relocates initial chunk offsets. The gallery adds an empty edit list. Both primary images decode with Pillow/libheif; both HEVC tracks decode without errors using FFmpeg `-map 0:1` (`-ignore_editlist 1` for the gallery). These are synthetic, independently encoded controls, not camera files. FFmpeg is fixture-generation tooling only, not a runtime/test dependency.

## Color model controls

`cmyk.icc` and `gray.icc` are macOS ColorSync Generic CMYK and Generic Gray profiles. Independent ImageCms anchors: CMYK(100,50,0,20) becomes sRGB(137,165,196); Gray128 becomes sRGB146.

- `cmyk.icc` SHA-256: `0c8a584b288a306eac9e1d3f1e68bc1b64331c717ceb051420e6257f17b3509a`.
- `gray.icc` SHA-256: `0ef4da994a2b833d54af2d4ecbb2c6654b7198ad9e6bd80ed86d684e54fd37d3`.
