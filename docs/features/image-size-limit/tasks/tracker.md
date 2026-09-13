# Tracker — image-size-limit

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Extra-shrink encoded output to meet a byte bound | domain | Tech Lead | M | — | done |
| T2 | Parse and convert optional size_limit fields | ports | Tech Lead | S | T1 | done |
| T3 | Signal miss versus met-limit with response headers | ports | Tech Lead | S | T2 | done |
| T4 | Add Size limit number and unit radios | ui | Tech Lead | S | — | done |
| T5 | Download on miss or met-limit without stale work | ui | Tech Lead | M | T3, T4 | done |
| T6 | Extend smoke coverage for the size-limit contract | tests | Tech Lead | S | T3, T4 | done |
| T7 | Verify browser acceptance of Size limit and miss | tests | Tech Lead | M | T5 | done |
| T8 | Document the optional size-limit workflow | docs | Tech Lead | S | T6, T7 | done |

**Total:** 8 tasks, ~4 person-days.

Review follow-up 2026-09-13 (`_review/review-2026-09-13.md` F1–F4): Size limit help copy, architecture-map D2, AC-10 new-file/stale abort, AC-11 live lock and failure retry. All eight tasks remain done.
