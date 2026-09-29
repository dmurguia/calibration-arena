# Engineering architecture — Benchmark Stadium

**Date:** 2026-08-31 (v2 pivot) · companion to `PRD.md`

## 0. v2 pivot delta (professional work arena)

The v1 skeleton below still describes the bones (one FastAPI process, SQLite,
snapshot pipeline, sandboxed document iframes). The pivot adds:

- **Taxonomy**: `categories.py` now holds two verticals (legal, finance) × four task
  types; `scenarios.py` is the synthetic matter library with structured facts
  (planted issues, expected postings, mapping keys) that generators and traps consume.
- **Generation**: `services/providers/professional.py` replaces the design generator —
  paper-styled work-product documents whose *substance* varies with a latent
  per-model quality level, plus `generate_broken()` for gold-standard trap artifacts.
- **Session shape**: 5 matches per battle — semi1, semi2, a `calibration` trap match
  (scores the rater into `trap_results`, never `votes`), final, third. Trap slots and
  positions are shuffled so nothing leaks which output is broken.
- **Trust layer**: `users.tier` from email domain at signup (free-mail 0 → named 3);
  `votes` carry `weight` (tier), server-side `decision_ms`, and `counted` (timing
  floor, `ARENA_MIN_DECISION_MS`). `ratings.py` fits a **weighted**
  Bradley–Terry; published snapshots read counted, weight ≥ 1 votes only.
- **Reviewer record**: `services/reviewer.py` computes calibration score (traps),
  consensus agreement vs. verified peers on identical (scenario, model-pair) votes —
  well-defined because sample outputs are deterministic — percentile, and badges;
  served at `/api/auth/reviewer`, rendered at `/profile`.
- **Company boards + release drama (BS-16)**: `arena_models.kind`
  (foundation | product | declined) with provenance + submitted version; products are
  drafted and ranked only inside their vertical (`arena.eligible_models`), declined
  vendors surface on boards as empty-chair rows (`LeaderboardOut.declined`).
  `model_releases` records each release with per-board rank movement captured as
  JSON; `services/releases.simulate_release` re-runs a foundation model (strength
  shift → synthetic re-run votes → snapshot recompute → before/after ranks) behind
  `POST /api/releases/simulate`, with `GET /api/releases` feeding the UI's Release
  radar and home banner. Real release detection and vendor submission replace the
  simulate path in production (BS-18). SQLite column backfill for the new
  `arena_models` fields lives in `db._ensure_columns` (Alembic later).

## 1. System shape (v1 baseline)

```
benchmark-stadium/
├── backend/                FastAPI + SQLAlchemy (SQLite default, Postgres-ready)
│   ├── app/
│   │   ├── main.py         app assembly, CORS, SPA static serving
│   │   ├── config.py       env-driven settings; all placeholders live here
│   │   ├── db.py           engine/session; create_all on startup
│   │   ├── models.py       ORM: users, arena_models, battles, generations,
│   │   │                   matches, votes, rating_snapshots, model_ratings
│   │   ├── security.py     stdlib HMAC session tokens + login codes
│   │   ├── categories.py   category registry (code-owned)
│   │   ├── deps.py         auth dependencies (bearer or cookie)
│   │   ├── routers/        auth, catalog, battles, leaderboard
│   │   └── services/
│   │       ├── arena.py    model selection, generation fan-out, bracket FSM
│   │       ├── ratings.py  Bradley–Terry (MM) + Elo scaling + bootstrap CIs
│   │       ├── leaderboard.py  snapshot compute/read
│   │       └── providers/  sample (offline) + live vendor adapters
│   ├── pipeline/           seed.py (roster+synthetic votes), compute_ratings.py (batch)
│   └── tests/              rating math, tournament FSM, full API flow
└── frontend/               Vite + React 18 + TS + Tailwind (mirrors repo's stack)
    └── src/pages/          Home, Login, Battle (vote+reveal), Leaderboard, History
```

Two deploy shapes, no code changes: dev = Vite server (5173) proxying `/api` to
uvicorn (8000); prod = `npm run build`, FastAPI mounts `frontend/dist` and serves the
SPA and API from one process.

## 2. Data model (the important invariants)

```
users ──< battles ──< generations >── arena_models
              │  └──< matches (semi1|semi2|final|third, unique per battle)
              └──< votes >── arena_models (winner/loser)
rating_snapshots ──< model_ratings >── arena_models
```

- **`votes` is append-only truth.** One row per pairwise human choice:
  `(category, winner_model_id, loser_model_id, user_id, battle_id, match_id, synthetic)`.
  Rankings never read anything else. `synthetic=true` marks seeded bootstrap votes so
  they can be down-weighted or aged out without schema changes.
- **`matches` is a tiny FSM.** All four rows are created with the battle; `final`/`third`
  slots stay NULL until both semis are decided, then are filled in the same transaction
  as the deciding vote. `current_match` = first match in order with both slots and no
  winner; the API rejects out-of-order votes (422).
- **Anonymity is server-enforced**, not CSS: generation → model mapping is only
  serialized after `battle.status == "complete"`, and slot positions are shuffled at
  creation so A–D carries no vendor signal.
- **`rating_snapshots`/`model_ratings` are materialized outputs.** The leaderboard API
  is a pure read of the latest snapshot per category — cheap, cacheable, and identical
  no matter which trigger computed it.

## 3. Ratings pipeline

**Fit.** Bradley–Terry by Hunter's MM iteration over (winner, loser) pairs; strengths
normalized to geometric mean 1; one virtual split game per observed pairing as
smoothing so undefeated models stay finite. Displayed score =
`1200 + 400·log10(strength)` (arena-style anchor/scale).

**Uncertainty.** 95% CIs by bootstrap: resample the vote set (default 40 rounds,
`ARENA_CI_ROUNDS`), refit, take the 2.5/97.5 percentiles per model.

**Triggers — one computation, three entry points:**

| Trigger | Path | Role |
|---|---|---|
| Batch CLI | `python -m pipeline.compute_ratings [--category …]` | production/nightly path, backfills |
| Battle completion | FastAPI `BackgroundTasks` → recompute battle's category + overall | board feels live seconds after voting |
| Seed | `python -m pipeline.seed [--reset]` | roster + ~3k synthetic votes + first snapshots |

**Cold start.** Seeding draws a latent per-(model, category) strength
(baseline × lognormal jitter, deterministic), then simulates votes from the implied BT
probabilities. The fitted board therefore recovers a plausible, noisy ordering — not a
hardcoded ranking — and live human votes merge into the same table seamlessly.

At current scale the whole fit is pure Python and sub-second; at real scale you'd move
the background recompute to a worker queue and debounce (see §6).

## 4. Generation providers

`get_provider_for(model)` routes on `ARENA_GENERATION_MODE`:

- **`sample` (default)** — offline generator; each roster model has a persona
  (hue, palette mode, radius, font, flavor: brutalist/glass/neon/editorial/playful/
  retro/minimal/corporate). Per-category template families (website, UI component
  variants, SVG dataviz, playable canvas game, SVG logo system, ASCII art) are
  parameterized by persona + a `Random(f"{model}::{category}::{prompt}")` seed and by
  keywords extracted from the prompt. Output is a self-contained HTML document —
  deterministic per input, visibly different across models. This keeps demo UX honest:
  votes are real judgments over real differences.
- **`live`** — per-model routing by `arena_models.provider`: Anthropic Messages API,
  OpenAI chat completions, Google generateContent, OpenRouter as the catch-all
  (GLM/DeepSeek/Qwen/Grok/…). Shared category system prompts demand a single
  self-contained HTML file; a fence-stripper normalizes output. All keys are
  `PLACEHOLDER_*` until swapped; calls fail fast with `ProviderNotConfigured` and a
  pointer to `.env.example`. **Adapters are written to documented API shapes but
  unexercised against real endpoints — smoke-test each when keys arrive.**

Generation fan-out is `asyncio.gather` over the four models at battle creation
(instant in sample mode). For live mode you'd move to async job + polling/SSE
(`generations.status` already models `pending/complete/failed`; see §6).

**Design sandboxing:** generated HTML is served from an API endpoint with a
restrictive CSP and rendered in `<iframe sandbox="allow-scripts">` — scripts run
(games are playable) but there's no same-origin access to the app, no network, no
top-level navigation.

## 5. Auth & sessions

Passwordless email codes (6-digit, 15-min TTL, single-use, stored in `auth_codes`).
Verification issues an HMAC-SHA256-signed, JWT-shaped token (stdlib only — the sandbox
has a broken native `cryptography`, and this app needs no asymmetric crypto), delivered
both as `httpOnly` cookie and bearer token; the SPA uses the bearer path
(localStorage) so the Vite dev origin works without cookie gymnastics.
Email delivery is the placeholder seam: dev mode returns the code in the response/UI.
The separate pilot uses Clerk with a backend session exchange; see
`docs/pilot/LOCAL-AND-HOSTED.md` → “Sign-in (Clerk)”.

## 6. Scale path (deliberately deferred, seams in place)

1. **Postgres**: set `ARENA_DATABASE_URL`; schema uses portable types; add
   Alembic when the schema starts moving.
2. **Async generation**: battle POST returns `generating`; workers fill generations;
   client polls or SSE. Status columns already exist.
3. **Ratings at scale**: debounced worker-queue recompute; incremental online Elo as
   the live approximation with periodic full BT refits (what the big arenas do).
4. **Vote integrity**: rate limits, per-(user,battle) constraints exist; add IP
   heuristics + anomaly checks in the pipeline (filter at read time — votes are never
   destroyed).
5. **CDN/object storage** for generated artifacts once categories include images.

## 7. Testing & verification

- `tests/test_ratings.py` — BT ordering recovery, count bookkeeping, smoothing
  boundedness, anchor/scale.
- `tests/test_api_flow.py` — full login→battle→4 votes→reveal→history flow; bracket
  order enforcement (422); auth gating (401); leaderboard reflects fresh votes;
  category/model catalog.
- Browser QA (Playwright + bundled Chromium): drove the real UI through sign-in,
  battle, all four votes, reveal, leaderboard, history; screenshots reviewed.
- Live-vote pipeline check: completed battle moved website snapshot 500→504 votes and
  overall 3000→3004 via the background recompute.
