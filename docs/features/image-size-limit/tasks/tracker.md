# Tracker — image-size-limit

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Extra-shrink encoded output to meet a byte bound | domain | Tech Lead | M | — | done |
| T2 | Parse and convert optional size_limit fields | ports | Tech Lead | S | T1 | todo |
| T3 | Signal miss versus met-limit with response headers | ports | Tech Lead | S | T2 | todo |
| T4 | Add Size limit number and unit radios | ui | Tech Lead | S | — | todo |
| T5 | Download on miss or met-limit without stale work | ui | Tech Lead | M | T3, T4 | todo |
| T6 | Extend smoke coverage for the size-limit contract | tests | Tech Lead | S | T3, T4 | todo |
| T7 | Verify browser acceptance of Size limit and miss | tests | Tech Lead | M | T5 | todo |
| T8 | Document the optional size-limit workflow | docs | Tech Lead | S | T6, T7 | todo |

**Total:** 8 tasks, ~4 person-days.
