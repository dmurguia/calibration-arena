# Calibrated

The current product is a prompt-first accounting workspace: choose a work type, compare two anonymous drafts, make your judgment, and keep the result in Notebook.

See [the product decision](docs/pilot/DECISIONS.md), [the cohort and credential runbook](docs/pilot/RUNBOOK.md), and [verification](docs/pilot/QA.md).

Start with `backend/.env.pilot.example`. Explicit authored samples work without credentials. Live prompting supports server-side OpenRouter configuration, or a temporary loopback-only [Codex and Claude Code bridge](docs/pilot/LOCAL-MODELS.md) using existing CLI sign-ins. Browser-bound identity is implemented; Clerk is an explicitly deferred cross-device upgrade.

Legacy tournament endpoints, synthetic boards and code-return login are disabled by default (`ARENA_LEGACY_API=0`). The original prototype notes below are historical, not current product claims.

---

# Benchmark Stadium

**The arena for work you sign your name to.** Blind head-to-heads of professional work
product — contract redlines, clause risk reviews, journal entries, chart-of-accounts
mappings — judged by verified professionals, feeding a credential-weighted
Bradley–Terry leaderboard.

Two launch verticals: **Legal** and **Finance / ERP**. Every document is synthetic
("we bring the doc"), so nothing confidential is ever uploaded to play.

Runs fully offline out of the box — no API keys needed (see *Generation modes* below).

## The loop

1. Pick a vertical → task type → scenario (a synthetic matter with planted issues).
2. Five models draft the work product, anonymized and shuffled.
3. You judge **five comparisons**: two opening rounds, a hidden **calibration check**
   (one output is objectively broken — it scores *you*, not the models), then the top
   and consolation matches.
4. Reveal: bracket, model identities, and your calibration result.
5. Your verified, credential-weighted votes recompute the board immediately.

## Company boards & release drama

Boards rank **foundation models and vendor products side by side**. Products (all
fictional in the prototype) carry a PRODUCT badge with provenance — self-submitted or
buyer-contributed, plus the submitted version — and compete only inside their
vertical. Invited vendors who declined appear as dashed **empty-chair rows** under
each board ("Invited · declined to participate") with a standing submission CTA.

When a foundation model ships, its rows re-run on every board it competes on and the
rank movement lands in the **Release radar** (`GET /api/releases`). In the prototype,
`POST /api/releases/simulate` (or the "Simulate next release" button on the
leaderboard) stands in for real release detection.

## Trust layer (baked in)

- **Credential tiers**: free-mail signup = tier 0 (directional only) · work-domain
  email = tier 1 (full weight) · verified license = tier 2 (1.5×, placeholder) ·
  named reviewer = tier 3 (2×). Published boards use tier ≥ 1 votes only.
- **Gold-standard traps**: every session hides one comparison against a deliberately
  broken work product (unbalanced entry, swapped parties). Results land in
  `trap_results` and drive each rater's calibration score, percentile, and badge.
- **Behavioral floor**: votes decided faster than `ARENA_MIN_DECISION_MS`
  (default 4s) are recorded but never counted.
- **Weighted Bradley–Terry**: the ratings fit consumes (winner, loser, weight).

## Quickstart

```bash
# from the repo root

# 1. Backend deps (Python 3.10+)
pip install -r backend/requirements.txt

# 2. Seed: 14-model roster + synthetic bootstrap votes + first boards
cd backend && python -m pipeline.seed

# 3. Run the API (http://localhost:8000)
uvicorn app.main:app --reload --port 8000

# 4. Frontend dev server (http://localhost:5173, proxies /api to :8000)
cd ../frontend && npm install && npm run dev
```

Single-process deploy: `npm run build` in `frontend/`, then the FastAPI app serves the
built SPA itself at `:8000`.

Sign-in uses email one-time codes shown in the UI (email delivery is a placeholder).
Use a **work-domain email** (anything not on the free-mail list) to land at tier 1 and
have your votes count on the boards.

## Generation modes

- `ARENA_GENERATION_MODE=sample` (default): the offline professional provider
  drafts real, gradeable work products per model quality tier — deterministic per
  (model, scenario), no credentials required.
- `ARENA_GENERATION_MODE=live`: each model routes to its vendor adapter
  (Anthropic / OpenAI / Google / OpenRouter). Swap the `PLACEHOLDER_*` keys in
  `backend/.env.example` first. The scenario brief becomes the live prompt.

## Pipeline

```bash
python -m pipeline.compute_ratings              # recompute all boards + overall
python -m pipeline.compute_ratings --category journal-entry
python -m pipeline.seed --reset                 # rebuild roster + synthetic votes
```

Snapshots also recompute automatically in the background whenever a session completes.

## Tests

```bash
cd backend && python -m pytest tests/
```

## Docs

- `docs/PRD.md` — product requirements (v1 recreation + v2 pivot)
- `docs/ARCHITECTURE.md` — engineering write-up
- `docs/TICKETS.md` + `docs/tickets.csv` — Linear-ready work log
