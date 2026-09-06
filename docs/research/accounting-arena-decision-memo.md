# Decision memo: what to build, what to claim, what to test

**To:** David · **Date:** 2026-09-04 · **Companion:** `docs/research/accounting-arena-evaluation-methodology.md` (all evidence, citations, and simulations live there; section references below point into it).

Each recommendation below states what it's grounded in. Three grounding grades: **[evidence]** = verified primary sources or your own repo's code; **[simulation]** = my seeded simulations with stated assumptions (Appendix A); **[bet]** = a judgment call you should treat as testable, not settled.

---

## 1. What to build first

**A static arena that separates "is it permissible?" from "which would you sign?" — then a reconciliation sandbox whose agent runs experts review as recordings.** Concretely, in order (§14 has the week-by-week):

1. Scenario generator with accounting invariants + parameterized variants for journal entries, replacing the 3 hard-coded scenarios (§9). **[evidence:** every credible accounting benchmark — APEX-Accounting, Ramp's bench — is built on expert-validated synthetic worlds with registered ground truth; your simulation shows scenario count, not vote count, is the binding constraint on ranking accuracy**]**
2. A programmatic layer-1 gate (balance, amounts, period, account, policy) that runs before humans vote (§7.1). **[evidence:** your own repo stores the ground truth for this and never checks it — `scenarios.py` has expected postings; nothing grades against them**]**
3. Replace the 5-vote bracket with one graded judgment per scenario: rank the 4 outputs with ties allowed, mark each acceptable/unacceptable, add confidence + optional correction (§7.2). **[evidence:** K-Sort Arena on K-wise efficiency; the ties literature on the bias from forced binary choice; DesignPref on why corrections and per-rater data matter**]**
4. Gold items and estimated rater reliability instead of one trap per session and fixed credential multipliers (§8). **[simulation:** your current "Calibrated Reviewer" bar mislabels a 60%-accurate rater 34% of the time at 5 traps; **evidence:** Crowd-BT line shows estimated reliability beats fixed weighting**]**
5. Then the reconciliation sandbox with recorded-trajectory review (§6 Phase 2, §11.2). **[evidence:** reconciliation is the task family every vendor you'd sell to actually automates, and it cannot be validly judged as a static document; AgentRewardBench shows expert review of recorded episodes works**]**

## 2. What not to claim yet

- **Don't publish the current leaderboard.** It ranks ~500 seeded synthetic votes per category against quality tiers hard-coded in your own sample generator — the board "discovers" numbers you typed in. **[evidence:** `pipeline/seed.py`, `leaderboard.py:23-27` (synthetic votes pass the published-board filter), `professional.py:24-33`; §15 items 8–9]**
- **Don't claim to measure "accounting-agent capability."** The current session measures comparative preference among four static documents on one scenario. No state, no consistency, no process. **[evidence:** §2 Q1; APEX's pass^8 ≤ 2.6% across nine frontier models shows consistency — invisible to your UI — is where agents actually differ]**
- **Don't cite the marketing stats.** "94% panel accuracy," "1,240 calibration checks," "Top 18%" are hard-coded strings (`StatBand.tsx:3-7`). Remove or label as illustrative.
- **Don't claim rater calibration measurement.** One memorizable trap per session can't support it **[simulation + evidence:** §8]**.
- **Don't claim prompts drive evaluation.** The prompt box discards the prompt (`PromptComposer.tsx:49-52`). Until routing exists (§10), say "choose a certified scenario."

## 3. What the current five-comparison interface can validly measure

Kept as-is (with the honest labels), it validly measures three narrow things **[evidence: §2 Q1, §15]**:
1. **Blinded comparative preference** among four pre-generated artifacts on one scenario — a taste signal, confounded with presentation, from whoever your raters are.
2. **Rater attention** at the gross-error level (the trap), weakly.
3. **Engagement/UX** viability of a 5-minute expert session — genuinely valuable product learning, and the bones (blinding, server-side timing, sandboxed rendering, snapshot pipeline) are good and worth keeping.

It cannot, even in principle, measure correctness, agent consistency, process quality, or anything long-horizon. And its statistics need repair before even the preference claim is publishable: the bootstrap treats clustered votes as independent — nominal-95% intervals cover ~45–59% under realistic dependence **[simulation: §12]**.

## 4. When a spreadsheet/workbench is necessary

**Decision rule [evidence: §2 Q4, §5]:** you need an environment when the deliverable is a *state change*, when *investigation across sources* is the skill being tested, or when you need *repeated runs* (consistency). By task family:
- **Static is fine:** single journal entries, CoA mapping, flux commentary on fixed statements, policy/estimate memos, batch categorization. Launch here.
- **Environment required:** bank/payment reconciliation, month-end close orchestration, AP flows, schedule roll-forwards, tax/audit workflows. This is also where the vendors you want as customers (Rillet, Numeric, Ramp, Basis…) actually operate — so the workbench is commercially unavoidable, just not first.
- **The bridge:** run agents in the sandbox offline; have experts judge recordings + end-state diffs. ~80% of the data value at static-session cost **[bet — the cost ratio is my estimate; the mechanism is evidenced by AgentRewardBench]**.

## 5. Evidence required before publishing a leaderboard

A pre-registered validation study (§13: 24 paid raters, 3 families, ~4 hrs each, ~$10–15K) plus these gates, per family board:
1. **Reliability:** Krippendorff's α ≥ 0.4 among gate-passing comparisons, or disagreement demonstrably structured by rater role. (Professional designers sit at α = 0.25 — if CPAs are similar, a single preference board misleads. **[evidence:** DesignPref**]**)
2. **Defect detection measured:** what share of planted errors do raters catch, by subtlety.
3. **Clustered statistics live:** BT-with-ties, rater×scenario clustered intervals, per-family boards, FDR-controlled comparisons **[simulation + evidence: §12]**.
4. **Scale floor (interim):** ≥20 scenarios, ≥30 contributing raters, ≥1,500 counted judgments per family — derived from the power simulation, to be re-derived from measured variance components, not copied from other arenas **[simulation: §12.2]**.
5. **Versioned units:** every row is a config (model+scaffold+prompt+tools+budget), synthetic votes excluded, change log public **[evidence:** APEX/Ramp fix the harness; The Leaderboard Illusion shows what fuzzy units invite**]**.
6. **No fabricated numbers anywhere in the product surface.**

## 6. The five highest-priority experiments

1. **Expert agreement study (kills or confirms the core thesis).** Do calibrated professionals agree on gate-passing work (α ≥ 0.4)? And how much of preference do rubric criteria explain? → decides preference-led vs rubric-led product. (§13 V1–V2; H1)
2. **Detection study.** Show raters L1-failing outputs ungated; measure catch rates by subtlety. Quantifies why the gate must exist and calibrates gold-item difficulty. (§13 V3; H6)
3. **Static→environment prediction.** Same configs ranked by static preference and by sandbox outcomes (mean criteria, pass^4); correlate. Decides whether static boards may use capability language. (§13 V4; H2)
4. **Reliability vs credential.** Does estimated rater reliability predict held-out gold accuracy better than credential tier? Decides the weighting system (and the "measure the judges" marketing claim). (H3)
5. **Consistency gap.** Run 4–8 repeats per config on the reconciliation family; measure pass^k vs pass@1. If the gap is large (APEX suggests it is), consistency becomes your headline differentiator vs one-shot arenas. (H4)

**One candid strategic note [bet]:** the rubric-benchmark layer is being commoditized by the vendors themselves — Ramp/Mercor already ship APEX-class evaluation. Your defensible asset is the *calibrated human panel* and the preference/correction data it produces. That asset only exists if Experiment 1 comes back positive; run it before spending on anything else. If it comes back negative, the pivot is rubric-authoring + correction data with experts as auditors rather than voters — different product, same panel.
