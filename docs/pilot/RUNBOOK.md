# Run the first cohort

## What is ready locally

A prompt-first React/FastAPI participant loop: work type + open prompt (or explicit sample case) → blinded drafts → per-draft approval + preference/reasons/confidence → saved reveal → optional reviewer background/usefulness → another prompt or case. Practice cases add an independent-conclusion step before drafts. Five authored practice cases. Randomized left/right placement. Immutable judgments and conclusions. Private founder inspection and complete raw JSON export. No seeded data feeds these tables.

The local working branch is `codex/accountant-pilot`, based on research branch `56f54d6` (which contains current main `d478e45`). Worktree: `/Users/david/Code/benchmark-stadium/pilot-cohort`. Original checkout and earlier uncommitted work were preserved. Publication and deployment are separate from this implementation.

## Temporary signed-in local models

Codex and Claude Code can now power the open prompt on this computer without an OpenRouter key. See [Local models](LOCAL-MODELS.md) for the verified launcher, limits, provenance and switch back to OpenRouter. This mode is loopback-only and is not the hosted cohort configuration.

## Start locally

From the pilot worktree:

```bash
cd frontend
npm ci
npm run build
cd ..
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.pilot.example backend/.env
.venv/bin/python -m uvicorn app.main:app --app-dir backend --env-file backend/.env --host 127.0.0.1 --port 8021
```

Open `http://127.0.0.1:8021`. This serves frontend and API on one origin. The prompt is the home screen, with the original engraving/lens, work-type choices above it, and explicit samples beneath. The sidebar holds the current Accounting workspace, sample library and notebook. Check occupied ports before changing them; do not stop unrelated projects. The preview launched during this implementation uses the parent checkout's existing Python venv, with a separate pilot SQLite database.

## Credentials and launch gates

1. **OpenRouter**: place your API key and two distinct exact model IDs in `backend/.env`. Also set `PILOT_INVITE_CODE`. Restart the backend. `/api/pilot/config` must report `ask_mode: live`. Ask makes two independent requests with identical system/user messages, temperature/top-p/token limits, and ZDR/no-collection routing. Both must succeed; provider failure is recorded and never silently replaced with samples. Live provider execution still needs your credentials and a real smoke test. Set an account spend limit. No uploads, retrieval or tools are provided.
2. **Pilot access**: set a private invitation code for the 10–20 people. Send it directly; do not put it into a URL. It limits casual access but is not an identity verification system. There is a 20-run/day/profile ceiling; browser profiles and a shared code are not a hardened public inference gateway.
3. **Founder review**: generate a random secret (for example `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`) and set `PILOT_ADMIN_TOKEN`. Open `/founder`, enter it there, inspect profiles, stage events, approvals, explanations/corrections, and usefulness; export raw JSON. The token is never stored in browser storage. Use HTTPS when hosted. Keep exports private and out of Git.
4. **Login**: Clerk is not required for this concierge test. The implemented identity is a high-entropy browser bearer token stored locally; server stores only its hash. Work persists across revisits in the same browser. Names, role and framework are self-reported, not verified. For cross-device recovery or a wider launch, add Clerk and server-side JWT verification plus an explicit guest-record claim flow. The example env file marks the future Clerk keys as inactive, rather than pretending that supplying them enables login.
5. **Hosting**: use one HTTPS origin and a durable database volume. Do not reuse a preview/test database for the real cohort. Set `PILOT_DATASET=cohort-2026-09` for new invitees; profiles otherwise default to `preview`, visible in founder review. The current localhost preview is not publicly shareable. If splitting API/frontend, set the existing `VITE_API_URL` plus exact `ARENA_CORS_ORIGINS`. Verify CORS and authentication from the actual hosted domain. Leave `ARENA_LEGACY_API=0`; old code-return login, seeded boards and simulated releases must stay disabled.
6. **Content**: ask two accountants to independently solve and critique all five cases and their rubrics. Reconcile ambiguity, version any changes, and record validation sign-off before framing the cases as validated. Current labels correctly say independent validation is pending. They are authored fixtures, not vendor outputs. Public cases/landing-page examples are exposed practice material, not hidden calibration tests.
7. **Private data operations**: record a named founder contact in your invitation. Honor withdrawal/deletion through a controlled, backed-up database operation. The pilot has no self-service deletion or account recovery; do not advertise either. Never reuse pilot data for model training or publish identifiable examples without a separate consent process.

## Recruit in two waves

First, five warm contacts across bookkeeping, public practice and industry/controllership. Watch the first case silently. Then invite the remaining 10–15 after fixing the biggest comprehension problem. State the requested time as “one case, about three minutes, plus optional feedback,” not a 30-minute evaluation assignment. The duration is a product target to validate, not a measured completion time.

Keep an invitation roster outside the app: participant alias, source, sent date, first-session date, whether the session was observed, any reminder date, and interview permission. Use links such as `/case/utilities-accrual?source=founder-wave1` and ask them to use the same browser. Source is an acquisition label, not a credential. Do not encode email or personal identifiers in URLs.

Suggested invitation (draft only; not sent):

> I’m building a small practice room for accountants reviewing AI work. Would you try one three-minute accounting case and tell me whether the reveal was worth your time? You’ll make your own call, review two anonymous practice drafts, and see the explanation. This early version uses authored examples; it doesn’t grade your credentials. No client information needed. If useful, there are four more cases and a place to ask your own hypothetical questions.

For a live Ask cohort, update the sentence about examples to distinguish authored practice cases from live Ask responses. Set honest expectations: there is no job placement, CPE credit, CPA certification or paid-work promise.

## Observe without steering

Before clicking: “What do you expect this to do?” After the first reveal: “What did you learn? What would you use this for next week? Which part felt like work for us instead of value for you?” Ask them to point to one useful detail. Note unsolicited confusion and requests for missing documents. Do not coach them toward the planted error or explain the voting buttons before they try.

Review every judgment each day. Flag unclear briefs, judgments with no evidence, corrections to the answer key, repeated reviewers/cases, very short or long review times, and failed inference. Do not automatically exclude slow or fast people; time includes reading, scrolling and interruptions. Do not treat high confidence as correctness.

## Read the data correctly

`pilot_participants`: guest identity first, optional post-reveal profile/source, private follow-up permission, optional research permission and its timestamp/version (null if not granted); publication/training consent always false. `pilot_runs`: owner, task version, frozen brief and drafts, displayed order, conclusion, state, provenance, response configuration, submission time, approval/preference/confidence/reasons/correction and usefulness. `pilot_events`: enrolled, profile_completed, visit, session_started, conclusion_saved, drafts_shown, judgment_completed, generation_failed, left_session, usefulness_submitted, share_intent. Event data contains no duplicate raw question text.

Server timestamps are authoritative. A visit is deduplicated within 30 minutes. Separate UTC activity days from 14-day return windows. A different day is not automatically an unprompted return—join against the invitation/reminder log. Separate second-day activity from same-day multiple sessions. Browser resets create another profile; reconcile duplicates manually with participant consent. Compare completed-case count with unique-case count. Refreshing a reveal never creates another judgment.

Report guest-only reviewers separately from people who supplied accounting context. Do not count anonymous browser participation as qualified accountant participation. An incomplete run is **not proven abandonment**. Use its last server step plus elapsed time and any client navigation event, then ask the participant. Tab closes/offline crashes may lose the best-effort left_session event. There is no identity before a guest starts using the service. Non-opened invites are captured in the invitation roster, not guessed from the application. Starting a session does not grant research permission. Filter for explicit research_consent before research reuse; operational records remain available for notebook and service support.

Export locally without an admin HTTP token:

```bash
cd backend
PYTHONPATH=. python -m pipeline.export_pilot --output /private/tmp/pilot-private-export.json
```

This uses the database selected by the process environment; the CLI does not automatically read `.env`. Use the same `ARENA_DATABASE_URL` as the running service. It refuses overwrites and writes mode 0600. Contains private questions/contact details; no training/publication rights are granted.

## Evidence gates after 14 days

Predeclare these as directional experiment targets, not statistically powered thresholds:

- **Continue the community-first bet** if at least 10 of 20 invited complete five distinct meaningful evaluations, five return within 14 days without payment or prompting, and at least 25 explanations/corrections contain a concrete useful detail (founder/adjudicator coded). Require interviews to identify learning or review value beyond free inference.
- **Change the mechanism** if more than roughly one-third of observed users need an explanation of the judgment controls, fewer than half complete a first case, paired reading feels burdensome, or “insufficient evidence” repeatedly exposes missing task context. Test single-output approve/revise + correction next, holding cases constant. These cutoffs are product decision rules, not research findings.
- **Change the task boundary** if accountants consistently ask for source documents or ledger state. Add one evidence packet or recorded reconciliation run before a general sandbox. Preserve the same review/correction record.
- **Reject or substantially revise the unpaid community thesis** if, after one targeted usability/content iteration, no one returns unprompted, explanations remain thin, and interviews say the work has value only as a paid assignment. Twenty people cannot prove universal non-demand; it can justify stopping this version.
- **Do not infer buyer demand** from participation. An enterprise conversation about a private release evaluation is a separate experiment, grounded in an actual reviewed artifact.

## Publication path

Begin with a field note: cohort composition and recruitment, exact cases and policies, known limitations, counts of approval/preference/tie/neither/unsure, disagreements and consent-cleared corrections. Publish no model ranking from authored drafts. For model evidence, run and freeze genuine models on independently validated cases, keep exact model/config/date/hash provenance, and collect judgments on that shared pool. Keep open Ask separate. Have an accountant adjudicate content and a methods reviewer examine dependence and uncertainty before any capability claim.

## Prompt and sample routing

See [Data pipeline](DATA-PIPELINE.md). Without configured live models, only explicit sample cases produce drafts. The former generic Ask walkthrough has been removed; old walkthrough records remain labeled in existing notebooks. No key or sample match is inferred from the question. The composer has no consent checkbox; Data use links to the storage/provider explanation and the optional profile records private research permission separately.
