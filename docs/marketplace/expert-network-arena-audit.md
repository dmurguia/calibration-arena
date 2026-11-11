# Corsac Expert Network → Calibration Arena: service audit and integration sequence

_Prepared 2026-10-29 for COR-433 by Claude (worktree `~/launch-work/claude-arena-audit`, branch `claude/expert-network-arena-audit`). Read-only audit: no deploys, migrations, auth changes, or edits to Codex-owned files._

## 1. Existing Railway service (Corsac Expert Network)

Inventory is from the repository, GitHub commit statuses and public endpoints. No Railway dashboard session was available, so values that only the dashboard can confirm are marked **unverified**.

| Item | Finding |
|---|---|
| Railway project | The project linked in COR-433 (one service, "Expert Network - corsac-expert-network", one production environment) |
| Deployed repo / branch | `dmurguia/corsac-expert-network`, branch `main` (Railway posts a GitHub commit status on every main commit) |
| Deployed commit | **Currently `fc982e8` (merge of PR #29) and it failed to boot.** Live domain returns 502 with `x-railway-fallback: true`. Last known-good deployment was the pre-#29 main (`4108e46` lineage per COR-430). |
| Public domain | `experts.corsac.ai` (custom domain; Railway status description "Success - experts.corsac.ai") |
| Runtime | Node, Express + tRPC, Vite client, `NODE_ENV=production` at start |
| Database engine | **MySQL** (Drizzle `dialect: "mysql"`, `mysql2` driver). Whether the DB is a Railway MySQL plugin or external is **unverified**. |
| Identity provider | Three paths coexist: Clerk (secret + publishable key), magic-link email login via Resend (`magic_links`, `outbound_emails`), and a legacy OAuth portal callback (`/api/oauth/callback`; `OWNER_OPEN_ID` marks the admin). Which of these real users actually signed in with is **unverified** (needs `users.loginMethod` counts). |
| Live data presence | **Unverified.** Migrations run through `0009_expert_journey`, and the pre-#29 code fell back to an in-memory store when `DATABASE_URL` was missing, so the production instance may never have had a persistent DB. Confirm by reading the Railway variables (is `DATABASE_URL` set and non-placeholder?) and `SELECT COUNT(*)` on `users`, `expert_profiles`, `submissions`, `vendor_postings`, `job_applications`. |
| Why #29 broke prod | `assertProductionEnv()` now requires `JWT_SECRET`, `DATABASE_URL`, `OWNER_OPEN_ID`, `CLERK_SECRET_KEY`, `VITE_CLERK_PUBLISHABLE_KEY`, `RESEND_API_KEY`, and the DB layer refuses the in-memory fallback. At least one is missing or a placeholder in the Railway prod environment. Revert is PR #30; alternatively set the variables and redeploy. |

### Data model (MySQL, Drizzle)

Accounts and orgs: `users` (role: user/admin/customer), `organizations` (customer orgs, status pending/active/suspended), `organization_members` (owner/manager/viewer).
Experts: `expert_profiles` (applicant/verified_expert/admin; verification status; rate tier standard/senior/principal; vertical medical/legal/financial/other), `credential_files` (license/credential/cv).
Work: `eval_suite_versions`, `evaluation_cases` (mode review/create; draft/available/archived), `submissions` (in_progress/submitted/reviewed/flagged; payout status), `payouts`, `admin_audit_log`.
Marketplace: `vendor_postings` (vendor-side job posts, rate unit hour/job/week/month), `posting_invites`, `job_applications` (submitted/matched/not_selected), `match_threads` + `match_messages` (kickoff chat).
Plumbing: `outbound_emails`, `magic_links`.

### Workflows (tRPC routers)

`auth`, `profile` (expert onboarding + credential upload), `cases`/`submissions` (timed evaluation harness with autosave, admin review, export), `admin` (approve/reject applicants, flag reviewers, audit log), `earnings`/`payouts` (balance, payout request, admin process/complete/fail), `customer` (org registration by domain, admin status), `vendor` (postings CRUD, bulk invites, inbox), `expertInvites`/`threads` (invite → accept → match thread), `expertSignup`/`application` (public application → status page by token → magic link), `jobs` (available jobs, apply), `evalSuites`.

## 2. Calibration Arena today (`dmurguia/calibration-arena` @ `572f9ae`)

| Item | Finding |
|---|---|
| Hosting | Railway (FastAPI backend, Postgres via `ARENA_DATABASE_URL`, SQLite locally) + Vercel frontend. Company site is a separate Vercel project `calibrated-site` built from `marketing/`. |
| Identity | `pilot_accounts` (email + password hash, optional unique `clerk_user_id`), `pilot_sessions` (server-side session tokens), Clerk verification in `pilot_clerk.py` (`POST /auth/clerk`). Clerk is live-capable although the README still calls it "deferred"; `/auth/signup`, `/auth/login`, `/auth/reset`, guests via `/guests`. |
| Data model | `pilot_participants`, `pilot_accounts`, `pilot_sessions`, `pilot_usage` (token budgets), `pilot_runs` (prompt → two drafts → preference/judgment/issues/improvements/feedback), `pilot_events`, `pilot_flags`, `pilot_reservations`. |
| What it lacks vs. the Expert Network | No expert application/credential vetting, no verified-expert role or rate tier, no customer organizations, no postings/invites/matching, no payouts/earnings, no admin applicant queue, no email plumbing (magic links / outbound email table). |
| What it has that the Expert Network lacks | A working individual participation loop with judgments and a leaderboard, Clerk already wired on both ends, Postgres, PostHog. |

## 3. Recommended mapping: what moves, what stays, what dies

Principle from COR-433: one identity system (Arena's `pilot_accounts` + Clerk), one individual product (Arena), the company site as the only public entry point. The Expert Network stays as **separate legacy infrastructure** until its selected capabilities are re-implemented in Arena; it is not linked from calibrated.co.

| Expert Network capability | Decision | Arena target |
|---|---|---|
| Public expert application → status page → magic link | **Replace** with the calibrated.co `/experts/` interest form (Codex) feeding the operator intake, then an Arena invite | `pilot_accounts` + Clerk invite; no magic-link table |
| Expert profile, vertical, rate tier, verification status | **Migrate (schema only)** | new `pilot_expert_profiles` keyed by `participant_id` |
| Credential file upload + admin approve/reject | **Migrate later**, after a first paid pilot proves the need | admin-only route group in Arena |
| Timed evaluation cases + submissions + review | **Do not migrate.** Arena `pilot_runs` is the judgment unit; expert tasks for the $12k pilot are authored as Arena cases | `pilot_runs` / cases |
| Vendor postings, invites, match threads, job applications | **Drop.** Buyer demand enters via `/get-data/` intake and is handled by the operator; no self-serve vendor side at launch | none |
| Customer organizations | **Drop for launch**; buyer orgs live in the intake records | none |
| Earnings / payouts | **Migrate as a ledger only** once experts are paid per accepted task | `pilot_payouts` (admin-written) |
| Admin audit log | **Migrate pattern** | `pilot_events` already covers it |
| Users with real sign-ins (if any) | **Migrate by email** into `pilot_accounts` with a reset link; preserve created_at | `pilot_accounts` |

## 4. Integration sequence (no production changes until step 5 is approved)

1. **Inventory live data** (owner, 15 min in Railway): confirm `DATABASE_URL` is real, run the five COUNT queries above, note `users.loginMethod` distribution. Decide: revert PR #29 now (PR #30) or set the six variables. Record in COR-433.
2. **Freeze the Expert Network**: no new public links to experts.corsac.ai; keep it up only for existing experts until migration. Remove the `experts.corsac.ai` footer link from the lazarus site and calibrated.co copy (see §6 brand conflict).
3. **Land Codex's company-site work** (`/get-data/`, `/data-partners/`, `/experts/`, `/api/intake`) behind `INTAKE_WEBHOOK_URL`; verify a durable receiver and an operator alert. Review notes in §5.
4. **Arena: expert profile + invite** (this branch, next): add `pilot_expert_profiles` (vertical, specialty, rate tier, verification status, profile_url), an admin endpoint to mark a participant `verified_expert`, and an invite path from an intake record to an Arena sign-up link. Keep Clerk as the only cross-device identity.
5. **Account migration script** (dry-run first): email-keyed import of Expert Network `users` + `expert_profiles` into Arena with password reset links; skip test/dev-login users. Owner approves the dry-run report before the real run.
6. **Decommission**: redirect experts.corsac.ai → calibrated.co/experts/ once migrated experts have signed into Arena; archive the Railway service after a 30-day read-only window and a DB export to object storage.

## 5. Review of Codex's `codex/calibrated-marketplace-integration` (uncommitted working tree as of 02:22 PT)

Scope read: `marketing/src/marketplace.mjs`, `marketing/public/marketplace.{mjs,css}`, `marketing/api/intake.js`, `marketing/scripts/{build,serve,intake.test,site.test}.mjs`, `components.mjs`, `package.json`.

**Solid.** The intake handler only reports success after the receiver confirms `{ok:true, stored:true, submission_id}`; retries reuse the same UUID; bodies are byte-bounded; origin and `sec-fetch-site` are checked; honeypot and consent enforced; seller rights gated; no logging of payloads. Pages honour the no-fabrication rule (pilot shown as "proposed scope", no reserved dataset). The `export default { fetch }` shape is supported by Vercel's Node runtime ([docs](https://vercel.com/docs/functions/functions-api-reference.md)).

Findings, highest first:

1. **Rate limiter is global, not per-client** (`intake.js`, `clientKey = 'instance'`). One instance allows 60 inquiries/min across all visitors and then returns 429 to everyone; a single bot could lock out real buyers for a minute at a time. Codex documents this as deliberate. Recommend keying on `request.headers.get('x-vercel-forwarded-for')` (set by Vercel's edge, not caller-controlled) with the global key as a fallback, or Vercel's firewall rate limiting.
2. **Nothing is committed.** All of this is working-tree only; the Linear agreement asks for commit SHAs in handoffs. Please commit before the next sync so review can pin to a SHA.
3. **CSP `form-action 'none'`** in `vercel.json` means the `<form method="post" action="/api/intake">` fallback is blocked if JS fails after load; `<noscript>` covers no-JS only. Acceptable given the JS-only design, but the `action` attribute is then misleading. Either drop `action`/`method` or allow `form-action 'self'`.
4. **Privacy page not updated** (`pages.mjs` unchanged). The forms now collect name, email, organization and free text and forward them to an operator webhook; the privacy notice should name that processing and retention.
5. **`intakeEnabled` is a build-time flag** from `INTAKE_WEBHOOK_URL`, while the function reads it at request time. If the variable is set only for the function and not the build, the form renders in "prepare and download" mode. Make sure the same variable is present in both Vercel build and runtime env, and add a site test that asserts the enabled form renders when the variable is set.
6. Minor: the seller `rights` select includes `unsure`, which the client blocks before sending and the server rejects; fine, but the server error message says "rights confirmation required" without listing the field, while other 422s do.

No correctness bugs found in the payload normalisation or receipt matching.

## 6. Brand conflict that needs an owner decision today

Two agent tracks diverged on the brand:

- **Linear direction (COR-433, owner clarification 28 Oct):** calibrated.co is the company entry point; Calibration Arena for individuals; the Corsac Expert Network is legacy and not part of the ecosystem. COR-384/COR-378 point to `data.calibrated.co`.
- **Shipped this morning (29 Oct):** `dmurguia/lazarus` PR #7 rebranded the data brokerage to **Corsac Data Partnerships** at `data.corsac.ai`, and Expert Network PR #29 added footer links to `corsac.ai` / `data.corsac.ai`. The lazarus site is live on Vercel under the Corsac name (DNS for data.corsac.ai not yet attached).

Recommendation: treat the Linear/Calibrated direction as binding, since it is the newer owner statement, and fold the lazarus `web/` content into calibrated.co `/data-partners/` (Codex already built that page) rather than attaching data.corsac.ai. The Corsac name stays on corsac.ai (evals) only. If the owner instead wants Corsac as the umbrella, COR-433's description and Codex's copy need to change before anything else ships.
