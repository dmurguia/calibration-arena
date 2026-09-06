# Calibration Arena — Product Architecture PRD

**Status:** v0 draft for founder review · 2026-09-04
**Ground rule for this document:** written from scratch. It does not assume the existing MVP's mechanics (five-comparison bracket, hidden trap match, credential-tier weights) or the earlier pilot mockup's rank-four screen. Where those mechanics survive, they survive on merit; where they don't, this PRD says what replaces them. Evidence citations live in the companion research docs (`accounting-arena-evaluation-methodology.md`, `-decision-memo.md`, `-pilot-spec.md`); this document is the product.

---

## 1. Thesis

**The product is a calibrated review layer for AI accounting work.** Verified accountants review blinded, AI-produced work items the way they review a junior's work: approve it, approve it with corrections, or reject it with a reason. Deterministic checks decide what is *permissible* before any human sees it; the panel decides what is *signable*. Out of that single gesture come the three things the market will pay for:

1. **Sign-off rates** — "what fraction of this agent's work would an independent CPA put their name on" — the trust metric no rubric-plus-LLM-judge benchmark (APEX, Ramp, Rillet's) can mint.
2. **A measured panel** — reviewers with known accuracy on gold items, not résumés.
3. **Corrections** — the fix, not just the flag: the scarcest training-grade data in the category.

## 2. Users and jobs

| User | Job to be done | What they get |
|---|---|---|
| **Reviewer** (CPA, controller, senior) | "Prove my professional eye is sharp; see what these tools can actually do; eventually get paid for judgment" | Calibration score with real error bars, portable badge, early intel, path to paid panel work |
| **Vendor** (Rillet, Numeric, Basis…) | "Make my agent credible to skeptical controllers; find out where it fails; show improvement release over release" | Private evaluation → certified sign-off rate → regression suite → corrections feed |
| **Lab / data buyer** | "Reward signal and demonstrations for accounting agents" | Licensed episodes with grades, preference data with rater-reliability metadata, corrections |
| **Buyer** (CFO/controller evaluating tools) | "Which of these is safe to let near my ledger?" | Public boards denominated in sign-off, per task family |

## 3. Core object model

The atomic unit is a **Review**, not a vote. Everything else is arranged around making reviews cheap to give and expensive to fake.

```
World (synthetic company snapshot, versioned)
 └── Scenario (task + ground truth + invariants + rubric, versioned, parameterized variants)
      └── WorkItem (one output by one Config on one scenario variant, run k of K)
           ├── CheckResult (programmatic: balance, amounts, period, policy → pass/fail + codes)
           └── Review (one reviewer × one item)
                 decision: approve | approve-with-note | reject
                 reason_codes[] (on reject): wrong-account · wrong-period · doesn't-balance ·
                   policy-violation · insufficient-support · overstates-certainty · other
                 correction? (edited entry / rewritten memo paragraph)
                 confidence (1 tap) · decision_ms (server-side)
Config (what's ranked): {model+version, scaffold+version, prompt hash, tools, budget, sampling}
Duel (secondary item type): two check-passing WorkItems, same scenario →
                 sign A | sign B | either | neither
TrajectoryItem (phase 2): recorded agent run + end-state diff → same Review gesture
Calibration item: a WorkItem whose CheckResult is a known fail (or a gold-standard pass),
                 served blind, at three subtlety tiers — scores the reviewer, never the model
```

**Why review-first instead of comparison-first.** (a) It is the real professional gesture — reviewers approve work items; nobody ranks four drafts of a journal entry at work. (b) The headline metric (sign-off rate) is measured *directly*, per item, instead of derived from tournament math. (c) A single-item screen is ~60–120 seconds — the casual loop survives. (d) Rejections carry reason codes and corrections natively; a comparison can't say *why*. (e) Comparative signal still exists two ways: statistically (many reviewers × many items per config on shared scenarios) and explicitly (Duels, served mainly where sign-off rates tie and a sharper instrument is needed). The earlier rank-four screen is retained **only as an A/B variant** (§10); the pilot decides, not this document.

## 4. Reviewer experience

**Surface 1 — The Queue.** Sign in → a short queue (3–6 items, ~8 minutes) shaped like a reviewer's inbox during close week. Mixed item types: mostly single reviews, occasionally a duel, occasionally (undisclosed, ~1 in 5 during a reviewer's first weeks) a calibration item. Every item: blinded author, scenario brief + policy chips, the work product, the decision bar. Session ends with a reveal: authors, check results, whether planted items were caught, and what the session contributed.

**Surface 2 — The Weekly Case.** One scenario per week, same for everyone; the week's reviews roll up into a published mini-report ("This week: the bonus accrual. 214 reviewers. Draft C signed by 61%; the most-cited rejection reason for Draft A was *overstates certainty*."). Purpose: cadence and habit (a Wordle-shaped ritual for a professional audience), maximum reviewer overlap on one item (best possible agreement statistics), and a naturally shareable artifact every single week instead of a leaderboard that moves invisibly. The Weekly Case is also where new scenario families debut for stress-testing before entering the rated pool.

**Reviewer payoff loop.** Calibration score = gold-item accuracy with honest binomial error bars and an explicit "not enough data yet" state until ~20 gold observations; consensus alignment shown separately; badge tiers earned from measured accuracy, never from email domain. Credentials (CPA verification) gate *entry* to the verified pool and appear as cohort labels — they never multiply anyone's weight.

## 5. Scoring and boards

Per **task family** (never one aggregate number):

| Board column | Definition | Source |
|---|---|---|
| **Signable %** | share of check-passing items approved (approve or approve-with-note) by verified reviewers, reliability-weighted | Reviews |
| **Check pass %** | share of items passing deterministic validity checks | CheckResults |
| **Duel rating** | Bradley–Terry-with-ties on duel outcomes, where the boards need finer separation | Duels |
| **Consistency** | pass^k across k runs per scenario variant (interactive families), criterion-score variance (static) | Repeated runs |
| **Cost / latency** | standardized $/item, wall-clock | Harness |

Uncertainty on every number (reviewer- and scenario-clustered bootstrap); models below the per-family exposure floor shown as *provisional*; a config is `{model, scaffold, prompt, tools, budget}` — vendor products rank as opaque versioned wholes on separately-badged rows. Failed-check items never dilute Signable % (they're reported in Check pass % and the failure taxonomy); reviews of failed-check items that reviewers *approved* feed calibration scoring and the failure dataset.

## 6. Panel and calibration system

- **Gold items** are ordinary-looking queue items with known answers, at three subtlety tiers (gross / material-but-plausible / defensible-vs-best-practice), generated as parameterized variants so no surface repeats. Density ~1 in 4–6 during a reviewer's first ~60 items, then ~1 in 10.
- **Reliability score** per reviewer from gold accuracy + agreement with high-reliability peers on shared items + repeat-item self-consistency + timing/pattern anomalies. It weights their reviews in Signable % and duel fits. Published as a distribution, never as a public individual ranking.
- **Appeals**: reviewers can see and contest gold scoring (graders can be wrong; contested golds go to panel adjudication and, if overturned, retro-correct scores).

## 7. Scenario supply chain

Scenarios are the binding constraint (more scenarios beats more reviews once a family has ~2k reviews). Pipeline: seeded generator builds worlds forward from ground-truth transactions (invariants hold by construction) → typed perturbation catalog plants defects against a register → every logical scenario compiles to ≥3 surface variants → an uninvolved expert solves it blind before release → versioned release batches with frozen checks, ~1/6 rotation per release, private hold-out slice never published. User-typed prompts route to a matching family (parameters seeded from their numbers, disclosed) or to a credited authoring queue — never silently ranked. The Weekly Case doubles as the proving ground for new families.

## 8. Vendor product line (the Rillet-shaped ladder)

1. **Benchmark teardown** (free, gives value first): their published benchmark vs the current published bar — task construction, repeated runs, statistics, judging, independence.
2. **Private pilot** (cheap/free for design partner #1): their agent as a Config on 20–30 scenarios in one family, k=4 runs. Deliverable: private report — Signable %, check pass %, pass^4, failure taxonomy with reviewer reason codes, 5–10 sample corrections. Private-first, publish only with consent.
3. **Certified evaluation** (paid): full family coverage, versioned, with the instrument's credentials attached (panel α, gold catch rates) — a number their sales team can cite because a third party with published methodology produced it.
4. **Regression suite** (recurring): frozen versioned slice re-run each agent release; movement report. This is the "make the agent better" product: score deltas by failure class, release over release.
5. **Corrections & episodes licensing** (data): consented, reliability-tagged reviews and corrections for training.

Empty-chair dynamics (boards showing invited-but-declined vendors) are deferred until at least two vendors are live — an empty chair with no occupied chairs beside it reads as weakness.

## 9. Data and consent (summary)

Every row carries `{config_id, scenario_id@version, world_id@version, generator_seed, check_version, reviewer_id, reliability_at_review, release_batch}`. Reviewer consent has two tiers: research/aggregate (default) and training-data licensing (separate opt-in, revocation forward-only, per-review flags in exports). No client data ever; all worlds synthetic. Vendor submissions carry per-row redistribution/training rights from the submission agreement.

## 10. MVP cut — the 10-friend test in this architecture

Build the queue as a static-content pilot (no generator, no live models needed on day one):

- **Content:** 6 hand-authored scenarios (4 JE, 2 accrual memo) × 4 model-produced drafts each; 2 scenarios carry a planted item (one plausible, one subtle); one duel; one recorded-trajectory item.
- **The A/B that decides the core screen** (both variants exist as clickable demos):
  - **Variant A — comparison screen:** all four drafts at once; per-draft "would you sign?"; rank with ties; confidence. One screen per scenario.
  - **Variant B — review queue:** one draft at a time; approve / approve-with-note / reject + reason codes + optional correction; a duel as its own item. Four short screens per scenario-equivalent.
  - Split the 10 friends 5/5, then swap for one scenario each. Measure: time per judgment, completion, planted-item catch rate, corrections volunteered, and — most important — which one they'd come back to weekly. Variant B is this PRD's default *hypothesis*; the pilot can overrule it.
- **Explicitly not in MVP:** leaderboard, weekly case automation, reliability model (log everything; compute later), routing classifier, live workbench.

## 11. Rolling into the existing repo

Keep from the current codebase: the FastAPI/SQLite skeleton and snapshot pipeline; server-side blinding and reveal gating; sandboxed iframe document rendering with CSP; server-side decision timing; guest-then-verify auth flow; the synthetic-scenario stance. Retire: the five-match bracket FSM and per-match `Vote` rows (replaced by `WorkItem`/`Review`/`Duel` tables); the separate hidden calibration match (calibration items are ordinary queue items with a server-side flag); fixed credential-tier weights; seeded synthetic votes in published boards; hard-coded marketing statistics. Migration is additive-tables-first: the new schema can land beside the old one, with the old UI decommissioned once the pilot picks a variant.

## 12. Product metrics

North star: **verified reviews per week** (quality-weighted: from reviewers above the reliability floor). Supporting: weekly active reviewers; median session length; return rate week-over-week; corrections per 100 reviews; gold catch rate by subtlety (instrument health); scenario-family coverage; vendor pipeline stage conversions.

## 13. Risks and open questions

- **Engagement risk:** reviewers may not return without pay; the Weekly Case + calibration credential is the retention bet. Kill signal: week-4 return rate < 20% among verified reviewers in the pilot cohort.
- **Agreement risk:** if calibrated professionals don't agree on signability of check-passing work, Signable % is noise — the validation study's α gate applies before any public board.
- **Pointwise leniency risk:** approve/reject thresholds drift by reviewer (some sign everything). Mitigated by reliability weighting, gold anchors, and duels for fine separation — but this is the main scientific cost of review-first vs comparison-first, and the A/B + study must confirm the anchoring works.
- **Scenario supply:** hand-authoring doesn't scale; the generator is the real engineering investment.
- Open: duel share of queue (10–25%?); whether approve-with-note counts fully toward Signable % or at a discount; correction licensing terms; when trajectory items enter the public queue vs stay vendor-private.

## 14. Companion documents

Methodology & evidence: `accounting-arena-evaluation-methodology.md`. Founder decisions: `accounting-arena-decision-memo.md`. Pilot protocol & build prompt: `accounting-arena-pilot-spec.md` (its Appendix B build prompt targets Variant A; a Variant B build prompt should be derived from §10 above plus the Variant B demo).
