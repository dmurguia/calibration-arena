# Calibrated

## Company marketing site

The separate company website lives in [`marketing/`](marketing/README.md). It has two reviewable homepage directions, enterprise and approach pages, a working practice-case excerpt, and a saved JEV persona comparison. It runs independently of the accounting app, without API keys or npm dependencies:

```bash
cd marketing
npm run dev
```

Open [the site](http://127.0.0.1:4317/) or [compare both directions](http://127.0.0.1:4317/review/). The intended company domain is `calibrated.co`; this local preview does not publish or change DNS.

## Accounting workspace

The current product is a prompt-first accounting workspace: choose a work type, compare two anonymous drafts, make your judgment, and keep the result in Notebook.

See [the product decision](docs/pilot/DECISIONS.md), [the cohort and credential runbook](docs/pilot/RUNBOOK.md), and [verification](docs/pilot/QA.md).

Start with `backend/.env.pilot.example`. Explicit authored samples work without credentials. Live prompting supports server-side OpenRouter configuration, or a temporary loopback-only [Codex and Claude Code bridge](docs/pilot/LOCAL-MODELS.md) using existing CLI sign-ins. Browser-bound identity is implemented; Clerk is an explicitly deferred cross-device upgrade.

## Local dev

```bash
make dev-backend    # uvicorn :8000, SQLite in backend/
make dev-frontend   # vite :5173, /api proxied to :8000
make test           # backend pytest
make build          # frontend production build
```

The public benchmark boards (`/benchmarks`) are built from the JSON under `benchmarks/` by `backend/pipeline/benchmarks.py` and `backend/pipeline/boards.py` (`make benchmarks-validate`, `make benchmarks-build`).

## Docs

- `docs/pilot/` — current product: decisions, runbook, QA, local and hosted setup
- `docs/DEPLOY.md` — Railway (API) and Vercel (frontend)
- `docs/PRD.md`, `docs/TICKETS.md` — product requirements and work log (parts predate the accounting pivot)

## Retired prototype

The original "Benchmark Stadium" / Design Arena prototype (four-model tournament, synthetic seeded votes, email-code login, `ARENA_LEGACY_API`) was removed from the tree. It is in git history before commit `cec8f89`; `docs/ARCHITECTURE.md` carries the pointer. Only the Bradley–Terry ratings math survived, as `backend/app/pilot_ratings.py`.
