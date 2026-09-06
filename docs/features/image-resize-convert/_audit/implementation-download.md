# Submit and download implementation acceptance

2026-09-06, implemented production build, Chrome through existing Playwright CLI.

RED: clicking Process image produced no POST. GREEN: local fractional dimension rejected without POST; valid request downloads a complete PNG; Pillow independently decodes 16x8 PNG and 32x16 JPEG retry. One native download per request, matching extension, empty native file input, empty dimensions, JPEG default, disabled parameters, focused file input, and zero active Blob URLs after reset. Same-file reselection works.

A gated 422 response verifies all controls disabled and repeated programmatic submits ignored. Structured validation displays only msg and maps known loc fields; input/ctx sentinels stay absent. Error retains selection; explicit retry succeeds. A controlled streaming Response verifies no download before complete body, retained input after interrupted body, and no stale download after pagehide invalidation even when the stale body subsequently completes.

Keyboard Tab order reaches width, height, format and submit; Enter downloads. Reduced motion removes animation. Both 360 and 1280 widths have no page overflow. A 500-character unbroken error first failed the 360px check; wrapping fixed it and the regression passed.

Native Safari also downloads a complete 637-byte JPEG, resets the form and focuses file selection. This is a happy-path check, not the complete T11 matrix.

Build/typecheck, ESLint, Ruff and host pytest pass (180 tests including concurrent backend review regressions). Other browser acceptance and owner review remain tracked by T11.
