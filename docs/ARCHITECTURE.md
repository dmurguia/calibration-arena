# Engineering architecture

The current product is the accounting workspace ("pilot" path):

- `backend/app/main.py` — FastAPI app, CORS, local-inference boundary, SPA static serving
- `backend/app/routers/pilot.py` — every `/api/pilot/*` route and the `Participant` / `Run` / `Event` tables
- `backend/app/pilot_*.py` — accounts and sessions (`pilot_accounts`, `pilot_clerk`), spend limits (`pilot_limits`, `pilot_usage`), cases and tasks (`pilot_cases`, `pilot_tasks`, `pilot_examples`, `pilot_study`), inference (`pilot_inference` switched by `ARENA_INFERENCE_BACKEND`, with `pilot_direct` and `pilot_local` adapters), audit hashing (`pilot_audit`), the preference leaderboard (`pilot_leaderboard` over `pilot_ratings`, a weighted Bradley–Terry fit with bootstrap CIs)
- `backend/app/db.py` / `config.py` — SQLAlchemy engine (SQLite default, Postgres via `ARENA_DATABASE_URL`), `create_all` plus a small column backfill on startup
- `backend/pipeline/` — `benchmarks.py` and `boards.py` build the public `/benchmarks` boards from `benchmarks/`; `export_pilot`, `audit_pilot`, `import_close_pack`, `pilot_roster` are operator scripts
- `frontend/src/pilot/` — the whole SPA (`Pilot.tsx`, `Benchmarks.tsx`, `Leaderboard.tsx`, `Account.tsx`, `clerk.tsx`); `App.tsx` re-exports `Pilot`

Setup, credentials and hosting: `docs/pilot/LOCAL-AND-HOSTED.md`, `docs/pilot/RUNBOOK.md`, `docs/DEPLOY.md`.

## Retired prototype

The "Benchmark Stadium" / Design Arena prototype that this file used to describe (four-model tournament bracket, calibration traps, credential tiers, synthetic seeded votes, email-code login, vendor product boards, simulated releases) was removed from the repository. Its code, the original v1/v2 write-up and its tests are in git history before commit `cec8f89`:

```bash
git show cec8f89:docs/ARCHITECTURE.md
git show cec8f89:backend/app/services/arena.py
```

Its database tables (`users`, `auth_codes`, `arena_models`, `battles`, `generations`, `matches`, `votes`, `trap_results`, `model_releases`, `rating_snapshots`, `model_ratings`) are no longer created or read; existing deployments may still carry them until dropped by hand.
