# Work log — Linear-ready tickets

For the current accounting product sprint, use [Two-day sprint: ten accountants, open prompts and shared cases](pilot/TWO-DAY-SPRINT.md). Its CA2D-01 through CA2D-12 entries are proposed local tickets, not existing Linear issues. The work log below describes earlier product work.

Upload companion: `tickets.csv` (same content, Linear CSV-import columns).
Tickets DA-1…DA-12 are **Done** (shipped on this branch) and double as the work log;
DA-13…DA-20 are **Backlog** — the follow-ups and placeholder swaps.

---

## Done (shipped in this change)

### DA-1 · Scaffold Design Arena app skeleton (backend + frontend)
Self-contained repo: FastAPI + SQLAlchemy backend (SQLite default),
Vite/React/TS/Tailwind frontend matching the repo's existing stack, Makefile, README,
env template. Single-process prod shape: backend serves the built SPA.
*Labels: infra · Estimate: 2*

### DA-2 · Data model for arena battles and votes
ORM schema: `users`, `arena_models`, `battles`, `generations`, `matches`, `votes`,
`rating_snapshots`, `model_ratings`. Votes append-only with `synthetic` flag; matches
unique per (battle, round); anonymity enforced at serialization.
*Labels: backend, data · Estimate: 2*

### DA-3 · Passwordless auth (email codes) with placeholder email delivery
Request-code/verify endpoints, 15-min single-use codes, HMAC-signed stdlib session
tokens (cookie + bearer), `/me`, logout. Dev mode surfaces the code in the response/UI;
`EMAIL_PROVIDER_API_KEY` placeholder for Resend/SendGrid.
*Labels: backend, auth · Estimate: 2*

### DA-4 · Offline sample generation provider with model personas
14 design personas (palette/typography/flavor) × 6 category template families
(website, UI component, SVG dataviz, playable canvas game, SVG logo, ASCII art).
Deterministic per (model, prompt, category), prompt-keyword aware, self-contained HTML.
*Labels: backend, generation · Estimate: 3*

### DA-5 · Live vendor adapters behind placeholder keys
Anthropic / OpenAI / Google / OpenRouter adapters (httpx, shared category system
prompts, fence stripping) routed by `ARENA_GENERATION_MODE=live`; fail fast with
`ProviderNotConfigured` while keys are `PLACEHOLDER_*`.
*Labels: backend, generation · Estimate: 2*

### DA-6 · Battle orchestration + tournament state machine
Random 4-model selection, async generation fan-out, shuffled anonymous slots,
semi1/semi2 → final/third bracket with server-enforced vote order, vote rows written
per pairwise choice, reveal only on completion.
*Labels: backend, core-loop · Estimate: 3*

### DA-7 · Bradley–Terry ratings engine
MM fit over pairwise votes, geometric-mean normalization, smoothing for undefeated
models, Elo-style display scale (1200 anchor, 400/decade), bootstrap 95% CIs.
Unit-tested (ordering recovery, boundedness, anchor).
*Labels: backend, pipeline · Estimate: 2*

### DA-8 · Leaderboard snapshot pipeline (batch + live triggers)
Materialized snapshots per category + overall; CLI batch job
(`pipeline/compute_ratings.py`), background recompute on battle completion, API reads
latest snapshot only. Verified live: completed battle moved website board 500→504 votes.
*Labels: backend, pipeline · Estimate: 2*

### DA-9 · Seed pipeline: model roster + synthetic bootstrap votes
14-model roster (GPT-5.5, Claude Opus 4.8, Gemini 3 Pro, GLM 5.2, …) with latent
per-category strengths; ~3k BT-distributed synthetic votes (flagged) so the board is
credible on day one; `--reset` to regenerate.
*Labels: backend, pipeline · Estimate: 1*

### DA-10 · Frontend: prompt → vote → reveal core loop
Landing ("What are you creating today?", category chips, examples, champions teaser),
battle page with side-by-side sandboxed interactive previews, vote buttons + arrow-key
shortcuts, progress dots, podium reveal with model identities and latencies.
*Labels: frontend, core-loop · Estimate: 3*

### DA-11 · Frontend: leaderboard, login, history
Leaderboard with category tabs / score bars / CIs / win rates / methodology note;
email-code login flow with dev-code surface; "My battles" history with resume-voting
and winners. Auth context + API client.
*Labels: frontend · Estimate: 2*

### DA-12 · Test suite + browser QA
10 backend tests (ratings math, API flow, bracket order, auth gating, leaderboard
freshness); Playwright run through the full real-browser flow with screenshot review;
game-template polish fixes (title stopwords, don't lose lives before first input).
*Labels: quality · Estimate: 2*

### DA-21 · Design fidelity pass v2 (match designarena.ai closer)
Deep-dive after first-draft review: "models are generating" intro phase with staggered
reveals; icon category grid inside the prompt card ("Ask Design Arena to create…");
live stats row (`/api/stats`); model roster strip + footer; bracket visualization on
the reveal; leaderboard podium, movement deltas vs previous snapshot (`rank_delta`/
`is_new`), and methodology section; expand-to-fullscreen during voting; Space
Grotesk/Inter typography; brand-name extraction ("called X" drives design copy);
website hero variants (centered/split/editorial), line + donut chart variants, logo
mark variants. 12 backend tests green; browser QA re-run.
*Labels: frontend, backend, design · Estimate: 3*

---

## Backlog (create as open tickets)

### DA-13 · Swap in real provider keys and smoke-test live generation
Replace `PLACEHOLDER_*` keys in `.env`, set `ARENA_GENERATION_MODE=live`, verify
each adapter (Anthropic/OpenAI/Google/OpenRouter) against real endpoints, tune category
system prompts on real outputs.
*Labels: backend, generation · Priority: Urgent · Estimate: 2*

### DA-14 · Wire transactional email for login codes
Integrate Resend (or SendGrid) behind `EMAIL_PROVIDER_API_KEY`, set
`ARENA_DEV_LOGIN_CODE=0`, add resend-code UX and basic rate limiting.
*Labels: backend, auth · Priority: High · Estimate: 1*

### DA-15 · Async generation UX for live mode
Battle POST returns immediately in `generating`; worker/asyncio task fills
generations; frontend polls or SSE with per-slot skeletons and failure/retry states
(status columns already exist).
*Labels: backend, frontend · Priority: High · Estimate: 3*

### DA-16 · Production hardening pass
Set real `ARENA_SECRET_KEY`, move to Postgres (`ARENA_DATABASE_URL`),
add Alembic migrations, guard `/api/leaderboard/recompute` behind admin auth, restrict
CORS, schedule the batch ratings job (cron/worker).
*Labels: infra · Priority: High · Estimate: 2*

### DA-17 · Vote integrity & synthetic decay
Per-user rate limits, anomaly filters in the pipeline (read-time filtering, votes stay
append-only), scheduled down-weighting/aging of `synthetic=true` votes as human volume
grows.
*Labels: pipeline, trust · Priority: Medium · Estimate: 3*

### DA-18 · Tie votes and tiebreaker match
"Both good / both bad" options on each pairwise, optional 5th tiebreaker match
(designarena parity); extend vote schema with outcome type and teach the BT fit ties.
*Labels: core-loop · Priority: Medium · Estimate: 2*

### DA-19 · Share pages and winners gallery
Public read-only battle page (prompt, bracket, revealed designs), OG images, gallery of
recent champions by category.
*Labels: frontend, growth · Priority: Medium · Estimate: 3*

### DA-20 · New-model onboarding flow
Admin path to add a roster model: provisional rating, min-vote threshold before public
listing, active/inactive toggles surfaced in an admin UI instead of DB edits.
*Labels: backend, admin · Priority: Low · Estimate: 2*

---

## v2 pivot — Benchmark Stadium (shipped)

### BS-1 · Vertical + scenario taxonomy (Legal, Finance/ERP)
Replace design categories with two accountability-filtered verticals and four task
types (contract-redline, clause-risk, journal-entry, coa-mapping); synthetic scenario
library with structured facts (planted issues, expected postings, mapping keys).
*Labels: backend, product · Estimate: 2*

### BS-2 · Professional work-product generator with quality tiers
Offline generator drafting redlines (<del>/<ins>), risk memos, journal entries, CoA
mappings as paper-styled HTML docs; latent per-model quality changes substance
(issues caught, accounts chosen); deterministic per (model, scenario).
*Labels: backend, generation · Estimate: 3*

### BS-3 · Calibration traps (gold-standard checks)
Every session hides one comparison vs. a deliberately broken artifact (unbalanced
entry, swapped parties, absurd mappings); outcomes recorded in trap_results, scoring
the rater — never the models; positions and slots shuffled to prevent leakage.
*Labels: backend, trust · Estimate: 2*

### BS-4 · Credential tiers + weighted verified boards
Tier from email domain at signup (free-mail 0 / work domain 1; license 2 and named 3
as upgrade placeholders); votes carry tier weight + server-side decision_ms;
behavioral timing floor (ARENA_MIN_DECISION_MS); weighted Bradley–Terry fit;
published snapshots use counted, weight ≥ 1 votes only.
*Labels: backend, trust · Estimate: 3*

### BS-5 · Reviewer record (the reviewer's payoff)
/api/auth/reviewer + profile page: calibration score from traps, consensus agreement
vs. verified peers on identical pairs, percentile among raters, badge ladder
(Apprentice → Calibrated → Top Reviewer), tier explanation.
*Labels: backend, frontend, growth · Estimate: 2*

### BS-6 · Frontend pivot
Repositioned home ("Which AI is actually good at your job?"), vertical/task/scenario
picker, onboarding modal (vertical + role), 5-comparison judging UI with document
panels, reveal with calibration card, vertical-grouped leaderboard with trust
methodology, reviewer profile page.
*Labels: frontend · Estimate: 3*

### BS-7 · Tests + browser QA for the pivot
15 backend tests (flow incl. trap, tier detection, weighted snapshots, reviewer
stats, catalog); Playwright run through sign-up → onboarding → session → reveal →
boards → profile with screenshot review.
*Labels: quality · Estimate: 2*

### BS-16 · Company boards + release-drama engine (prototype scope — shipped 2026-09-01)
Roster extended beyond foundation models: `kind: foundation | product | declined`
with provenance (self-submitted / buyer-contributed + version). Vendor products
(fictional personas) seeded per vertical, drafted into battles and ranked on boards
only inside their vertical; invited-but-declined vendors rendered as dashed
empty-chair rows with a submission CTA (the FOMO mechanic). Release engine:
`model_releases` table, `POST /api/releases/simulate` re-runs a foundation model's
rows across its boards (synthetic re-run judgments → snapshot recompute → captured
rank movement), `GET /api/releases` feed; UI ships a Release radar panel with
movement chips + one-click simulate, and a home-page drama banner. 19 backend
tests passing. Production remainder split into BS-18.
*Labels: backend, pipeline, frontend, growth · Estimate: 4*

### BS-13 · Prompt-first front door (shipped 2026-09-01)
The front door is an open prompt box ("describe the work") with work-type chips and a
typed rotating placeholder; free text keyword-routes to the right board. Battles no
longer require auth: a guest gets ONE real blind comparison, then the auth gate
(work-email code, in place, mid-session) — signing in claims the running battle so
the bracket continues. Guest votes carry zero weight and never touch published boards.

### BS-19 · Front-end rebuild from Magic Patterns (shipped 2026-09-01)
Replaced the stopgap dark UI with the Magic Patterns design (corsac.ai system: cream
paper palette, Manrope, slim left sidebar, rounded-xl cards). All six screens wired to
the live API: prompt-first home (real scenarios, stats, drama banner), blind judging
with sandboxed document iframes in the paper chrome, reveal (real bracket, calibration
pass/fail card, board movement), leaderboards (chart/table toggle, release radar with
one-click simulate, PRODUCT provenance, empty chairs), sessions, reviewer record with
onboarding. Design source prompt: docs/magic-patterns-prompt.md.

## v2 backlog

### BS-8 · Describe-don't-disclose scenario synthesis
User describes their situation ("SaaS vendor paper, customer side, aggressive
liability caps"); the generator synthesizes a parallel synthetic document to battle
on. The privacy-preserving BYOD path.
*Labels: backend, product · Priority: High · Estimate: 3*

### BS-9 · License verification integrations
Bar number / CPA / SAP cert checks to upgrade raters to tier 2; admin flow for named
tier-3 reviewers.
*Labels: backend, trust · Priority: High · Estimate: 3*

### BS-10 · Rater-level reliability weighting
Bradley–Terry on raters: agreement with traps + verified-peer consensus becomes a
continuous vote weight; astroturf pattern detection (one-model favoritism across
categories).
*Labels: pipeline, trust · Priority: Medium · Estimate: 3*

### BS-11 · Per-firm private arena (the enterprise product)
Firm workspace: their scenarios, named reviewers, private board, benchmark
certificate readout (discrimination, expert agreement, coverage). The sales motion
this prototype rehearses.
*Labels: product, enterprise · Priority: High · Estimate: 5*

### BS-12 · Morning docket
One comparison a day by email — two-minute ritual for busy professionals; streaks
and calibration progress in the digest.
*Labels: growth · Priority: Medium · Estimate: 2*

### BS-14 · Medical coding & clinical documentation vertical
Vertical 3. Task types: E/M coding of a clinical note (ICD-10/CPT keyed — traps and
scoring half-deterministic), prior-auth appeal letters, denial-response letters.
Strongest certification culture (CPC/CCS), 2–5 min units, chronic churn → training
demand. Scenario library + generators + traps per the legal/finance pattern.
*Labels: backend, product, vertical · Priority: High · Estimate: 4*

### BS-15 · Tax vertical
Vertical 4. Task types: tax memo on a position (e.g., R&D credit, S-corp basis),
return-position review, client explanation letters. Seasonally viral; CPA overlap
with the finance vertical's reviewer base.
*Labels: backend, product, vertical · Priority: Medium · Estimate: 4*

### BS-18 · Company boards, production scope
The parts of BS-16 the prototype stubs: real vendor submission portal (opt-in
endpoint or bulk upload, terms, versioned resubmission), buyer-contributed outputs
under the buyer's own license, real model-release detection replacing the simulate
endpoint, product-row re-run cadence (vendor releases + quarterly), and the
quarterly "State of [vertical] AI" report generated from captured board movement.
*Labels: backend, pipeline, growth · Priority: High · Estimate: 4*

### BS-17 · Training & ramp-up mode (L&D SKU)
Reframe judging as deliberate practice for juniors in high-churn roles: curricula of
calibrated items with instant trap feedback, progress tracking against the calibration
ladder, manager dashboards. Monetizes via onboarding/L&D budgets (per-seat,
recurring); trainee votes stay low-weight until calibration earns weight — the tier
system already supports this.
*Labels: product, enterprise · Priority: High · Estimate: 4*
