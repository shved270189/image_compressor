# Implemented browser acceptance — image-size-limit — 2026-09-13

Status: PASS — T7 acceptance on Desktop Chrome via Chrome DevTools at
http://localhost:5173 against the live Vite proxy and FastAPI on :8000.
No browser-test runner was added.

| Environment | Scenario | Actual result |
|---|---|---|
| Desktop Chrome, 360×800 CSS px | Size limit radios sit left of the number; `documentElement.scrollWidth === 360` | PASS; no horizontal page overflow |
| Desktop Chrome, 1280×800 CSS px | Same form; `scrollWidth` 1265 inside `innerWidth` 1280 | PASS; no horizontal page overflow |
| Desktop Chrome | Keyboard focus on Size limit number and both Mb/Kb radios; `:focus-visible` outline solid | PASS |
| Desktop Chrome | Reduced-motion stylesheet (`prefers-reduced-motion: reduce` zeros animation/transition) present; controls remain usable | PASS |
| Desktop Chrome | Local invalid bound `0`: copy `Ліміт ваги must be a positive number with Mb or Kb or left empty`; `sample.png` and preview kept | PASS |
| Desktop Chrome | Met-limit `0.5` Mb JPEG: one `result.jpg` download, form reset to empty file, empty bound, Mb, JPEG; file input focused | PASS |
| Desktop Chrome | Miss `0.001` Kb JPEG: one further `result.jpg` download; form kept (`noisy.png`, `0.001`, Kb, JPEG, preview); notice `The result is 629 bytes. The size limit was exceeded.` with `role="status"` `aria-live="polite"` | PASS |
| Desktop Chrome | After miss, Size limit and Process remain enabled; no fabricated percentages | PASS |
| Desktop Chrome | Reload after miss restores empty form, no preview, no miss notice | PASS |
| Project owner | Exceeded-notice contrast | ACCEPTED via the existing ink-on-surface pair (`#202b25` on `#fffcf5`); agent-measured 14.3:1. Same tokens the owner accepted for labels and fields on 2026-09-06 |

Loading lock of Size limit is implemented as the existing fieldset `disabled={!file || busy}` plus `disabled={busy}` on the file input. The miss encode completed before a mid-flight snapshot; the lock is the same busy path already accepted for dimensions.

Native Safari/Firefox and real-device checks for this increment were not repeated. Android remains deferred.
