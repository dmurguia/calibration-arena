# Verification — updated 6 September 2026

## Automated

- Backend: **34 passed**, one upstream Starlette/httpx deprecation warning. Includes existing tournament regression tests (legacy API explicitly enabled only by test config) and 15 pilot tests.
- Frontend: TypeScript + Vite production build passed.
- `git diff --check` passed.
- Tested boundaries: optional research permission, guest identity and invitation checks, optional profile enrichment preserving ownership, cross-participant access denial, blind fields withheld before judgment, conclusion required before challenge drafts, immutable submissions, preference validation, failed inference recorded without fixture substitution, exact Ask prompt preservation, paired provider payload contract, separate fixture provenance, computed ledger checks, daily participant limit, private founder export authorization and session-to-event joins.
- Live OpenRouter calls were not made. Provider payload was tested with a mock transport. Real model output quality, provider routing availability, latency/cost and production configuration require your key and two model IDs.

## Browser — current revision

- Copy: removed founding-cohort, pilot and beta framing from participant pages, profile and service errors; retained factual sample provenance and connection status.
- Desktop: Calibrated brand with Accounting as the separate workspace; persistent left navigation on Home, Notebook, sample review and How it works. Existing engraving/lens and typography retained.
- Composer: no consent checkbox or private-review notice. Custom prompt without live models stays in the composer with a clear connection message. No unrelated sample answers are returned.
- Explicit sample selection loads the actual brief and fixed-draft label. Editing it restores custom-prompt mode. Workpaper review shows its two samples; Treatment memo honestly indicates no fixed samples yet.
- Sample launched through the composer → independent conclusion → blind A/B → both ready / A preferred / Clarity / high confidence with synthetic explanation → saved reveal. Both supported postings passed case checks; authorship and explanations appeared after judgment. The completed review appeared in Notebook.
- Mobile at requested 390 × 844: readable homepage, work types wrap, sidebar opens from the header and closes on navigation. Home and How it works had equal document/client widths (375/375 CSS px; browser scrollbar occupies the remainder). Screenshots rendered the full phone-width content without the prior capture clipping. Actual-device testing remains separate.
- Prior implementation checks also covered founder token authorization/export, profile enrichment preserving session identity, and refreshing saved notebook/reveal records. Automated tests preserve those boundaries.
- Browser records are QA/local preview activity, not recruited participant evidence. One additional explicitly synthetic judgment was completed during this revision; previous user/local test activity was preserved.

## Local artifacts and operations

- Preview: `http://127.0.0.1:8021/`, server bound to loopback only.
- The running local preview uses the test-only founder token (configured only in the local process) for synthetic records. This is not a production secret; configure a fresh random `PILOT_ADMIN_TOKEN`, invitation code and empty durable database before hosting.
- Final private QA export: `/private/tmp/calibrated-pilot-qa-export-final-20260904.json`, mode 0600. This historical September 4 snapshot contained 2 QA profiles, 3 runs and 16 events, no bearer tokens/hashes, with valid run/event links. It is not a current database count. This is a verification artifact, not an evaluation report.
- Built application excludes the static public A/B demos; their source remains in `docs/research/demos`. Legacy pages/API are archived by default, so synthetic stats and code-return login do not appear in this pilot.
- At the initial September 4 verification, no deployment, push, PR or commit had been performed. Existing user work in the parent checkout was preserved.

## Remaining external validation

Two independent accountant reviews of the cases and rubrics; live OpenRouter smoke test; actual-device check; deployment to a durable HTTPS environment if approved; named founder contact/withdrawal procedure in invitations; and real return/usefulness data. None of those outcomes is claimed by this implementation.

## Local CLI integration — 6 September

41 backend tests now pass, including seven local adapter/boundary tests; final targeted rerun and production build passed. Real Codex and Claude Code responses were generated through the browser in 9.2 seconds and the judgment/reveal was saved. See [Local models](LOCAL-MODELS.md). OpenRouter itself remains untested.
