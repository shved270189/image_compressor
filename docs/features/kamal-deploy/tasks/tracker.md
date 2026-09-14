# Tracker — kamal-deploy

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Ignore the Secrets file in git | infra | Tech Lead | S | — | done |
| T2 | Record Deploy configuration with locked host facts | infra | Tech Lead | S | — | done |
| T3 | Add a throwaway Secrets file fixture | tests | Tech Lead | S | T1 | done |
| T4 | Implement the offline Configuration check success path | ports | Tech Lead | M | T2, T3 | todo |
| T5 | Fail the Configuration check with named missing fields and secrets | tests | Tech Lead | M | T4 | todo |
| T6 | Reject committed secrets and production-target mismatch | tests | Tech Lead | S | T1, T4 | todo |
| T7 | Document the later publish command | docs | Tech Lead | S | T2 | todo |
| T8 | Keep the compression form and existing smoke unchanged | tests | Tech Lead | S | T2 | todo |

**Total:** 8 tasks, ~4 person-days.
