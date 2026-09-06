# The first 20 accountants

Updated, 6 September 2026. Keep the Design Arena front door: an open prompt in the center of the screen, immediate engagement, and optional examples. Reuse the existing Calibrated engraving/lens, dial and typography. This is an experiment in repeat participation, not a model benchmark launch.

## What I compared

- GitHub main `d478e45`: strongest brand (paper, spruce, editorial documents, dial), but Ask discards the prompt; five-round forced-choice bracket; fictional model/season statistics and unverified credential language. Too many product promises before the first useful result.
- Research branch `56f54d6`, Demo A: four drafts, per-draft approval, ranking with ties. Good measurement ambition, excessive reading/ranking burden for an unpaid first visit. Static demo; stores nothing.
- Same branch, Demo B: a familiar review queue with approve/note/reject, occasional duel, correction and confidence. Better professional language. Four heterogeneous items make first-session value slow; demo calibration and signable percentages are not earned evidence.
- Earlier local Ask/Challenges implementation: useful separation and paired OpenRouter contract; still lacks a complete cohort identity/observation system. Do not substitute its older checkout for latest main.

## Mechanism choice

One open prompt or bounded case; two drafts; judge approval readiness of each; choose A/B/equivalent/neither/insufficient evidence; add a reason and confidence, with optional explanation or correction. Form an independent conclusion before seeing challenge drafts. Reveal immediately. The two-draft limit is a product bet about effort, not a claim that pairwise beats all other formats.

| Mechanism | Measures / contribution | Immediate value | Invalidity risk | First cohort |
|---|---|---|---|---|
| Two drafts + approval rubric | Mixed: policy/amount checks separate from preference; accountant identifies defects and preferable presentation | Compare approaches, inspect explanation, retain own answer | Style, position, ambiguous policy, fixture authorship | Yes; short journal-entry and period-end cases |
| Four-way ranking | Relative preference among four static artifacts | Broader model comparison | Burden, ties confusion, dependence among derived pairs | Defer |
| Single-output review + correction | Approval readiness and failure reasons; no pairwise estimate | Familiar workpaper review | Leniency varies by reviewer; no matched alternative | Borrow the language; test alone if pairs feel burdensome |
| Free question / Ask | Exploratory preference under same prompt/config settings | Useful responses to their own question | No common task population or known ground truth | Yes; separate exploratory pool, live provider required for real utility |
| Reconciliation sandbox / recorded agent run | Stateful correctness, investigation, controls and consistency | Review a real workflow | Incomplete traces, unjustified inference from final prose | Defer until static review earns repeat use |

Static pages are enough when all necessary facts and the final artifact fit on screen. Use an environment when the task requires investigating sources or changing the books. A chat box cannot validate a reconciliation agent.

## Features and experiment hypotheses

1. Prompt-first entrance, work-type choices and explicit samples, and a three-step review: accountants can engage immediately. Guests can start without a consent checkbox or background questionnaire. Operational storage is disclosed through Data use; private research reuse is a separate optional profile opt-in. Measure entry -> drafts -> judgment; for cases, measure the independent-conclusion step too. Collect optional professional context after the reveal, preserving the same participant and judgments.
2. Ask: useful questions lead to voluntary returns. Measure live own-question sessions separately from authored cases, including usefulness and later-day activity. Arbitrary prompts have no fixture fallback: without live credentials the prompt stays in the composer with a configuration message.
3. Optional post-reveal background profile + browser-bound saved work: role/experience/context help interpret disagreement and support return behavior. Self-reported, never credential verified. Measure completed cases, later-day visits and profile completion; background-missing guests must not be counted as qualified accountants. Browser identity is not proof of a unique human.
4. Separate readiness and preference: “least bad” must not become “correct.” Measure contradictions, neither/unsure rates, explanations and corrections.
5. Reveal and case-only share link: learning is the reward and a case is the invitation. Measure share intent and referred starts, not imaginary reach. No personal results or prompts go into share links.
6. Founder review/export: inspect every failed step and substantive contribution before scaling. Real participant events stay separate from authored fixture content and legacy seeds.

## Research interpretation

The repository methodology usefully separates objective correctness, professional criteria and preference, and warns about repeated reviewers/tasks, artificial seeds and fixed credential weights. Its future study sizes, thresholds and cost estimates are proposals, not validated launch requirements. We are intentionally cutting the proposed 25–30-minute, seven-screen pilot to one case with an optional next case.

Primary sources checked for this decision: [Chatbot Arena](https://proceedings.mlr.press/v235/chiang24b.html) establishes a human-preference mechanism, not accounting correctness. [Preference with ties](https://arxiv.org/abs/2410.05328) supports retaining ties; it does not settle this cohort's best UX. [OpenRouter ZDR](https://openrouter.ai/docs/guides/features/zdr) documents eligible routing, not an exemption from our own storage responsibilities. Other research in the repository remains supplied background; numerical claims are not re-certified here.

## Scope boundaries

No public leaderboard, CPA badge, peer percentile, paid assignment promises, enterprise console, agent execution, uploads, referral rewards, or social feed. No credential multipliers. No reuse of questions or corrections for training/publication without a later separate opt-in. Enterprise workflow evaluation remains the commercial hypothesis; this pilot sells accountants a useful practice session.

## What we could publish

First: a transparent field note on what 10–20 self-reported accounting professionals found difficult to review, with case-specific denominators, rubric disagreements and consent-cleared corrections. Authored fixtures can establish usability and defect-detection observations, never model performance. To publish actual model preference, collect and freeze real outputs with model/config/prompt/version provenance, independently validate the cases, and obtain appropriate publication consent.

Report A/B/tie/neither/insufficient separately, show per-output approval rates and stratify by case and reviewer context. Do not flatten repeated votes into independent observations or treat confidence as expertise. Use paired reviewer-by-case records; deduplicate first judgments for primary estimates, label repeats. Once enough cases/reviewers exist, estimate uncertainty resampling reviewers and cases, with ties modeled explicitly. At 20 people, show counts and uncertainty/limitations; do not manufacture a universal rank.

## Workspace and entry routing

Calibrated is the brand; Accounting is the current workspace. Persistent left navigation holds New comparison, Sample cases, Notebook and How it works. Journal entry, Treatment memo and Workpaper review select the requested artifact, not a canned answer. Samples are explicit instances within those types: selecting one loads its full brief, and editing it switches to live generation. See [Data pipeline](DATA-PIPELINE.md).

## User-facing positioning

User direction, 6 September: remove founding-cohort, pilot and beta framing throughout the participant experience, including profile, notebook, help and errors. Present Calibrated as the product. Keep factual source labels for authored samples and actual connection errors; do not imply model generation or verified credentials. Internal cohort operations, validation status and dataset labels remain in private documentation and records.
