# Evaluation Methodology for an Accounting & Finance AI Arena

**Author:** research pass commissioned by David Murguia · **Date:** 2026-09-04
**Repository audited:** `dmurguia/calibration-arena` @ `d478e45` (default branch at time of audit; all file/line references below are to that tree)
**Status of this document:** research recommendation. It changes no application code.

**Epistemic labeling convention used throughout:**
- **[S]** sourced fact — verified against a fetched primary source (paper, official methodology page, or this repository's code); citation attached.
- **[I]** inference — my analysis or simulation, with reasoning or code shown.
- **[R]** recommendation — a design choice I am proposing, with its grounding stated.

Verification caveats: most external sources were fetched directly (arXiv abs/HTML pages, ACL Anthology, PMLR PDFs, vendor pages). Where a source could only be partially accessed (e.g., OpenReview blocked the WebArena Verified PDF; the Ramp Labs page is a client-rendered SPA read via its JS bundle), that is stated inline and in the bibliography (§17). Nothing below is cited from memory alone; anything that could not be verified is labeled as such.

---

## Table of contents

1. [Executive recommendation](#1-executive-recommendation)
2. [Direct answers to the seven questions](#2-direct-answers-to-the-seven-questions)
3. [Competitive-methodology matrix](#3-competitive-methodology-matrix)
4. [Annotated literature review](#4-annotated-literature-review)
5. [Accounting task taxonomy](#5-accounting-task-taxonomy)
6. [Three architectures compared](#6-three-architectures-compared)
7. [Recommended measurement model](#7-recommended-measurement-model)
8. [Rater and calibration methodology](#8-rater-and-calibration-methodology)
9. [Synthetic-world and scenario-generation protocol](#9-synthetic-world-and-scenario-generation-protocol)
10. [Prompt-to-benchmark routing design](#10-prompt-to-benchmark-routing-design)
11. [Three worked task examples](#11-three-worked-task-examples)
12. [Statistical analysis plan](#12-statistical-analysis-plan)
13. [Minimum viable validation study and evaluator burden](#13-minimum-viable-validation-study-and-evaluator-burden)
14. [Ninety-day research and product roadmap](#14-ninety-day-research-and-product-roadmap)
15. [Prototype gap analysis with exact repository references](#15-prototype-gap-analysis)
16. [Risks, unresolved questions, and falsifiable hypotheses](#16-risks-unresolved-questions-and-falsifiable-hypotheses)
17. [Bibliography](#17-bibliography)
18. [Appendix A: simulation code](#appendix-a-simulation-code)

---

## 1. Executive recommendation

**Build a layered evaluation system in which deterministic accounting checks decide what is *permissible* and calibrated experts decide what is *preferable* — and stage it in three phases, entering through an upgraded static arena rather than a full workbench.** This is the pattern the strongest recent accounting-agent evaluations already converge on: APEX-Accounting and the Ramp Accounting benchmark run agents inside synthetic company worlds and grade against expert-authored criterion rubrics with frozen judges and repeated runs [S: arXiv:2607.27189; labs.ramp.com/ramp-accounting-bench], while preference arenas (Chatbot Arena, Design Arena, K-Sort) contribute the blinded-comparison mechanics and the ranking statistics [S: PMLR 235:8359; designarena.ai/about; arXiv:2408.14468]. Neither family alone answers your product question. Rubric benchmarks have no live human-judgment layer and therefore produce no preference or calibration data; preference arenas without correctness gates measure persuasiveness confounded with quality — a real risk in accounting, where the prototype's own "broken" artifact is styled to look confident (`backend/app/services/providers/professional.py:283`, a deliberately unbalanced entry captioned "All entries verified and in balance").

**The five-part recommendation:**

1. **Adopt the four-layer quality model** (hard validity constraints → criterion-level professional quality → comparative preference among acceptable outputs → operational measures). Preference votes involving a layer-1-failing output are excluded from the "professional quality" rating but retained as failure/detection data (they measure the *rater* and generate training-negative material). Grounding: §7; the emerging hybrid pattern in APEX/Ramp/ToolSandbox/WebArena Verified [S]; and the confound evidence from LMArena's style-control work showing verbosity/formatting materially shift preference-based rankings [S: lmsys.org/blog/2024-08-28-style-control].

2. **Replace the forced-binary five-comparison bracket with per-task graded judgment:** K-wise ranking (or pairwise with `tie / both acceptable / both unacceptable / not enough information`), plus 2–4 criterion ratings, a confidence report, and an optional correction. One evaluator's five bracket votes on one scenario are heavily dependent observations, not five independent samples (§2 Q1, §12); K-Sort Arena shows one K-wise ranking carries roughly the information of K(K−1)/2 pairwise votes at similar evaluator cost [S: arXiv:2408.14468], and dropping ties provably biases inferred preference strength exactly where models are close [S: arXiv:2410.05328].

3. **Rank versioned configurations, not bare model names** — {model+version, scaffold+version, prompt hash, toolset, budget policy, sampling params} — with foundation models run on one fixed reference scaffold (as Ramp does with its ReAct harness [S]) and vendor products ranked as opaque versioned wholes on separate, clearly labeled boards (§2 Q7).

4. **Fix the statistics before publishing any leaderboard.** The prototype fits weighted Bradley–Terry and bootstraps individual votes as if independent (`backend/app/services/ratings.py:114-120`). My simulations (§12, Appendix A) show that under realistic evaluator- and scenario-level dependence, that bootstrap's "95%" intervals cover the truth ~45–59% of the time, and with a 5-scenario library per category (the prototype has 2–3), ranking accuracy plateaus near 64% for a 35-Elo gap *no matter how many votes arrive* — the binding constraint is scenarios, not votes. Ship: BT-with-ties, two-way clustered uncertainty (evaluator × scenario), estimated rater reliability instead of fixed credential multipliers, and per-task-family boards instead of one aggregate.

5. **Sequence: Phase 1 (weeks 0–6)** static arena on document-shaped task families with validity gates, rubrics, graded judgment, and a real scenario generator (≥30 parameterized scenarios/family). **Phase 2 (weeks 6–14)** expert review of *pre-recorded agent trajectories* from a sandboxed environment (reconciliation first) — this yields trajectory-level evaluation and process-supervision data at a fraction of live-workbench cost, following the AgentRewardBench pattern of experts judging recorded episodes [S: arXiv:2504.08942]. **Phase 3 (month 4+)** live interactive workbench only for the task families where the construct requires it (§2 Q4). The hybrid is the destination, but it is earned through the validation study in §13, not assumed.

**What not to do:** do not publish the current leaderboard (it ranks seeded synthetic votes against hard-coded quality tiers — §15); do not claim calibration measurement from one trap per session (a 60%-accurate rater passes the current "Calibrated" bar 34% of the time after five sessions — §8); do not treat user-typed prompts as benchmark items (the prototype already silently discards them — §15, which is the right instinct but the wrong UX).

---

## 2. Direct answers to the seven questions

### Q1. Can a useful arena be as simple as "which of two outcomes is better," five times?

**Short answer [I]:** it is useful for exactly one construct — *comparative professional preference among static work products on a single scenario* — and it measures that construct inefficiently. It cannot measure correctness, consistency, process quality, or long-horizon capability, and treating its output as "accounting-agent capability" is a construct-validity error.

**What the current design actually measures.** The prototype's "five comparisons" are four preference votes on one scenario by one evaluator (two semifinals, a final, a third-place match) plus one hidden rater-calibration trap (`backend/app/services/arena.py:22,101-106`; trap outcome routed to `trap_results`, never `votes`, `arena.py:155-163`). So a completed session contributes four *dependent* pairwise observations: same evaluator, same scenario, same moment, and the final/third-place pairings are themselves functions of the semifinal outcomes (`arena.py:192-206`). Under a Bradley–Terry lens this is one clustered mini-tournament, not five votes.

**What such a signal can support [S+I]:**
- Chatbot Arena demonstrates that blinded pairwise preference at scale yields a stable ranking of *general chat helpfulness*, with crowd-vs-expert agreement of 72.8–83.1% on their validation battles, and expert-vs-expert agreement 79.4–89.8% [S: Chiang et al., PMLR 235, Table 3]. Preference voting is not inherently unscientific.
- But accounting diverges from chat in the two ways that matter. First, an objective core exists: an unbalanced entry is wrong regardless of preference, and a rater can fail to notice — that is precisely why the prototype's traps exist. A preference vote records *whether the rater noticed*, not *whether the work is right*. Second, on the judgment layer, professionals genuinely disagree: DesignPref found professional designers' pairwise preferences have Krippendorff's α = 0.25 (binary) and that personalized preference models beat a single aggregate model even with 20× less data [S: arXiv:2511.20513]. If accounting judgment behaves similarly (an open question — falsifiable hypothesis H1, §16), a single aggregated preference board partially averages away real, legitimate disagreement (the Pluralistic Leaderboards critique [S: arXiv:2606.02547]).
- What preference-of-final-artifacts structurally cannot see: **consistency** (τ-bench's pass^k: agents that look strong on one run fail across repeated trials — gpt-4o pass^1 61.2% retail but pass^8 <25% [S: arXiv:2406.12045]; APEX-Accounting: best Mean Criteria@3 56.4% but max Pass^8 2.6% [S: arXiv:2607.27189]); **process** (side effects, unnecessary actions, policy violations — the things AgentRewardBench had experts label because neither rules nor LLM judges catch them reliably [S: arXiv:2504.08942]); and **state correctness** (τ-bench and WebArena grade the resulting database state, not the artifact [S]).

**Efficiency note [S+I]:** even for the construct it does measure, the bracket is a weak instrument. K-Sort Arena's premise is that one K-wise ranking of 4 comparable outputs supplies ≈ K(K−1)/2 = 6 pairwise comparisons of information at similar human cost, converging in their simulation with 716 comparisons where Elo-style pairwise needed 11,692 [S: arXiv:2408.14468]. The prototype already renders 4 outputs; asking for a ranking (with ties allowed) instead of a 4-vote bracket collects more information per session with less dependence artifice.

**Verdict [R]:** keep blinded comparison as the *layer-3* instrument, restructured as one K-wise graded judgment per scenario with abstention options, sitting on top of gates and rubrics. Do not present it, alone, as a measure of accounting-agent capability.

### Q2. How should objective correctness combine with professional judgment?

**Recommendation [R]: deterministic validity gate → criterion scoring → preference within the acceptable set, with all three recorded per episode.** Concretely:

1. **Layer 1 gate runs first, programmatically, before any human sees the output.** Debits = credits; amounts tie to source documents; correct period and entity; required accounts exist in the CoA; policy constraints (e.g., capitalization threshold) respected; in interactive tasks, the end-state checks and prohibited-action list (ToolSandbox's "minefields" [S: ACL Anthology 2025.findings-naacl.65]). This is cheap, reproducible, and, per WebArena Verified, must itself be audited — their re-audit of WebArena's 812 checkers found pervasive false negatives from brittle matching, fixed with type- and normalization-aware comparison and backend-state verification [S: NeurIPS 2025 workshop; github.com/ServiceNow/webarena-verified].
2. **Layer 2 criterion rubric, expert-authored per task family, graded per criterion.** APEX-Accounting is the direct precedent: binary unweighted criteria, ~13.7 per task, "one fact or judgment per criterion," judge validated against expert majority at 97.1% accuracy, human Fleiss' κ = 0.857 on criterion labels [S: arXiv:2607.27189]. In the arena the criterion grader can be programmatic where possible, LLM-judged where validated, and human for judgment criteria.
3. **Layer 3 preference is asked only between outputs that pass layer 1** (both-pass pairs), with `tie / both acceptable / both unacceptable / not enough information` available. Where a layer-1-failing output is shown anyway (deliberately — this is what the calibration system becomes, §8), the vote scores the rater and feeds the failure dataset, never the professional-quality rating.

**Why not preference-first?** Three sourced reasons. (a) Presentation confounds are large and measurable: LMArena's style-control regression found answer length the dominant stylistic coefficient (0.249, vs 0.019–0.031 for markdown features) and rank shifts of 5–12 places for some models once style is adjusted [S: lmsys.org/blog/2024-08-28-style-control]. Accounting's equivalent — confident memos, tidy tables over wrong numbers — is built into this very repo's broken artifacts. (b) Human detection of planted objective errors is imperfect (that is the empirical premise of the prototype's traps; Chatbot Arena attributes most crowd-expert disagreement to "crowd user making mistakes or overlooking factual errors" [S: PMLR 235]). (c) Votes contaminated by undetected invalidity are also poor training data: reward-model learning inherits the error (§2 Q6).

**Why not correctness-only?** Because layers 2–3 are where the product's differentiation and the field's open problem live: APEX's own limitation section concedes coverage limits, and no rubric benchmark measures *which professionally-acceptable treatment practitioners prefer* — materiality thresholds, documentation style, when to ask a clarifying question (ToolSandbox found "Insufficient Information" among the hardest categories even to evaluate [S]). The layered design records both and never lets one masquerade as the other.

**Analysis choice [R]:** collect preference *alongside* criterion scores in the same session (not in separate sessions) — the marginal evaluator cost is small and the paired data lets you estimate how much of preference is explained by rubric criteria (validation study, §13).

### Q3. Task source: prebuilt bank, user prompts, or generated scenarios?

**Recommendation [R]: a versioned bank of parameterized, expert-reviewed scenario generators is the only thing that gets ranked. User prompts are routed — to an existing family/slice when they match, to an authoring queue when they don't — and are never silently promoted to benchmark items.**

Grounding:
- Ranking requires comparability and known ground truth. Every serious accounting/agent benchmark fixes its task set and freezes grading before comparing models (Ramp: "Every model receives the same frozen tasks, source materials, execution instructions, environment, timeout policy, and grading rubric" [S: labs.ramp.com]; APEX: expert-authored worlds with a "trap register cataloging every seeded contradiction" and independent expert baselining at a 1.1% defect rate [S: arXiv:2607.27189]). An arbitrary user prompt has none of that.
- Open prompts are, however, the best *discovery* channel: Chatbot Arena's fresh crowd prompts are its contamination defense [S: PMLR 235], and Dynabench institutionalized human-in-the-loop collection of examples that break current models [S: NAACL 2021]. User prompts should feed the bank's growth the way Dynabench feeds datasets: candidate → authoring → expert review → versioned release.
- The prototype currently displays a free-text prompt box but sends only `{category, scenario_id}` (`frontend/src/components/workspace/PromptComposer.tsx:49-52`), silently substituting a random prebuilt scenario (`backend/app/routers/battles.py:99`, `backend/app/scenarios.py:164`). The instinct (don't rank on unvalidated prompts) is right; the silent substitution is a trust liability — the user believes their prompt was measured. §10 specifies the honest version: visible routing with an explicit "matched to scenario family X / queued as new task" contract.

### Q4. Is an editable spreadsheet / simulated workspace more valuable than static documents?

**Answer [I, from sourced task analysis]: it depends on the task family, and the split is knowable in advance.** The decision rule: an interactive environment is required when (a) the deliverable is a *state change* rather than a document; (b) the construct includes *investigation* across sources or *tool competence*; or (c) you need *repeated runs* on the same initial state (consistency measurement). A static artifact suffices when the input context is fully presentable and the deliverable is the document itself.

- **Static-valid families** (§5 taxonomy): single journal-entry drafting from a described transaction; CoA mapping; flux/variance commentary *given* fixed statements; policy memos; classification/coding of presented transactions. Evidence that static evaluation is meaningful here: FinQA/ConvFinQA graded expert-authored numerical reasoning over fixed report extracts with execution accuracy [S: EMNLP 2021/2022]; the prototype's `journal-entry` and `coa-mapping` categories are of this shape (`backend/app/scenarios.py:81-151`).
- **Interactive-required families:** reconciliations (multi-source investigation is the construct — Ramp's sample task: reconcile POS vs platform reports, "bring the clearing account to zero, and propose a separate entry for every discrepancy" [S: labs.ramp.com]); month-end close orchestration; AP/AR flows with approvals; anything where APEX/Ramp/τ-bench-style end-state grading applies. APEX gives agents 91 tools across filesystem/docx/pdf/excel/mail/code/accounting software, and worlds average 73 input files [S: arXiv:2607.27189] — that workload cannot be flattened into a side-by-side document view without destroying the construct. SpreadsheetBench 2 shows the same for spreadsheet work: real business workbooks average 11.8 sheets and 593.5 cell modifications per task, and the dominant failure modes are *insufficient inspection* and *wrong target selection* [S: arXiv:2606.29955] — failure modes that only exist when the model must navigate the workbook.
- **The bridging insight [S+I]:** you can get most of the interactive families' evaluation value without a live user-facing workbench by having experts review *recorded* trajectories and end-state diffs — AgentRewardBench had 6 experts label 1,302 recorded web-agent trajectories for success, side effects, and looping, at 89.3% inter-annotator agreement on success [S: arXiv:2504.08942]. Phase 2 (§6) is exactly this.

Also note the consistency argument: pass^k requires k runs from identical initial state. A static display of one pre-generated artifact per model (the prototype's deterministic `professional.py:42` outputs) cannot measure it, and APEX/τ-bench show it is the single most discriminating metric for agentic accounting work (max Pass^8 = 2.6% across nine frontier models [S: arXiv:2607.27189]).

### Q5. How can synthetic scenarios be generated from user intent while staying deterministic, valid, reproducible, leakage-resistant, and useful?

Full protocol in §9. The short answer [R]: **seeded, schema-typed world generation with accounting invariants enforced by construction, discrepancies planted by a constraint solver against a ground-truth register, parameterized surface variants per logical task, mandatory expert playtesting, and versioned frozen releases.** Each element has a precedent: APEX's four-stage expert world-building with a seeded-contradiction register and novelty screening ("Every document is novel and screened against public sources") [S: arXiv:2607.27189]; WorkArena++'s compositional task generators with oracle solutions and programmatic validators [S: arXiv:2407.05291]; SpreadsheetBench's multiple perturbed test workbooks per instruction to separate robust solutions from overfit ones [S: arXiv:2406.14991]; LiveBench's rotation (~1/6 of questions replaced per update) for contamination resistance [S: arXiv:2406.19314]; BenchmarkCards for the documentation schema — noting, as a gap to improve on, that BenchmarkCards itself lacks contamination/versioning fields [S: arXiv:2410.12974].

### Q6. What data would actually help improve accounting agents?

Ordered by training value per unit of collection cost, with the caveat that these estimates of *value* are my inference from the training literature, not measured outcomes [I]:

1. **Outcome supervision with verifiable reward** — per-episode layer-1 invariant results + layer-2 criterion vectors on tasks with ground truth. This is directly usable as a reward signal (the τ-bench/APEX grading style) and is the scarcest commercial commodity: it requires the world + rubric infrastructure, not just votes.
2. **Expert corrections** — the rater edits the wrong entry / fixes the mapping / rewrites the memo paragraph. A correction converts a failure into a demonstration and localizes the error. No arena currently collects this; the prototype has no field for it (`Vote` schema, `backend/app/models.py:134-152`). Highest marginal value of any UI change.
3. **Process supervision** — milestone hits, tool-call sequences, state diffs, flagged side effects on recorded trajectories. The PRM literature for agents is young but converging on trajectory-derived step labels (Web-Shepherd's 40K step-level preference pairs with checklists [S: arXiv:2505.15277]; AgentPRM's TD-based step labels [S: arXiv:2511.08325]); expert side-effect labels are the ground truth those methods need (AgentRewardBench precedent [S]).
4. **Demonstrations** — expert "golden responses" (APEX requires one per task, scoring 100% on its rubric [S]) and oracle traces (WorkArena++ ships human-coded oracle solutions per task [S]). A by-product of scenario authoring if you mandate it.
5. **Preference data** — usable for reward-model training *only* with: rater-reliability estimates attached (Crowd-BT/am-ELO line [S: WSDM 2013; arXiv:2505.03475]), tie/both-bad options (dropping ties biases learned preference strength most where responses are close [S: arXiv:2410.05328]), layer-1 stratification (a preference between two invalid outputs is not a quality signal), and rater IDs preserved for pluralistic modeling (DesignPref [S]). Raw forced-binary anonymous-weighted votes — what the prototype stores — are close to untrainable.
6. **Leaderboard data** (the fitted ratings) — marketing and monitoring value; near-zero training value.
7. **Production telemetry** — out of scope until real deployments and consent frameworks exist; listed to keep the boundary explicit.

**Do not assume all votes are suitable for training [R]:** votes to exclude from any licensed training set: failed-gate pairs (except as detection labels), votes from raters below the reliability floor, sub-4-second votes (the behavioral floor already exists: `backend/app/services/arena.py:176-178`), and votes on scenarios later found defective (version linkage, §9).

### Q7. What exactly is being ranked?

**Recommendation [R]: the versioned unit of comparison is a full evaluation configuration:**

```
config_id = hash(model_id, model_version, scaffold_id, scaffold_version,
                 system_prompt_sha, toolset_id, tool_versions,
                 sampling_params, budget_policy, context_policy)
```

with two board classes:
- **Reference-scaffold boards:** foundation models compared under one arena-owned scaffold held constant (Ramp: "Agents run as ReAct toolbelt agents with a basic system prompt… Each episode boots an isolated sandbox" [S: labs.ramp.com]; APEX similarly fixes the harness and token/step budgets [S]). What is ranked is "model × reference scaffold," and the board must say so.
- **Product boards:** vendor products ranked as opaque versioned wholes (self-submitted or buyer-contributed, exactly as the prototype's provenance fields anticipate — `backend/app/models.py:60-70`), never interleaved with reference-scaffold rows without a visible badge and never described as ranking the underlying model.

Grounding: budget and scaffold change results more than model identity in agentic accounting — APEX's budget ablation moves Claude-Fable-5 from 11.8% to 55.2% Mean Criteria as the per-task budget goes $1→$50 [S: arXiv:2607.27189]; SpreadsheetBench 2 found shipping products (e.g., "Claude for Excel" at 15.4% on their subset) far below the same-family raw model in their scaffold [S: arXiv:2606.29955]. And The Leaderboard Illusion documents what happens when the ranked unit is fuzzy: undisclosed private variants and selective score retraction distorted Chatbot Arena rankings [S: arXiv:2504.20879]. Every rating row, vote, and episode must therefore carry `config_id`, `scenario_id@version`, `world_id@version`, `grader_version`, and `rater_id` — the provenance spine (§7, §9).

---

## 3. Competitive-methodology matrix

All entries verified against the primary sources listed in §17; access caveats noted per row. The core comparison table first; per-system details (ties, rater controls, contamination, cost, strengths, threats, transfer) follow.

| System | What is ranked/evaluated | Unit of analysis | Static vs interactive | Task source | Judge | Scoring | Repeated runs | Statistical model / CI |
|---|---|---|---|---|---|---|---|---|
| **Design Arena** [S: designarena.ai/about] | Generative models for visual/web design (14 categories) | Pairwise vote in a 4-model, 5-battle tournament | Static one-shot ("multi-turn… planned") | User prompts | Human crowd | Pairwise (tournament) | None | Bradley–Terry, Rating = 400·log₁₀(strength); no CI method documented; ~200-comparison "preliminary" threshold |
| **LMArena / Chatbot Arena** [S: PMLR 235:8359] | LLMs (general chat) | One crowdsourced battle (conversation + 1 vote) | Interactive conversation (avg 1.3 turns) | Open user prompts | Human crowd (+expert/GPT-4 validation studies) | Pairwise with tie/both-bad buttons | None per battle; volume (~8K votes/model) | BT by reweighted MLE; sandwich robust SEs (bootstrap compared); rank via simultaneous confidence sets; active sampling ∝ CI-reduction |
| **K-Sort Arena** [S: arXiv:2408.14468; CVPR 2025] | Image/video generative models | One K-wise (K=4) comparison | Static outputs | Platform prompts | Trained human evaluators (profs/grad students) | K-wise best-pick or full ranking, ties allowed | None | Bayesian Gaussian skill (μ, σ); conservative score μ−3σ; UCB exploration matchmaking; claims 716 vs 11,692 comparisons to converge (sim, 50 models, 5% noise) |
| **Ramp Accounting bench** [S: labs.ramp.com, via JS bundle] | 14 frontier models as accounting agents | Task episode (137 tasks × 3 attempts, 22 worlds) | Interactive (ReAct agent, sandbox, MCP gateway) | Frozen expert-built worlds + human-authored rubrics | Frozen LLM judge (GPT 5.6 Luna) over rubrics | Criterion partial credit (mean reward@3), solve rate, pass³ | 3 attempts/task; retry-uplift & inconsistency metrics | Interval shown per model but method not stated; "Small differences may not be statistically meaningful" |
| **APEX-Accounting** [S: arXiv:2607.27189] | 9 frontier models on close-cycle bookkeeping | Task (160 tasks, 10 worlds; 8 runs each; 11,520 trajectories) | Interactive (91 tools; 500 steps, 5M tokens cap) | 42 experts (median 11 yrs; 52.4% Big Four); 4-stage world build with trap register; independent baselining (1.1% criterion defect rate) | LLM judge (DeepSeek-v4-Flash, GEPA-optimized prompt) validated at 97.1% vs 3-expert majority | Binary unweighted criteria (~13.7/task); Mean Criteria@3 | 8 runs; Pass@8, Pass^8 | Task-level bootstrap, 10,000 resamples, 95% CI; Benjamini–Hochberg FDR on pairwise diffs |
| **SpreadsheetBench** [S: arXiv:2406.14991; NeurIPS 2024] | LLMs/products on real spreadsheet manipulation | Instruction (912) with avg 3 test-case workbooks | Both settings (single-round; 5-round ReAct w/ exec feedback) | Real Excel-forum questions, 2-tier annotator validation | Programmatic (cell-level exact match, OJ-style) | Soft (fraction of test cases) & hard (all-pass) | Multiple test cases per instruction (robustness, not stochastic reruns) | None reported |
| **SpreadsheetBench 2** [S: arXiv:2606.29955] | Agents on end-to-end business workbook workflows | Task (321; avg 11.8 sheets, 593.5 cell edits) | Interactive (SWE-agent scaffold, 50 turns, bash/view/submit) | Expert-authored from real filings (>1,500 expert-hours); dual independent expert review | Programmatic cell checks + VLM judge (GLM-4.6V) for visualization rubrics | Strict all-cell Accuracy + partial-credit Modification | None ("we do not report error bars or confidence intervals" — cost) | None |
| **τ-bench** [S: arXiv:2406.12045] | Tool-agent-user interaction (retail/airline) | Conversation episode vs DB ground truth | Interactive w/ LM-simulated user | Manual design + LM generation + manual validation via agent runs | Programmatic (final DB state + required info in responses) | Binary r = r_action × r_output | ≥3 trials; pass^k = E[(c choose k)/(n choose k)] | None (no CIs) |
| **ToolSandbox** [S: ACL 2025.findings-naacl.65] | LLM tool use with state & user simulator | Trajectory (1,032 scenarios) | Interactive, stateful, on-policy simulated user | 2 internal domain experts, seed-scenario branching | Programmatic trajectory matcher; GPT-4o user sim (error-annotated) | Milestones (DAG-matched) & minefields (must-not events, score-nullifying); similarity in [0,1], geometric-mean aggregation | 4 repeated trials per model | Geometric means; no CIs |
| **WorkArena++** [S: arXiv:2407.05291] | Web agents on enterprise (ServiceNow) workflows | Browser episode (682 tasks; ≤50 steps) | Interactive (BrowserGym, live instance) | Compositional generators from atomic tasks; oracle + validator per task | Programmatic validators | Binary success | Seeded curriculum (seeds 0–9 eval) | Success rate ± standard error |
| **WebArena** [S: arXiv:2307.13854] | Autonomous web agents | Browser episode (812 intents / 241 templates) | Interactive, self-hosted Docker sites | Annotator-authored, double-annotated; author-written checkers | Programmatic (exact/must-include/fuzzy-LLM match; program-based state checks) | Functional correctness, binary | Single run | None |
| **WebArena Verified** [S: NeurIPS'25 wkshp page + repo; PDF inaccessible] | Same 812 tasks, repaired measurement | Same | Same (plus offline HAR replay) | Full audit: "Every task, reference answer, and evaluator has been manually reviewed and corrected" | Deterministic checkers only (LLM-judge & substring matching removed; type/normalization-aware; backend-state verification) | Structured JSON status codes | n/s in accessible material | Template-level macro averages; 95% CIs; ~11% false-negative reduction on their baseline agent |
| **AgentRewardBench** [S: arXiv:2504.08942] | LLM judges of web-agent trajectories (meta-eval) | Recorded trajectory (1,302 from 4 agents, 5 benchmarks) | Static judging of interactive episodes | Stratified sampling from existing benchmarks | 6 expert humans (ground truth) vs 12 LLM judges | Binary labels: success, side effects, looping; judge precision/recall | n/a | 89.3% inter-annotator agreement on success; no CIs reported |

**Per-system notes — ties, rater quality, contamination, cost, strengths, threats, and what transfers to accounting:**

- **Design Arena.** Ties: no tie/both-bad vote documented. Rater controls: anonymization only. Contamination: n/a. Cost/latency: not documented. Strength: lowest-friction expert-adjacent judging loop; proof that a niche vertical arena can exist commercially. Threats: no annotator model, no CI method, one-shot only, no correctness layer. Transfers: the session UX shape and blinding. Does not transfer: using every tournament vote as an independent BT observation for professional work.
- **Chatbot Arena.** Ties: interface has tie/both-bad; paper's H∈[0,1] framing generalizes but deployed tie encoding is not specified in-text. Rater quality: conformal anomalous-voter detection (rank-based p-values + Fisher combination; ~90% TPR / 60–70% TNR on a hand-labeled set); expert validation studies. Contamination: fresh prompts; model-name leakage filtered by keyword. Cost: free crowd; 1–2K votes/day at publication. Strengths: the statistical gold standard for preference arenas (sandwich CIs, active sampling with measured gains — random needed 54% more samples for win-matrix precision). Threats: population bias (self-selected hobbyists), style confounds (their own later style/sentiment-control posts), and the gaming dynamics documented in The Leaderboard Illusion [S: arXiv:2504.20879]. Transfers: BT + clustered-robust uncertainty, active sampling, anomaly detection, expert-agreement validation design. Does not transfer: open uncurated prompts as the ranked task distribution.
- **K-Sort Arena.** Ties: allowed in both modes, absorbed in Bayesian update. Rater quality: trained expert voters, guidelines (50% alignment / 50% aesthetics). Cost: efficiency measured in votes. Strengths: K-wise information gain; uncertainty-aware matchmaking. Threats: visual-perception premise ("higher perceptual intuitiveness than texts") — reading four accounting workpapers is slower than glancing at four images, so the K-wise economics partially transfer at best; validated mostly in simulation. Transfers: rank-K-with-ties as the session primitive for ≤4 short artifacts; uncertainty-aware pairing. Does not transfer: assuming 4-way ranking is cheap for long documents.
- **Ramp Accounting bench.** Ties: n/a (absolute grading). Rater quality: human-authored rubrics; frozen judge; no judge-validation stats published on the page. Contamination: frozen synthetic worlds. Cost/latency: exemplary reporting (mean cost/run, cost per solve, p90 duration, tool calls, tokens). Strengths: worlds + rubrics + consistency metrics + cost, presented for practitioners. Threats: CI method unstated; judge unvalidated publicly; page content only recoverable from its JS bundle (fragile citation). Transfers: nearly everything methodological; it is the closest existing artifact to this product's evaluation layer — which is itself the competitive warning: the *benchmark* layer is being commoditized by vendors; the defensible layer is calibrated human judgment and preference/correction data, which Ramp's design does not collect.
- **APEX-Accounting.** Ties: n/a. Rater quality: the strongest published protocol in this space — 3 experts per criterion for judge validation, Fleiss' κ=0.857, judge 97.1% accuracy. Contamination: novel documents screened against public sources; closed private set. Cost: budget-standardized runs; Simpson's-paradox budget analysis. Strengths: world construction pipeline, criterion design rules, repeated-run metrics, honest power discussion ("With only 160 held-out tasks… two adjacent-rank pairs are statistically indistinguishable"). Threats: LLM-judge residual error; closed set limits scrutiny; excludes tax/audit/consolidation/multi-currency by their own statement. Transfers: world schema, criterion style, judge-validation protocol, task-level bootstrap + FDR. Does not transfer: absence of any human-preference or correction layer (their design goal differed).
- **SpreadsheetBench 1/2.** Ties: n/a. Rater quality: SB1 two-tier annotation + post-hoc audit (3.8% grader false-negatives found); SB2 dual independent expert solves. Contamination: SB1 revises forum text, perturbs data, moves answer positions; SB2 silent. Cost: SB2 explicitly skipped error bars for cost. Strengths: SB1's *multiple perturbed test workbooks per instruction* is the cleanest anti-overfitting device in the packet; SB2's failure taxonomy (inspection/target-selection dominate) tells you what trajectory review should look for. Threats: exact-match undercounts equivalent solutions (SB2's own limitation). Transfers: parameterized variants per logical task (adopted in §9); phase-structured trajectory analysis. 
- **τ-bench / τ²-bench.** Ties: n/a. Rater quality: iterated author validation of tasks; user-simulator error acknowledged. Cost: $0.38/$0.23 per task agent/user sim. Strengths: end-state grading; pass^k; the demonstration that user interaction collapses reliability (τ²: pass^1 drops 18–25% when the simulated user can act [S: arXiv:2506.07982]). Threats: no CIs; simulator artifacts. Transfers: pass^k (adopted), DB-state ground truth, user-simulator caution — an accounting arena's "requester" simulation must be validated or avoided in Phase 1.
- **ToolSandbox.** Milestones/minefields with DAG matching transfer directly to close-checklist and reconciliation scoring (§7); "Insufficient Information" scenarios transfer as the clarification-behavior construct. Threats: authoring cost of milestones ("many iterations, hindering scalability" per authors); geometric-mean aggregation is a modeling choice to revisit.
- **WorkArena++.** Compositional generation + oracle traces + cheap validators transfer as the scenario-generator architecture (§9). Threat noted by authors: single-platform scope; demographic skew in their human study.
- **WebArena → WebArena Verified.** The pair is the strongest available evidence that *checker quality is a first-class research object*: the Verified effort manually re-reviewed every task/answer/evaluator and replaced brittle matching with normalization-aware, backend-state checks. Transfers: audit-the-graders discipline; report template-level (here: family-level) aggregates with CIs. Caveat: primary PDF inaccessible (OpenReview wall); claims verified via the NeurIPS virtual page, GitHub README, and docs site only.
- **AgentRewardBench.** Transfers: the Phase-2 design (experts label recorded trajectories for success/side-effects/looping), the finding that rule-based evaluation *underreports* success while LLM judges *overreport* (best judge precision ≤70%), and the implication that neither can replace calibrated humans at the frontier of trust. Threat: their trajectories are web tasks; accounting side-effect taxonomy must be built (§11).

---

## 4. Annotated literature review

Grouped by role in this design. Publication status labels: **[PR]** peer-reviewed venue, **[PP]** preprint, **[CT]** company technical report / methodology page, **[PV]** partially verified (access caveat in §17).

**Preference arenas and ranking statistics.**
- Chiang et al., *Chatbot Arena* (ICML 2024) **[PR]** — the reference design: BT via reweighted MLE, sandwich CIs, simultaneous rank confidence sets, active sampling, conformal anomaly detection, expert-agreement validation (72.8–83.1% crowd-expert). Anchor for §12; its own limitations (population bias, helpfulness-only) motivate the vertical-expert variant.
- Li et al., *K-Sort Arena* (CVPR 2025) **[PR, PV: verified via arXiv v2; CVF page 403'd]** — K-wise ranking with Bayesian (μ,σ) skills and UCB matchmaking; efficiency claims are simulation-based. Motivates the rank-4-with-ties session primitive.
- Chen et al., *Crowd-BT* (WSDM 2013) **[PR]** — joint item-quality + annotator-reliability estimation (η per rater inside the BT likelihood); active triplet selection; 90% of gold-standard accuracy at 3% of labeling budget in their study. The intellectual ancestor of §8's reliability model; its 2025–26 successors: am-ELO (ICML 2025) **[PP/PR-claimed]** and Shejole et al. (UAI 2026, PMLR 337) **[PR, PV: landing page only]** — EM with Pólya-Gamma augmentation, robustness to spammers/adversaries with matrix-sensing guarantees.
- Christiano et al., *Deep RL from Human Preferences* (NeurIPS 2017) **[PR]** — trajectory-segment comparison works; ties get (½,½) targets; "can't compare" excluded; 10% rater-error mixture in the likelihood. Foundational for judging *trajectories*, not just artifacts.
- Knox et al., *Models of Human Preference…* (arXiv 2206.02231; TMLR 2023 per secondary confirmation) **[PR, PV on venue]** — preference-generation model matters: regret-based preferences are identifiable where summed-reward preferences are not. Design consequence: elicit preferences over *outcomes within comparable contexts*, and be suspicious of aggregating preferences across segments with different difficulty.
- Liu, Ge & Zhu, *Reward Learning From Preference With Ties* (arXiv 2410.05328) **[PP]** — Rao-Kupper generalized BT; dropping ties biases Δr̂ most when Δr*≈0, bounded by log((1+θ²)/2θ). Note: the research brief for this project described the paper as covering "Rao-Kupper / Davidson" — the fetched paper uses Rao-Kupper only; reported as a discrepancy per the contradictory-evidence standard.
- Peng, Bigham & Wu, *DesignPref* (arXiv 2511.20513) **[PP]** — 20 professional designers × 600 pairs: Krippendorff's α = 0.248 (binary), 28.5% of pairs at ≥96% pairwise disagreement; personalized judges beat aggregate ones with 20× less data. The strongest available warning against a single "taste" leaderboard for professional judgment.
- Haghtalab et al., *Pluralistic Leaderboards* (arXiv 2606.02547) **[PP]** — BT collapses heterogeneous user populations; identical pairwise data can hide a 40% minority that dislikes the entire BT top-3; proposes locally-stable committee/ranking mechanisms with Õ(k) queries per user. Motivates §7's segmented boards (by role/policy-regime) over one aggregate.
- Shi et al., *position bias in LLM-as-judge* (IJCNLP-AACL 2025) **[PR, PV: landing page]** — >150K judged instances: position bias varies by judge/task, driven by quality gap between candidates. Constraint on any LLM pre-grader in §7 (A/B swap protocol mandatory, as Plan-RewardBench also enforces).
- Singh et al., *The Leaderboard Illusion* (arXiv 2504.20879) **[PP]** — documented private-variant testing and data asymmetries distorting Chatbot Arena. Motivates §7's versioned-config policy and public change logs.
- LMArena *style control* and *sentiment control* posts **[CT]** — BT with style covariates (length coefficient 0.249 dominates); sentiment adjustment reorders top models. Motivates collecting presentation covariates per artifact and reporting style-controlled boards.

**Multi-turn agents and trajectory evaluation.**
- Yao et al., *τ-bench* (arXiv 2406.12045) **[PP; ICLR 2025 acceptance not verified on fetched pages]** and Barres et al., *τ²-bench* (arXiv 2506.07982) **[PP]** — end-state DB grading, pass^k, user-simulator effects. Adopted: pass^k, end-state ground truth; avoided in Phase 1: LM user simulation.
- Lu et al., *ToolSandbox* (NAACL Findings 2025) **[PR]** — milestones/minefields over trajectories with DAG matching; on-policy user simulator with measured error; "Insufficient Information" as a first-class category. Adopted: milestone-DAG scoring, prohibited-action minefields, clarification-behavior tasks.
- Lù et al., *AgentRewardBench* (arXiv 2504.08942) **[PP]** — experts as trajectory ground truth; LLM judges ≤70% precision; rules underreport / LLM judges overreport success. Adopted: Phase-2 recorded-trajectory review; two-sided judge-error framing.
- Boisvert et al., *WorkArena++* (arXiv 2407.05291; NeurIPS 2024 D&B per listing, venue not on fetched page) **[PR-claimed, PV]** — compositional generators, oracles, validators; humans 93.9% vs GPT-4o 2.1% on the shared subset. Adopted: generator+oracle+validator triple per scenario.
- Zhou et al., *WebArena* (arXiv 2307.13854) **[PP; ICLR 2024 not verified on fetched page]** and *WebArena Verified* (NeurIPS 2025 workshop) **[PV]** — execution-based grading and the necessity of auditing it.
- Wang et al., *Plan-RewardBench* (arXiv 2604.08178) **[PP]** — 1,171 trajectory preference pairs; best evaluator 69.96% pairwise accuracy; judge accuracy collapses beyond ~32K-token contexts, "several evaluators fall below random chance" long-horizon. Direct warning for LLM-judging long accounting trajectories; humans stay in the loop at exactly the episode lengths accounting produces.
- Levy et al., *ST-WebAgentBench* (arXiv 2410.06703, ICLR 2026 per page) **[PR-claimed]** — Completion-Under-Policy metric; agents' CuP "less than two-thirds of their nominal completion rate." Adopted: policy-compliance-gated success (layer 1 includes policy).
- Chae et al., *Web-Shepherd* (arXiv 2505.15277, NeurIPS 2025 spotlight per page) **[PR-claimed]**; Xi et al., *AgentPRM* (arXiv 2511.08325) **[PP]** — the process-reward-model demand side for the §2 Q6 data products.

**Accounting, finance, spreadsheets.**
- *APEX-Accounting* (arXiv 2607.27189) **[CT/PP: Mercor + Ramp technical report]** — see §3; the central precedent. Note its honest self-limits: close-cycle only; 160 tasks bound statistical power.
- *Ramp Accounting bench* **[CT, PV: JS-bundle extraction]** — see §3.
- Ramp Builders posts (*Stack Benchmarking*; *financial benchmarks*) **[CT]** — internal 237-task/8-world bench with 5-run Pass^5 and "roll-forward worlds" testing whether agent memory transfers across periods without contaminating the next close; a taxonomy hint (§5) and a versioning idea worth borrowing.
- Ma et al., *SpreadsheetBench* (NeurIPS 2024 spotlight) **[PR]**; Zhu et al., *SpreadsheetBench 2* (arXiv 2606.29955) **[PP]** — see §3.
- Chen et al., *FinQA* (EMNLP 2021) **[PR]**; Chen et al., *ConvFinQA* (EMNLP 2022) **[PR]** — expert-authored numerical reasoning with gold programs; expert ceiling ~89–91% execution accuracy vs crowd ~47–51% — a measured expert/layperson gap that supports the expert-panel thesis. Insufficient as agent benchmarks (static extracts, no state).
- Krumdick et al., *BizBench* (ACL 2024) **[PR]** — CFA/CPA-derived program-synthesis tasks; hidden test sets against contamination. Useful item bank for rater-screening questions more than for agent ranking.
- Islam et al., *FinanceBench* (arXiv 2311.11944) **[PP]**; Bommarito et al. CPA-exam study (arXiv 2301.04408) **[PP]**; CA-Ben (arXiv 2506.21031) **[PV]** — context on knowledge-level finance evals; none evaluate stateful work.

**Benchmark construction.**
- Liang et al., *HELM* (arXiv 2211.09110) **[PP; TMLR status not verified]** — scenario taxonomy, multi-metric, disaggregated reporting; adopted as the reporting philosophy (§7 boards).
- Kiela et al., *Dynabench* (NAACL 2021) **[PR]** — human-and-model-in-the-loop collection; validated model error rate; ~2× cost per example vs static, justified by longevity. Adopted for the unmapped-prompt → authoring pipeline (§10).
- White et al., *LiveBench* (arXiv 2406.19314; ICLR 2025 spotlight per page) **[PR-claimed]** — rotation (1/6 per update), objective scoring, LLM-judge avoidance rationale, rank stability >0.997 across updates. Adopted for versioned rotation (§9).
- Sokol et al., *BenchmarkCards* (arXiv 2410.12974) **[PP]** — 30-field documentation standard; adopted for scenario-release documentation, extended with the contamination/versioning fields it lacks.
- Aleithan et al., *SWE-Bench+* (arXiv 2410.06992) **[PP]** and Prathifkumar et al. (arXiv 2512.10218) **[PP]** — measured leakage/weak-test rates in SWE-bench (32.67% solution leakage; 31.08% weak tests) and memorization effects (3× score gap vs contamination-aware sets). The cautionary tale §9's leakage controls are designed against. SWE-bench Verified **[CT, PV: mirror-verified]** — 93 engineers screening tasks, 68.3% filtered out: expert audit changes benchmarks materially.

---

## 5. Accounting task taxonomy

Built from official vendor documentation fetched 2026-09-04 (Rillet, Campfire, Basis/getbasis.ai, Numeric, Puzzle, Digits, Pilot, Intuit/QuickBooks, Ramp — URLs in §17.3). Vendor claims are **[S]**; the groupings and the last four columns are **[I]**. Verification caveats: Basis was verified via getbasis.ai raw HTML (basis.so returned 403); one Intuit accountant-page quote and Pilot's Meridian are search-snippet-identified only.

| # | Task family | Typical inputs | Output type | Objectivity vs judgment [I] | Horizon [I] | Static-valid? [I] | Observed at (examples) [S] |
|---|---|---|---|---|---|---|---|
| 1 | Document capture & extraction | PDFs/scans/emails, prior returns | Structured records | High objectivity | Single-shot | Yes | Ramp (line-item invoice OCR), Basis tax intake, Digits |
| 2 | Transaction categorization / coding | Bank/card feed, CoA, history, policy | Ledger state change | Mostly objective; policy tail | Continuous stream | Yes (batch form) | Ramp Accounting Agent, Digits AGL, Puzzle, Pilot, Intuit Accounting Agent, Basis, Campfire, Rillet |
| 3 | Matching & reconciliation (bank, payment↔invoice, PO 2/3-way, GL↔subledger) | Statements, ledger, subledgers, POs | State change + exception list | Match objective; exception resolution judgmental | Multi-step | **No — interactive** | All nine vendors |
| 4 | Journal entries & recurring schedules (accruals, prepaids, depreciation) | Source docs, contracts, policy, prior schedules | Entry + workpaper | Computation objective; estimates judgmental | Recurring monthly | Yes (single-entry); No (schedule roll-forward) | Rillet (proposes accruals), Numeric (JEs to NetSuite), Digits Automated Schedules, Ramp, Basis, Campfire, Puzzle |
| 5 | Revenue recognition & AR/billing | Contracts, billing/usage data | Schedules + entries; invoices | Rules-based post-policy; policy setup judgmental | Recurring multi-step | Partially (memo/schedule yes; system flow no) | Rillet (ASC 606, usage-based), Campfire, Puzzle, Digits, Intuit Payments Agent |
| 6 | AP & payment execution | Bills, POs, vendor master, approval policy | State change incl. money movement | Objective + fraud/exception judgment; universal human gate ("no money ever moves without a human confirmation" — Ramp) | Multi-step w/ approvals | No — interactive | Ramp AP agents, Digits Bill Pay, Rillet |
| 7 | Expense/policy compliance | Card txns, receipts, policy | Approvals/flags | Policy-objective; edge cases escalate | Continuous | Yes (batch form) | Ramp, Intuit Assist, Campfire |
| 8 | Anomaly/exception surveillance | Live GL stream | Flags/alerts | Detection objective-ish; triage judgmental | Always-on | No (needs stream) | Rillet Continuous AI, Numeric monitoring, Pilot, Digits |
| 9 | Month-end close orchestration | Close checklist, ledger, schedules | Checklist state + document trail | Completeness objective; sequencing judgmental | Multi-day — canonical long-horizon | No — interactive | Numeric, Rillet, Campfire, Digits Agentic Close, Basis ("59% of our close checklist" customer quote), Ramp Stack |
| 10 | Flux/variance analysis & commentary | TB/GL by period, budget, drivers | Narrative + tables | Numbers objective; explanation judgmental | Per close | Yes (given data) / No (investigation variant) | Numeric ("flux on autopilot"), Campfire, Basis, Ramp Stack |
| 11 | Reporting & consolidation | TB, multi-entity ledgers, FX | Statements, packs, elimination entries | Mechanics objective; presentation/disclosure judgmental | Multi-step | Partially | Rillet, Campfire, Basis (draft FS + footnotes), Numeric |
| 12 | Ledger Q&A / ad-hoc analysis | Ledger + NL question | Answer/analysis | Varies | Short | Yes (frozen extract) | Rillet Aura Assistant, Campfire Ember, Ask Digits |
| 13 | Tax prep & compliance | Prior return, client docs, workpapers | Workpapers + return drafts | Assembly objective; positions judgmental | Multi-day + client back-and-forth | No — interactive | Basis Tax, Intuit tax agents, Pilot |
| 14 | Audit execution & support | TB, PBC docs, firm methodology | Cited workpapers, drafted FS | Tests objective; sufficiency judgmental | Multi-week | No — interactive | Basis Audit |
| 15 | Forecasting / planning / advisory | Historicals, KPIs, scenarios | Models/analyses | High judgment | Multi-step | Yes (given data) | Intuit Finance Agent, Pilot CFO services, Campfire |

**Cross-cutting patterns [S+I]:** every vendor pairs agents with audit trails and confidence-gated human review ("first pass / start at review" is the near-universal framing: Basis, Ramp Stack, Puzzle, Rillet, Intuit); two interface archetypes exist — AI-native ledgers (Rillet, Campfire, Puzzle, Digits) vs overlay agents on QuickBooks/NetSuite/spreadsheets (Numeric, Ramp, Basis, Pilot-on-QBO, Intuit) — which is why the recommended workbench (§6) is a *neutral* ledger+spreadsheet+documents sandbox rather than a clone of any one product.

**Coverage assessment of the prototype [I]:** the current finance bank covers slivers of families 4 and a stylized form of CoA management (3 journal-entry + 2 CoA scenarios; `backend/app/scenarios.py:81-151`) — roughly 2 of 15 families, in static miniature. Content validity for a claim like "accounting-agent leaderboard" requires at minimum families 2, 3, 4, 9, 10 (the close-cycle core that APEX also chose, and where vendor products overlap most).

---

## 6. Three architectures compared

The brief demands the hybrid not be assumed. Here is the honest comparison [I except where cited].

### Architecture A — lightweight static work-product arena (the prototype's lane, upgraded)

Prompted scenario → N pre-generated final artifacts → layer-1 programmatic gate → blinded expert session (K-wise ranking with ties/both-bad, 2–4 criterion ratings, confidence, optional correction) → BT-with-ties fit with clustered uncertainty.

- **Complexity:** low. Extends the existing FastAPI/SQLite skeleton; new tables for criteria/corrections; a real scenario generator.
- **Scientific validity:** valid for the static-valid families in §5 (≈6 of 15, in constrained forms) *provided* the gate, rubric, tie options, and clustered statistics exist. Invalid as a general "accounting-agent capability" claim: no state, no consistency, no process (§2 Q1/Q4).
- **Evaluator burden:** lowest — 3–6 min/session (the prototype's own design target: "outputs a professional can judge in 2–5 minutes," `backend/app/categories.py:5-6`).
- **Usefulness to practitioners:** moderate — familiar artifacts, immediate.
- **Usefulness to model developers:** moderate — preference + rubric + correction data on final artifacts; no trajectories.
- **MVP feasibility:** weeks.

### Architecture B — sandboxed multi-turn accounting workbench

Persistent synthetic company world (ledger + subledgers + documents + spreadsheets + mail), tool API, episode runner with reset/teardown, state-diff logging, milestone scoring; agents run live; humans review episodes and/or interact.

- **Complexity:** high. This is APEX/Ramp-class infrastructure: 91 tools and 500-step budgets (APEX [S]), isolated sandboxes with MCP gateways (Ramp [S]). Ramp reports mean episode wall-clock of ~6 minutes and mean cost up to $4.30/run for frontier models [S: labs.ramp.com]; APEX runs took 12–81 minutes per episode [S]. Multiply by k repeats × tasks × configs.
- **Scientific validity:** highest for families 3, 6, 9, 13, 14 — end-state ground truth, pass^k, process measures. But without a human layer it duplicates APEX/Ramp (already built, better-funded), and its LLM-judged rubric layer inherits the judge-precision ceiling AgentRewardBench documents (≤70% precision for trajectory judges [S]) unless human-validated like APEX's.
- **Evaluator burden:** highest — reviewing a multi-tool trajectory is slower than comparing two documents; AgentRewardBench's experts labeled recorded trajectories, and APEX's judge validation cost 3 experts × 1,687 criteria [S].
- **Usefulness to practitioners:** high ceiling (it looks like their actual work) but slow to reach.
- **Usefulness to model developers:** highest — trajectories, state diffs, outcome supervision, process labels.
- **MVP feasibility:** months; the scenario/world bank is the long pole (APEX used 42 experts, ~14 per world [S]).

### Architecture C — hybrid router

Task families route to the mode that matches their construct (per §5 column "Static-valid?"): static artifacts through the A-pipeline; stateful families through the B-pipeline; both feed one provenance-spined data model and family-level boards.

- **Complexity:** A + B + routing + one unified schema. Strictly more than either.
- **Scientific validity:** the only architecture that can honestly cover the taxonomy; validity per family equals that of the mode it routes to.
- **Burden/feasibility:** inherits B's costs for the families that need B.

### Verdict [R]

**Hybrid is the correct destination, but the evidence-based sequencing matters more than the label:**

- **Phase 1 (A′):** static arena on families 2, 4, 10, 12, 15 (constrained forms) with gates/rubrics/graded judgment and a ≥30-scenario-per-family generator. Rationale: evaluator supply and scenario coverage — not software — are the binding constraints (§12 shows more votes cannot compensate for few scenarios), and A′ is where the calibration/rater-reliability machinery gets built and validated cheaply.
- **Phase 2 (B-offline):** stand up the world + tool sandbox, run agents *offline*, and have experts judge **recorded trajectories and end-state diffs** for the reconciliation family (family 3). This captures most of B's data value (trajectories, state diffs, side-effect labels) at A-like session cost, on the AgentRewardBench pattern [S]. It also produces the criterion-validity dataset: do Phase-1 static preferences predict Phase-2 environment outcomes? (§13, §16 H2.)
- **Phase 3 (full C):** live interactive workbench (user-in-the-loop episodes, clarification behavior) only for families and buyers that the Phase-2 evidence justifies.

The honest anti-hybrid consideration: if the §13 validation study shows expert preference among gate-passing static artifacts is (a) reliable (α ≥ ~0.4) and (b) predictive of environment outcomes, a leaner A′-heavy product is defensible and B becomes a data-licensing back office. If (a) fails, the preference layer — the product's current identity — needs rework regardless of architecture. Run the study before scaling either.

---

## 7. Recommended measurement model

### 7.1 The four quality layers

Per episode (an episode = one config attempting one scenario version once):

- **L1 — hard validity constraints** (programmatic, blocking): entries balance; amounts tie to source documents within stated tolerance; correct period/entity; accounts exist in CoA and are of legal type for the posting; policy compliance (thresholds, approval rules); for interactive episodes: required end-state assertions pass, no prohibited actions (minefields), environment left consistent (subledger↔GL tie, bank clearing at target). Output: pass/fail + violation codes (WebArena-Verified-style structured statuses [S]).
- **L2 — criterion-level professional quality** (rubric): completeness, evidence coverage/citations, materiality handling, controls awareness, documentation/memo quality, auditability of the trail, appropriateness of clarification requests. APEX criterion rules apply: one fact/judgment per criterion, self-contained, outcome-anchored [S: arXiv:2607.27189]. Graders: programmatic where possible → validated LLM judge (with A/B-swap and human-validation protocol) → human for judgment criteria.
- **L3 — comparative preference among acceptable outputs**: K-wise ranking with ties (or pairwise with the full response set below) asked only across L1-passing outputs; captures the residual "which would you sign?" signal that rubrics under-specify.
- **L4 — operational measures**: cost (standardized token pricing, as APEX [S]), latency, steps/tool calls, retries, unnecessary actions, side effects, recoverability after injected errors; consistency across repeats (pass^k, criterion-score variance). Reported, never blended into the quality score (HELM's multi-metric disaggregation stance [S: arXiv:2211.09110]).

**Gate policy [R]:** L1 failure blocks the episode's votes from the professional-quality rating and from any preference-training export, but the episode is retained in: the failure taxonomy, detection-rate statistics (did human raters notice?), rater calibration scoring, and negative-example training data. This answers the brief's question directly: yes, block; no, don't discard.

### 7.2 Allowed judgment responses

Pairwise: `A better | B better | equivalent (both acceptable) | both unacceptable | not enough information to judge` + per-vote confidence (3-point) + optional 1-sentence rationale + optional correction. K-wise: full ranking with ties allowed + per-artifact `acceptable? (yes/no/can't tell)` checkboxes — which yields the both-bad and gate-audit signal in one gesture. Grounding: Chatbot Arena ships tie/both-bad [S]; Christiano et al. found "can't compare" must be separable from ties [S]; the ties paper quantifies the cost of omission [S]; ToolSandbox's Insufficient-Information category shows abstention is signal, not noise [S].

### 7.3 Rating model

- **Core:** Bradley–Terry with ties (Rao-Kupper: P(i≻j) = πᵢ/(πᵢ+θπⱼ), θ≥1 [S: arXiv:2410.05328]) fit per task family on L3 data from L1-passing pairs, weighted by *estimated* rater reliability (§8), never by credential tier constants.
- **Target model (as data grows):** hierarchical/mixed-effects extension — logit(P) = (βᵢ−βⱼ) + (bᵢₛ−bⱼₛ) + rater terms, with scenario-level random effects bₘₛ and rater discrimination (Crowd-BT η [S: WSDM 2013] / am-ELO-style ability [S: arXiv:2505.03475]). Until the fitting infrastructure exists, approximate its uncertainty consequences with two-way clustered bootstrap (§12).
- **Presentation covariates:** log length, table count, headings, hedging markers recorded per artifact; publish both raw and style-controlled boards (LMArena method: BT logistic regression with additive style features, normalized (A−B)/(A+B) [S: lmsys.org style-control post]).
- **Boards (disaggregated by default):** per task family × {L2 mean criterion score, L3 preference rating, L4 consistency (pass^k where applicable), L4 cost}; segment views by rater role (controller vs auditor vs bookkeeper) and policy regime once populated — the Pluralistic-Leaderboards and DesignPref evidence says a single aggregate can misrepresent coherent professional minorities [S: arXiv:2606.02547; arXiv:2511.20513]. An "overall" number, if shown at all, is an explicitly-weighted composite with the weights published, HELM-style [S].
- **Uncertainty:** 95% intervals from evaluator×scenario clustered bootstrap (§12); ranks displayed with interval-based rank sets (Chatbot Arena's simultaneous-CI ranking [S: PMLR 235]); models below a minimum-exposure threshold shown as "provisional" (Design Arena uses ~200 comparisons [S: designarena.ai/about]; our threshold derives from §12 power analysis per family, not a copied constant).
- **Active sampling:** start with balanced random assignment; add uncertainty-directed pairing (Chatbot Arena's CI-reduction rule; K-Sort's UCB matchmaking [S]) only after the anomaly-detection layer exists, since adaptive sampling + adversarial raters interact badly (the conformal method in Chatbot Arena assumes exchangeability within pairs [S]).

### 7.4 Schemas (minimum viable, versioned)

**Task/scenario** (per version, immutable once released):
```
scenario: {scenario_id, version, family_id, world_id@version, generator_id@version,
           generator_seed, params, brief, artifacts[], hidden_ground_truth{
             expected_postings|mapping_key|discrepancy_register|solution_set},
           invariants[] (L1 checks, machine-executable),
           rubric[] {criterion_id, text, grader: prog|llm|human, weight=1},
           milestones[] (DAG, interactive only), minefields[],
           acceptable_solution_policy, difficulty_est, leakage_screen_result,
           authors[], reviewers[], review_status, release_batch, retired_at?}
```
**Episode/trajectory:**
```
episode: {episode_id, config_id (§2 Q7), scenario_id@version, run_index (for pass^k),
          started/ended, transcript[] {step, tool_call, args_hash, observation_ref},
          state_diffs[] {step, entity, before_ref, after_ref},
          final_artifacts[], env_init_snapshot_ref, env_final_snapshot_ref,
          L1_results{pass, violations[]}, L2_results[{criterion_id, grade, grader_id@version}],
          L4{cost_usd_standardized, latency_s, steps, retries, side_effects[]}}
```
**Judgment:**
```
judgment: {judgment_id, session_id, rater_id, scenario_id@version,
           items[] (episode_ids or artifact_ids), response {ranking|pair_choice,
           ties, acceptability[], confidence, rationale?, correction_ref?},
           decision_ms (server-side, as arena.py:121-128 already does),
           is_gold_item, gold_key_ref?, ui_variant, position_permutation}
```
**Provenance/version fields required everywhere:** `config_id`, `scenario_id@version`, `world_id@version`, `grader_id@version`, `generator_id@version+seed`, `rubric_version`, `rater_id`, `release_batch`. Environment lifecycle: `init` from world snapshot (content-addressed), `reset` = restore snapshot (deterministic, as WebArena's Docker-image reset [S]), `teardown` = archive final snapshot + diffs. Observable state vs hidden truth: the agent/rater sees world artifacts; `hidden_ground_truth` and the discrepancy register are never serialized to any client (the prototype already enforces the analogous rule for model identity, `backend/app/routers/battles.py:45-85`).

**Privacy/consent/licensing [R]:** rater consent at signup covering (a) research use, (b) anonymized publication of aggregate statistics, (c) an explicit, separately-consented tier for training-data licensing of their judgments/corrections with revocation forward-only; per-judgment license flags in the export pipeline; no client data ever (the "we bring the doc" stance, `backend/app/scenarios.py:1-8`, is correct — keep it); vendor-submitted product outputs governed by submission terms recording redistribution and training rights (the buyer-contributed path in the PRD implies a licensing question the schema must answer per row: `provenance`, `submitted_version` already exist in `backend/app/models.py:69-70`). BenchmarkCards' Ethical & Legal fields (privacy, licensing, consent, compliance) adopted as the release checklist [S: arXiv:2410.12974].

---

## 8. Rater and calibration methodology

### 8.1 What the prototype does and why it under-delivers

Fixed credential-tier weights {anon 0, free-mail 0.25, work-domain 1.0, license 1.5, named 2.0} multiply votes directly in the BT fit (`backend/app/services/arena.py:24-26,167`; `backend/app/services/ratings.py`); one hidden trap per 5-vote session scores calibration (`arena.py:87-99,155-163`); a "Calibrated Reviewer" badge requires ≥80% trap pass rate (`backend/app/services/reviewer.py:56-58`); trap pass rate never feeds vote weight (explicitly deferred: `docs/PRD.md:123-128`).

Problems, quantified [I, Appendix A Sim 4]:
- **One trap per session is too slow to measure anything.** With the ≥80%-of-5 badge rule, a rater with true 60% detection accuracy earns "Calibrated" 33.7% of the time; even at n=10 traps, 16.7%. To *estimate* a rater's accuracy within ±0.10 takes ~61–81 gold items — at 1 trap per ~5-minute session, ~5–7 hours of judging before the number means anything.
- **Fixed multipliers have no empirical basis and add variance if mis-set.** No fetched source supports credential-proportional weights; the literature line (Crowd-BT → am-ELO → Shejole 2026) instead *estimates* per-rater reliability jointly with item quality and shows it beats majority/uniform weighting on real crowd data (Crowd-BT accuracy 0.6978 vs 0.6815 plain BT on their document-ranking data; simulated gains far larger with adversarial raters [S: WSDM 2013]).
- **Trap artifacts are deterministic per scenario** (`professional.py:53-62`), so repeat raters can memorize them; and the trap is *gross* (flipped debits, 10× amount error) — it screens for attention, not for the fine judgment the arena claims to weight.

### 8.2 Recommended protocol [R]

1. **Qualification (screening, not weighting):** identity + credential verification (e.g., CPAVerify for CPAs, as the PRD already contemplates, `docs/PRD.md:94-100`) gates *access* to the expert pool and appears as a cohort label on published methodology. It sets a prior, not a multiplier.
2. **Gold-item program:** a bank of gold items per family at three subtlety levels (gross violation / material-but-plausible error / defensible-vs-best-practice), parameterized so no rater sees the same surface twice (§9 generators make this cheap). Density: ~1 gold per 4–6 judged items during a rater's first ~60 items (calibration phase), decaying to ~1 in 10 for maintenance. This reaches the ~40–60 gold observations that Sim 4 shows are needed for a stable accuracy estimate within weeks of normal participation, not years.
3. **Reliability estimation from all signals, jointly:** gold accuracy (by subtlety level), agreement with high-reliability peers on shared items (the prototype's consensus metric, `reviewer.py:75-113`, generalizes once items are versioned), intra-rater consistency on repeated items (same logical item, different surface parameters, ≥2 weeks apart), and response-time/pattern anomaly flags (Chatbot Arena's conformal anomaly detection as the template [S: PMLR 235]). Fit as Crowd-BT-style rater parameters inside the rating model; until that ships, a transparent composite reliability score with published formula.
4. **Weight = estimated reliability**, floored to zero below a threshold; credential tier never multiplies votes. Publish the reliability distribution, not individuals' scores; the rater-facing "calibration score" product surface (the genuinely good idea in the prototype) reports gold accuracy with binomial CIs and honest "insufficient data" states instead of a percentile computed over ≥3 traps (`reviewer.py:116-135`).
5. **Ongoing calibration:** drift monitoring per rater (rolling gold accuracy), gold-item refresh tied to scenario-release batches, and periodic expert-panel adjudication of contested items (the Chatbot-Arena-style expert-agreement study rerun quarterly on a sample [S]).
6. **Fairness/consequence controls:** raters must be able to see and appeal gold scoring (gold items can be wrong — WebArena Verified's lesson applies to *our* graders too [S]); gold items excluded from model ratings by construction (the prototype already does this correctly — trap outcomes never enter `votes`, `arena.py:155-163`).

**Credential tiers vs estimated competence — the direct answer [R]:** estimate competence; use credentials for pool admission and reporting cohorts. Grounding: Crowd-BT/Shejole show joint estimation works and is robust to spammers/adversaries [S]; no source supports résumé-proportional vote multipliers; and DesignPref warns that some "disagreement" is legitimate taste, so the reliability model must be fit on items with *known* answers (gold + invariant-violating items), not on raw majority agreement alone — otherwise you'd punish principled minority judgment (the pluralistic failure mode [S: arXiv:2606.02547]).

---

## 9. Synthetic-world and scenario-generation protocol

Goal: from a task-family intent (possibly a routed user prompt) produce scenarios that are **deterministic** (seeded), **valid** (accounting-true), **reproducible** (versioned), **leakage-resistant**, and **durable** (parameterized families, rotation).

1. **World schema.** A world is a content-addressed snapshot of a synthetic company: entity graph (single or multi-entity), CoA (typed accounts, normal balances), opening balances, subledgers (AR/AP/bank/fixed assets/deferred revenue), document store (invoices, statements, contracts, policy memos — rendered PDFs/CSVs/XLSX generated from the same structured facts), personnel/approval matrix, and a policy pack (capitalization threshold, materiality, rev-rec policy). Precedents: APEX worlds ("a self-contained company, frozen at a specific month-end close… its own entity type, chart of accounts, revenue model, and prior-period balances," averaging 73 input files [S: arXiv:2607.27189]); Ramp's 22 worlds [S].
2. **Invariants by construction.** The generator emits transactions, then derives statements/subledgers/documents *from* them — so double-entry balance, subledger↔GL ties, and bank-statement consistency hold by construction, and every deliberate violation is an explicit, registered perturbation. This is the single most important validity device: ground truth exists because the world was built forward from it (APEX's "trap register cataloging every seeded contradiction" [S]).
3. **Constraint-based discrepancy planting.** Each scenario = world + a perturbation set drawn from a typed catalog (timing difference, duplicate, missing entry, misclassification, transposition, cutoff error, policy breach…) with solver-checked satisfiability: the planted set must (a) be detectable from the observable artifacts, (b) have a unique or explicitly-enumerated acceptable resolution set, (c) not interact to create unintended second solutions (checked by re-running the L1/L2 graders against the oracle solution — WorkArena++'s oracle+validator pairing [S: arXiv:2407.05291]).
4. **Parameterized variants.** Every logical scenario compiles to ≥3 surface variants (names, amounts within ranges, dates, orderings, distractor documents) sharing ground-truth structure — SpreadsheetBench's multiple-test-case device, which separates robust solutions from per-instance overfitting [S: arXiv:2406.14991] — and powering: pass^k across variants, gold-item non-memorability (§8), and intra-rater repeat items.
5. **Ground-truth state & oracle.** Per scenario: machine-checkable end-state assertions, the enumerated acceptable-solution set (with policy-conditional branches: "under policy P1 treatment A; under P2 treatment B acceptable"), and an expert golden response scoring 100% on the rubric (APEX requirement [S]).
6. **Expert review.** Two-stage: author-independent expert *solves* the scenario blind (SpreadsheetBench 2's dual-review [S: arXiv:2606.29955]); discrepancies reconciled; then batch-level baselining on a sample by unexposed experts with a published defect rate (APEX: 1.1% criterion defect rate [S]). No scenario enters the rated pool unreviewed — this is precisely what separates a benchmark item from a user prompt (§10).
7. **Adversarial cases.** A standing Dynabench-style loop: routed user prompts that broke models, rater corrections, and model-failure clusters get authored into new perturbation types targeting current blind spots [S: NAACL 2021]. Include deliberately underspecified scenarios where the *correct* behavior is a clarification request (ToolSandbox Insufficient-Information [S]) and policy-conflict scenarios where the correct behavior is escalation (ST-WebAgentBench's completion-under-policy [S: arXiv:2410.06703]).
8. **Leakage resistance & versioning.** Novelty screening of all generated text/numbers against public corpora (APEX [S]); private hold-out slice never published (BizBench hidden test sets [S: ACL 2024]; APEX closed set [S]); rotation of the public-facing pool (~1/6 per release, LiveBench cadence, with rank-stability checks across rotations — theirs held >0.997 [S: arXiv:2406.19314]); frozen graders per release (Ramp [S]); scenario retirement with tombstones so every historical vote/episode stays interpretable; per-release BenchmarkCards-style documentation extended with contamination and version-diff fields [S: arXiv:2410.12974]. Roll-forward versioning — advancing a world one period to test cross-period memory without contaminating the next close — borrowed from Ramp's internal "roll-forward worlds" [S: builders.ramp.com/post/stack-benchmarking].

---

## 10. Prompt-to-benchmark routing design

The prototype's front door promises "describe the work" and then discards the description (`frontend/src/components/workspace/PromptComposer.tsx:49-52,92-94`). The honest, useful version [R]:

1. **Parse & classify.** Typed prompt → intent classifier (LLM with a constrained output schema) → {family_id candidates with confidence, extracted slots: transaction type, amounts, period, entity hints, policy hints}. The taxonomy in §5 is the label space.
2. **Three routing outcomes, always disclosed to the user:**
   - **Matched (high confidence + slot compatibility):** the session runs a *versioned scenario* from that family whose parameters are set from the user's slots where the generator supports them ("Your prompt matched: Prepaid/deferred revenue recognition — running certified scenario family F4.2, variant seeded from your amounts"). The board contribution is tagged with the scenario version, not the raw prompt. What is measured is the family, and the UI says so.
   - **Near-miss (family match, unsupported specifics):** run the nearest scenario, show the delta ("we can't yet represent multi-currency; running the single-currency variant"), and queue the delta as generator feature demand.
   - **Unmapped:** no battle on the rated boards. Offer (a) an *exhibition session* — judgments collected, clearly excluded from ratings (schema flag `exhibition=true`), or (b) "submit to the task-authoring queue," with credit/attribution. The queue feeds §9 step 7's Dynabench loop; promotion to the bank requires the full §9.6 review. Never pretend an arbitrary prompt is a validated item — the routing contract *is* the scientific claim.
3. **Routing quality is itself measured:** log classifier confidence and human-audited routing accuracy on a sample each release; publish the acceptance rate and median time-to-promotion of queued prompts (the Dynabench-style vitality metric [S: NAACL 2021]).
4. **Contamination interface:** matched sessions must not echo hidden ground truth back into the prompt-visible surface; user-entered numbers flow only into parameter slots that the generator already randomizes, so a prompt cannot reverse-engineer the discrepancy register [I].

---

## 11. Three worked task examples

All three are specified against the schemas of §7.4. Example 1 deliberately upgrades an existing prototype scenario so the delta is visible.

### 11.1 Example 1 — deterministic core: annual prepaid subscription (family 4, static mode)

Prototype ancestor: `annual-prepaid-saas` (`backend/app/scenarios.py:83-91`), which stores the expected postings but never checks outputs against them.

- **Initial world state:** Meridian Fitness LLC, calendar-year accrual-basis; CoA excerpt with Cash (1000), Deferred Revenue (2600), Subscription Revenue (4100), Sales Revenue (4000 — distractor); policy pack: revenue recognized ratably over service period; materiality $500. Variant parameters: amount ∈ {$9,600…$36,000 in $1,200 steps}, start date ∈ {1st or mid-month}, term ∈ {12, 24 months} — mid-month start makes the first-month recognition a genuine choice (half-month convention vs daily proration), moving one variant class from "uniquely correct" to "enumerated acceptable set."
- **User request (brief):** "On {date} we collected {amount} cash for a {term}-month subscription starting that day. Record the receipt and {month}'s revenue recognition, with memos."
- **Information available / intentionally missing:** available — policy pack, CoA, bank confirmation snippet. Missing — none in the base variant; in the underspecified variant the service start date is absent from the brief but present in the contract PDF (tests evidence-seeking), or absent everywhere (correct behavior: state the assumption or ask).
- **Allowed tools (static mode):** none — output is the artifact. (The same logical scenario compiles to a workbench variant where the entry must be posted to the sandbox ledger.)
- **Acceptable solution set:** Dr Cash / Cr Deferred Revenue {amount}; Dr Deferred Revenue / Cr Subscription Revenue {amount×recognized fraction}; enumerated acceptable recognition conventions for mid-month variants; crediting 4000 Sales Revenue directly = L1 policy violation (this is exactly the `wrong_account` the prototype plants, `scenarios.py:90` — promoted from a quality-tier trick to a graded check).
- **Objective invariants (L1):** each entry balances; total credited to revenue over the term = amount; period correct; accounts from CoA with legal normal balance; no revenue recognized before service start.
- **Milestones:** n/a (static, two postings).
- **Expert rubric (L2, binary criteria):** correct deferral on receipt; recognition amount matches an acceptable convention; memo states the convention/assumption; memo cites the contract; presentation posts round amounts with the schedule shown; flags the remaining deferred balance.
- **Preference dimensions (L3):** memo clarity, schedule presentation, assumption transparency.
- **Failure taxonomy:** premature full recognition; wrong revenue account; unbalanced; wrong fraction (off-by-one month); no memo; fabricated policy citation.
- **Public in arena:** blinded artifacts, family-level ratings, aggregate criterion pass rates. **Private:** ground-truth register, gold-variant keys, per-rater data, raw corrections. **Licensable:** episode artifacts + L1/L2 grades (outcome supervision); corrections; L3 preferences with reliability metadata (consented tier only).

### 11.2 Example 2 — interactive core: multi-source bank reconciliation (family 3, workbench mode; Phase 2 = recorded trajectories)

- **Initial world state:** Harbor Deli Group, one operating bank account; sandbox ledger (QuickBooks-shaped API) with November cash activity; artifacts: bank statement PDF (47 lines), POS settlement CSV (daily batches, fees netted), delivery-platform payout report PDF, AP payment run listing XLSX, policy memo ("fees recorded gross to 6220 Processing Fees; clearing account 1050 must be zero at close"). Perturbation register (planted, solver-checked): 1 duplicate ledger entry, 2 timing differences (deposits in transit), 1 platform fee netted incorrectly, 1 bank service charge unrecorded, 1 transposition ($1,290 vs $1,920). Modeled directly on the Ramp sample task shape ("bring the clearing account to zero, and propose a separate entry for every discrepancy" [S: labs.ramp.com]).
- **User request:** "Reconcile the operating account for November, bring 1050 to zero, propose adjusting entries for every discrepancy with support, and produce the reconciliation schedule."
- **Available / missing:** all artifacts available; the platform's fee-schedule page is *not* provided — the correct gross-up rate must be derived from the payout report itself (tests investigation, not recall).
- **Allowed tools:** ledger read/write API (post/void/query), spreadsheet tool, PDF/CSV readers, calculator/code execution; **prohibited (minefields):** deleting historical transactions, posting to retained earnings, altering the bank statement artifact.
- **Objective invariants (L1):** end-state: account 1050 = 0; adjusted book balance = bank balance ± enumerated timing items; every adjusting entry balances and is posted to the correct period; no minefield violations; ledger↔subledger tie preserved.
- **Milestones (DAG, ToolSandbox-style [S]):** M1 imported/inspected all four sources → M2 identified duplicate → M3 identified both timing differences (parallel) → M4 fee gross-up computed correctly → M5 service charge recorded → M6 transposition found → M7 schedule produced with item-level references. Score = DAG-matched milestone completion; minefield violation nullifies (ToolSandbox's score = M⁺ × 1{M⁻=0} [S]).
- **Expert rubric (L2):** each discrepancy resolved with the *right explanation* (not just a plug); support cited per adjustment; schedule reviewable by a third party; unresolved items explicitly listed rather than forced to zero; materiality-appropriate treatment of a $3 rounding residue.
- **Preference dimensions (L3, on recorded episodes that pass L1):** investigation efficiency (unnecessary-action count is L4, but *reviewability of the path* is judgment), quality of the proposed entries' memos, schedule presentation.
- **Failure taxonomy:** plug to force zero (the cardinal sin — an L1-passing balance with an L2/L1-policy fail via the "no unexplained plug" invariant); duplicate missed; fee netting kept; period error; minefield violations; loop/timeout (L4).
- **Repeated-run protocol:** k=4 runs per config per variant (Ramp uses 3, APEX 8 [S]; 4 balances cost against Sim-3's separation power), pass^k and criterion-variance reported.
- **Public:** family board (preference + mean criteria + pass^k + cost). **Private:** perturbation register, world snapshots, trajectories. **Licensable:** trajectories with state diffs + expert side-effect labels (process supervision, the AgentRewardBench-shaped asset [S]); end-state grades (outcome supervision).

### 11.3 Example 3 — judgment-heavy: year-end bonus accrual estimate + memo (family 4/10 boundary, static mode with rich context)

- **Initial world state:** Caldera Systems Inc., Dec 31 close; artifacts: bonus plan document (pool = 8% of EBITDA over a $2.0M threshold, board discretion ±20%, pro-rata for mid-year hires), preliminary P&L (EBITDA $3.1M, one pending revenue item of $150K flagged uncertain), headcount roster with hire dates, prior-year accrual workpaper (prior board exercised −10% discretion), policy pack (materiality $25K; accruals require documented methodology).
- **User request:** "Propose the year-end bonus accrual with a supporting memo a reviewer could sign off on."
- **Available / missing:** everything above; deliberately missing — any indication of *this* year's board intent (the professional move is to state the discretion assumption and flag it, or recommend inquiry; asserting a discretionary cut as fact is a documentation failure).
- **Allowed tools:** none required; spreadsheet optional.
- **Acceptable solution set (a *range*, not a point):** accrual computed on EBITDA ∈ [$2.95M, $3.1M] (pending item excluded or included with disclosure) × discretion ∈ [no adjustment, disclosed assumption]; pro-rata correctly applied. Any documented, internally-consistent figure in the induced range passes; the *estimate itself is L2, not L1*.
- **Objective invariants (L1):** entry balances; posted to correct accounts/period; arithmetic from stated assumptions is correct; no recognition of the pending revenue without disclosure; figure within the outer defensible range (a wide gate — outside it is not judgment, it's error).
- **Expert rubric (L2):** methodology documented and reproducible; pending-item treatment disclosed; discretion assumption explicit; sensitivity shown (range or table); comparison to prior year; materiality framing; appropriate escalation/inquiry recommendation.
- **Preference dimensions (L3):** which acceptable memo would you file? (conservatism, clarity, sensitivity presentation, reviewer-readiness). This is the family where DesignPref-style legitimate disagreement is most expected — L3 data here is tagged for pluralistic analysis by rater role [S: arXiv:2511.20513; arXiv:2606.02547].
- **Failure taxonomy:** point estimate asserted with no assumptions; pending revenue silently included; pro-rata ignored; arithmetic error; memo unfalsifiable ("management believes the accrual is reasonable").
- **Public / private / licensable:** as 11.1; corrections here (experts rewriting memo paragraphs) are the highest-value licensable unit — judgment-task demonstrations barely exist in public corpora [I].

---

## 12. Statistical analysis plan

All simulation numbers below are from Appendix A (`sims.py`, seeded, reproducible); the generative assumptions are stated with each result. These are design-guidance simulations, not measurements of real evaluator behavior — the §13 study replaces assumptions with estimates.

### 12.1 Dependence structure — what the votes actually are

A session yields multiple judgments sharing: rater (persistent perception effects), scenario (task-model interaction: model m is idiosyncratically good/bad at scenario s), battle (same sitting, sequential context), and — in the current bracket — *outcome-dependent pairing* (finalists are semifinal winners, `backend/app/services/arena.py:198-203`). Model-side, repeated runs of a stochastic agent on one scenario share a run cluster. Any inference that treats votes as i.i.d. ignores all of this.

**Simulation 1 (CI coverage).** World: 8 configs with true Elo spread ≈ 0–243; 40 raters × 25 bracket sessions (4,000 votes); rater effects u ~ N(0, 0.5²) per (rater, model) and scenario effects b ~ N(0, 0.5²) per (model, scenario) on the log-strength scale; prototype-mirroring BT fit (MM + virtual-split smoothing, `ratings.py:59-64`) and three bootstraps (200 resamples):

| Condition | Naive i.i.d. vote bootstrap (the prototype's method) | Battle-cluster | Rater-cluster |
|---|---|---|---|
| No clustering, 1000 scenarios | 93.6% coverage | 94.0% | 91.5% |
| Rater+scenario effects, 1000 scenarios | **59.4%** | 58.0% | 75.8% |
| Rater+scenario effects, **5 scenarios** | **45.1%** | 44.2% | 58.2% |

Reading: (a) the prototype's bootstrap is fine only in the world where its assumptions hold; (b) rater-clustering recovers part of the loss; (c) with a small scenario library **no resampling fixes it**, because the scenario draw shifts the estimand itself — with S scenarios the per-model bias has sd ≈ σ_task/√S (≈ 39 Elo at σ=0.5, S=5), which is invisible to any within-sample method. Consequence [R]: cluster the bootstrap two ways (resample raters; resample scenarios) and take the union/max interval as the honest default; grow S before growing votes; and treat per-family boards with S < ~20 as "provisional" regardless of vote count.

**Simulation 2 (power / votes needed).** Head-to-head analytic (α=.05 two-sided, power .80): detecting P(win)=0.55 (≈35 Elo) needs ~783 votes on that pair; 0.60 (≈70 Elo) ~194; 0.65 ~85; 0.75 ~29. Arena-style (8 configs, bracket sampling, BT pooling), P(top model correctly ranked #1):

| Condition | 200 votes | 1,000 | 2,000 | 8,000 |
|---|---|---|---|---|
| 35-Elo top gap, no rater/task noise | 63% | 87% | 97% | 100% |
| 35-Elo gap, rater+task effects, 5 scenarios | 41% | 56% | 65% | **64% (plateau)** |
| 70-Elo gap, no noise | 78% | 99% | 100% | 100% |
| 70-Elo gap, rater+task effects, 5 scenarios | 55% | 77% | 83% | 86% (plateau) |

The plateau is the §12.1 scenario-lottery bias made visible: after ~2,000 votes, additional votes buy nothing; additional *scenarios* do. This kills any fixed "minimum vote threshold" copied from other arenas: the threshold must be stated as (votes AND scenarios AND raters) per family, derived by rerunning this simulation with the variance components estimated in §13. Until then, an interim publishable bar per family board [R]: ≥20 scenarios, ≥30 raters contributing, ≥1,500 counted judgments, and bootstrap rank-set stability across the two clustered resamplings.

**Simulation 3 (pass^k and heterogeneity).** Three agents with identical pass@1 = 0.80: deterministic-mixture (solves 80% of tasks always), i.i.d.-noisy (0.8 per trial), Beta(4,1)-heterogeneous. pass^8 = 0.80 vs 0.17 vs 0.33. Repeated runs are not a nicety; they are the only way to separate "knows 80% of the work" from "gambles on all of it" — the distinction practitioners care about most (τ-bench introduced pass^k for exactly this [S: arXiv:2406.12045]; APEX's Pass^8 ≤ 2.6% shows where frontier models actually sit [S]). Protocol [R]: k=4 runs minimum on interactive families (k=8 where budget allows), estimated unbiasedly via the (c choose k)/(n choose k) U-statistic, reported per family with task-level bootstrap.

**Simulation 4 (rater gold items)** — reported in §8.1.

### 12.2 The estimator stack [R]

1. **Per-family BT-with-ties (Rao-Kupper)** on L1-passing L3 judgments, rater-reliability-weighted, presentation covariates available for a style-controlled variant (LMArena's additive-covariate BT [S]). Fit by MLE; the prototype's MM fitter generalizes or use standard optimization.
2. **Uncertainty:** two-way clustered bootstrap (raters; scenarios) with ≥1,000 resamples (the prototype's 40 rounds with its percentile indexing, `ratings.py:117-127`, is under-resolved for a 95% interval even under i.i.d.); report simultaneous rank sets (Chatbot Arena method [S]). Where a parametric route is preferred later: mixed-effects logistic (lme4-style) with crossed random effects for rater and scenario, sandwich covariance clustered at the rater level as the robustness check (Chatbot Arena's sandwich precedent [S]).
3. **Agreement/reliability reporting:** Krippendorff's α per family for L3 (the DesignPref comparison point of 0.25 [S] gives an external anchor); Fleiss' κ for L2 criterion grades (APEX anchor: 0.857 [S]); test–retest for repeated raters; all published on the methodology page.
4. **Multiplicity:** pairwise config differences per board controlled with Benjamini–Hochberg at 5% FDR (APEX precedent [S]); movement claims ("model X overtook Y") only when rank sets separate.
5. **Ties/both-bad analysis:** tie rates monitored per family as a *difficulty/indistinguishability* metric; both-unacceptable rates feed the scenario-difficulty and model-floor dashboards; forced-choice bias is measured directly in the §13 study by A/B-ing the response formats. Intransitivity: with K-wise data, per-session transitivity holds by construction of a ranking; across sessions, cyclic aggregate preferences are detectable (and expected under heterogeneity — Pluralistic Leaderboards' committee view is the fallback if cycles are common [S]).
6. **Position/order effects:** position randomized (the prototype already shuffles, `arena.py:75-99`) *and logged* (`position_permutation` in the judgment schema) so position effects are estimable, not just averaged; the same discipline applies to any LLM pre-grader (A/B swap, per Plan-RewardBench protocol and the position-bias literature [S: arXiv:2604.08178; ACL 2025.ijcnlp-long.18]).

---

## 13. Minimum viable validation study and estimated evaluator burden

**Purpose:** replace this report's simulation assumptions with measured quantities *before* any public leaderboard. Five questions: (V1) Can qualified raters reliably rank gate-passing accounting artifacts? (V2) How much of preference is explained by rubric criteria vs residual taste? (V3) Do raters detect planted L1/L2 defects, and at what subtlety? (V4) Is static preference predictive of environment outcomes? (V5) What are the variance components (rater, scenario, both) that the §12 power analysis needs?

**Design [R]:**
- **Materials:** 3 task families (11.1 journal-entry class; 11.3 accrual-memo class; 11.2 reconciliation — as recorded trajectories/end-state packets from the Phase-2 sandbox). 8 scenarios per family × 3 surface variants. 5 configs (4 real model configs on the reference scaffold + 1 expert-authored golden response as a hidden ceiling probe). Episodes pre-generated; k=4 runs for the reconciliation family.
- **Raters:** 24 verified professionals (target mix: 12 controllers/accounting managers, 8 senior accountants, 4 auditors), recruited per the PRD's channel list (`docs/PRD.md:116-121`), paid.
- **Assignment:** each scenario-variant judged by 3 raters (triads enable α/κ and majority baselines); each rater: ~30 judgment items + 8 gold items (3 subtlety levels) + 4 repeat items (same logical scenario, different surface, ≥1 week later). Response format A/B: half the sessions K-wise ranking with ties, half pairwise with the full §7.2 response set — measuring forced-choice bias and format efficiency directly.
- **Measures:** Krippendorff's α (V1, per family); regression of L3 preference on L2 criterion vectors (V2 — the residual is the "taste" share); detection ROC by subtlety level (V3); Spearman correlation of family-level static-preference ratings vs environment mean-criteria/pass^k orderings for the same configs (V4 — n=5 configs is a directional check only, widen later); variance decomposition via the mixed-effects fit (V5).
- **Decision rules (pre-registered):** publish a family board only if α ≥ 0.4 among gate-passing comparisons *or* disagreement is shown to be structured by rater role (pluralistic case) rather than noise; if gross-defect detection < 90%, raise the gate (more programmatic checks, less reliance on raters noticing); if V2 shows criteria explain >~80% of preference variance, rubric-first UX (preference demoted to tie-breaker); if V4 correlation is low, stop describing static boards as agent-capability measures anywhere in the product.

**Burden and cost estimate [I — arithmetic, assumptions shown]:** per rater: ~42 items. Static items ~4 min (prototype design target 2–5 min [S: `categories.py:5-6`], plus criterion clicks); reconciliation-packet items ~10 min (reading a trajectory summary + end-state diff; AgentRewardBench-style review [S]). Mix ≈ 30×4 + 12×10 = 240 min ≈ **4 hours/rater**, ~96 expert-hours total. At $100–150/hr (senior CPA freelance range — assumption, verify at recruitment): **$10–15K in rater cost** plus generation compute (5 configs × 96 episodes × k: at Ramp-observed $0.85–$4.30/run [S], $500–$2,500). Elapsed: 3–4 weeks including the repeat-item gap. Deliverable: a public methodology note with all five measurements — which is itself the product's first credibility artifact.

---

## 14. Ninety-day research and product roadmap

**Weeks 0–2 — stop the bleeding, keep the shell.**
- Freeze public claims: label the current board "simulated demonstration data" (it is: §15 items 8–9) and remove/annotate the fabricated stats band (`frontend/src/components/about/StatBand.tsx:3-7`).
- Schema v1: add judgment-response options, confidence, rationale, correction, provenance/version fields (§7.4) — additive tables, no behavior change yet.
- Scenario generator v0 for family 4 (journal entries) with invariants + parameterized variants (§9 steps 1–5), replacing the 3 hard-coded scenarios.

**Weeks 2–6 — Phase 1 arena (A′).**
- L1 gate service + rubric grading for families 4 and 10; K-wise session UI with ties/acceptability; honest prompt routing v0 (§10 outcomes disclosed).
- Gold-item program v1 (3 subtlety levels, parameterized); reliability score v0 (gold + agreement composite, published formula); retire fixed tier multipliers from the fit.
- Ratings v2: BT-with-ties, two-way clustered bootstrap, per-family boards, provisional-status rules (§12.2). Live-model generation smoke-tested (`providers/live.py` is written but "unexercised against real endpoints" [S: `docs/ARCHITECTURE.md:137`]).

**Weeks 6–10 — Phase 2 sandbox + validation study.**
- Reconciliation world v1 (11.2): ledger sandbox, artifact renderer, perturbation catalog v1, milestone/minefield grader; agents run offline, k=4.
- Recorded-trajectory review UI (end-state diff + step list + side-effect flags).
- **Run the §13 validation study** (recruit weeks 4–6; field weeks 6–9; analyze week 10).

**Weeks 10–13 — decide and publish.**
- Publish the methodology note with study results; apply the pre-registered decision rules (§13) to choose the Phase-3 emphasis (preference-led vs rubric-led; which families go live).
- First versioned public release: scenario batch v1.0 with BenchmarkCards-style documentation + frozen graders; private hold-out slice reserved (§9.8).
- Design-partner loop: one vendor evaluation dry-run on the reconciliation family (the PRD's ICP-1 motion, `docs/PRD.md:103-110`) under the §7 config-versioning rules.

Explicitly deferred beyond 90 days: live user-in-the-loop workbench episodes; user-simulator-driven multi-turn tasks (τ²-bench shows simulator effects are large [S: arXiv:2506.07982]); paid-panel marketplace mechanics; training-data licensing sales (until consent tiers + the validation note exist).

---

## 15. Prototype gap analysis

Every claim below was verified by reading the file at the cited lines (tree `d478e45`). Structured as: finding → evidence → disposition (keep / revise / replace).

1. **The "five comparisons" are four model votes + one rater trap, all on one scenario, not five turns of anything.** `backend/app/services/arena.py:22` (`ROUNDS`), `:101-106` (match creation), `:155-163` (trap → `trap_results`), `:192-206` (final/third derived from semi outcomes). *Disposition:* replace the bracket with one K-wise graded judgment per scenario (§7.2); keep the blinding, shuffling, and server-side ordering enforcement (`:137-141`), which are sound.
2. **The typed prompt does not affect task creation.** POST body is `{category, scenario_id}` only (`frontend/src/components/workspace/PromptComposer.tsx:49-52`); typing clears the selected scenario (`:92-94`), so free text yields a *random* prebuilt scenario (`backend/app/routers/battles.py:99` → `backend/app/scenarios.py:164`); the stored `battle.prompt` is the scenario brief, not the user's text (`arena.py:52,57`). The attachment buttons are inert ("coming later", `PromptComposer.tsx:9-13`). *Disposition:* replace with disclosed routing (§10).
3. **No tie / equivalent / both-acceptable / both-unacceptable / insufficient-information options; no confidence, rationale, or correction.** `VoteIn = {match_id, winner_generation_id}` (`backend/app/schemas.py:160-162`); server enforces winner ∈ {A,B} (`arena.py:140-141`); UI renders exactly two buttons (`frontend/src/pages/JudgeSession.tsx:200-216`). *Disposition:* replace per §7.2; the ties literature says the omission biases exactly the close matchups a leaderboard exists to resolve [S: arXiv:2410.05328].
4. **Objective checks and preference are not separated — there is no L1 gate.** Scenarios *store* ground truth (expected postings `scenarios.py:86-91`, mapping keys `:120-131`) but nothing evaluates outputs against it; deliberately-degraded outputs (wrong-account bookings at low quality tiers, `professional.py:256-260`) flow into the same vote stream as sound ones. *Disposition:* build the gate (§7.1); the stored ground truth shows the authors already knew it was needed.
5. **No trajectories, intermediate states, rationales, or corrections are stored.** `Generation` holds final HTML + a latency int (`backend/app/models.py:93-108`); latency is fabricated in sample mode (`professional.py:51,62` — `rng.randint(1400, 4600)`); no tool-call or state tables exist (full `models.py` read). *Disposition:* additive schema per §7.4; stop displaying fabricated latency anywhere user-visible.
6. **Fixed credential weights and the trap regime lack empirical justification.** Weights {0, 0.25, 1.0, 1.5, 2.0} (`arena.py:24-26`), tier from email domain (`backend/app/services/reviewer.py:18-34`), "Calibrated" badge at ≥80% traps (`reviewer.py:56-58`), percentile over ≥3 traps (`:116-135`); PRD defers reliability weighting (`docs/PRD.md:123-128`). Sim 4: 5 traps mislabel a 60%-accurate rater 33.7% of the time; deterministic trap artifacts are memorizable (`professional.py:53-62`). *Disposition:* replace with §8 (estimated reliability; credential = admission).
7. **The BT fit and bootstrap ignore clustering.** Individual-vote i.i.d. resampling (`backend/app/services/ratings.py:114-120`), 40 rounds (`backend/app/config.py:49`) with coarse percentile indexing (`ratings.py:126-127`); no rater/battle/scenario clustering anywhere. Sim 1: nominal-95% coverage 45–59% under realistic dependence. *Disposition:* replace per §12.2; the MM fitter itself (`:38-86`) is correct for what it does and can stay as the point estimator.
8. **Published boards are seeded fiction that the sample mode then "confirms."** ~500 synthetic votes/category with default weight 1.0 and `counted=True` (`backend/pipeline/seed.py:105-132`; `models.py:146-151`) pass the snapshot filter (`backend/app/services/leaderboard.py:23-27`, whose comment concedes it: "plus the flagged synthetic bootstrap"); the offline generator's QUALITY tiers (`professional.py:24-33`) mirror the same seed strengths (`seed.py:33-48`), so in sample mode human votes largely recover a hard-coded ordering. Fictional vendor products and "declined" empty-chair rows ship on the board (`seed.py:53-68`). *Disposition:* demo-label or age out synthetic votes before any public claim; never let `synthetic=True` rows into a published fit.
9. **Marketing numbers are fabricated.** "94% Panel accuracy…", "1,240 Calibration checks…", "Top 18%" are hard-coded UI strings (`frontend/src/components/about/StatBand.tsx:3-7`). *Disposition:* remove until the §13 study produces real ones.
10. **What can stand as the MVP interface:** the blinded side-by-side document viewer with sandboxed iframes and CSP (`frontend/src/pages/JudgeSession.tsx:58-64`; `backend/app/routers/battles.py:144-163`), server-side identity concealment until completion (`battles.py:45-85`), server-side decision timing (`arena.py:121-128`) and the behavioral floor (`:176-178`), the snapshot-based leaderboard pipeline (`backend/app/services/leaderboard.py`), guest-then-verify flow, and the synthetic-scenario stance (`scenarios.py:1-8`). These are good bones; everything measured through them changes.

---

## 16. Risks, unresolved questions, and falsifiable hypotheses

**Risks (consequential-validity first):**
- **Leaderboard incentive distortion:** optimizing for expert preference could reward confident, polished presentation over flagged uncertainty — the professionally *wrong* gradient (accounting rewards disclosed doubt). Mitigations: L1/L2 gates, style-controlled boards, rubric criteria that pay for disclosed assumptions (11.3). Residual risk real; monitor via the style-coefficient dashboard [I; mechanism evidenced by LMArena style effects [S]].
- **Judge/grader capture:** LLM graders drift or get gamed; Plan-RewardBench shows judge accuracy collapsing on long trajectories [S: arXiv:2604.08178]. Mitigation: human-validated judges per release (APEX protocol [S]), deterministic checks wherever possible (LiveBench/WebArena-Verified stance [S]).
- **Gaming by vendors:** private-variant shopping and selective submission (Leaderboard Illusion patterns [S: arXiv:2504.20879]). Mitigation: versioned-config policy, submission logs, retraction rules published in advance.
- **Rater-market failure:** too few calibrated raters → boards go stale or one clique's taste dominates; pluralistic reporting and recruitment cadence are product problems as much as statistical ones.
- **Contamination decay:** any published scenario leaks into training corpora eventually; rotation + private hold-out is maintenance, not a one-time fix (SWE-bench's measured decay is the cautionary example [S: arXiv:2410.06992]).
- **Positioning risk (business):** the rubric-benchmark layer is being commoditized by the very vendors on the roster (Ramp/Mercor). The defensible asset is the calibrated human panel + preference/correction data; if the §13 study shows weak preference reliability, that asset thesis needs revision — surface this to investors *before* they ask [I].

**Unresolved questions:** deployed tie encoding in the rating fit (Rao-Kupper θ estimated per family vs fixed); whether K-wise sessions are tolerable for long documents (K-Sort's economics assumed images [S]); the right materiality for L1 amount tolerances per family; whether user-simulated requesters are ever reliable enough for multi-turn accounting tasks (τ² says treat with suspicion [S]); legal shape of correction-data licensing.

**Falsifiable hypotheses (each tied to a §13/§14 measurement):**
- **H1:** Among gate-passing outputs, verified professionals' L3 judgments have Krippendorff's α ≥ 0.4 within task family (vs DesignPref's 0.25 for designers). If false → pluralistic/rubric-led product.
- **H2:** Family-level static preference ratings correlate ρ ≥ 0.7 with environment-mode mean-criteria orderings of the same configs. If false → static boards must drop capability language.
- **H3:** Estimated rater reliability (gold+agreement) predicts held-out gold accuracy better than credential tier does (ΔAUC > 0). If false → tiers were fine and §8 is over-engineered.
- **H4:** Frontier configs show pass^4 at least 15 points below pass@1 on the reconciliation family (consistency gap exists in accounting as in τ-bench/APEX). If false → repeated-run budgets can shrink.
- **H5:** A style-covariate BT fit on arena votes shows a positive, significant length/polish coefficient. If false → presentation-bias mitigations can be lighter.
- **H6:** ≥30% of L1-failing outputs are *preferred* by at least one rater when shown ungated (measures the cost of preference-first design). If false — i.e., raters catch nearly everything — the gate's role is efficiency, not validity.

---

## 17. Bibliography

Status codes: **[PR]** peer-reviewed; **[PP]** preprint; **[CT]** company technical report or official methodology page; **[PV]** partially verified (access caveat given). All URLs fetched 2026-09-04 unless noted.

### 17.1 Arenas, preference, and rater modeling

1. Chiang, Zheng, Sheng, Angelopoulos, Li, Li, Zhu, Zhang, Jordan, Gonzalez, Stoica. *Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference.* ICML 2024, PMLR 235:8359–8388. https://proceedings.mlr.press/v235/chiang24b.html **[PR]** (full PDF fetched and text-extracted).
2. Li, Liu, Fu, Li, Gu, Keutzer, Dong. *K-Sort Arena: Efficient and Reliable Benchmarking for Generative Models via K-wise Human Preferences.* CVPR 2025. arXiv: https://arxiv.org/abs/2408.14468 **[PR, PV]** — verified via arXiv v2; the CVF openaccess page (https://openaccess.thecvf.com/content/CVPR2025/html/Li_K-Sort_Arena_Efficient_and_Reliable_Benchmarking_for_Generative_Models_via_CVPR_2025_paper.html) returned HTTP 403 at fetch time.
3. Christiano, Leike, Brown, Martic, Legg, Amodei. *Deep Reinforcement Learning from Human Preferences.* NeurIPS 2017. https://papers.nips.cc/paper_files/paper/2017/hash/d5e2c0adad503c91f91df240d0cd4e49-Abstract.html ; arXiv: https://arxiv.org/abs/1706.03741 **[PR]**.
4. Knox, Hatgis-Kessell, Booth, Niekum, Stone, Allievi. *Models of Human Preference for Learning Reward Functions.* arXiv: https://arxiv.org/abs/2206.02231 **[PP; TMLR 2023 per secondary confirmation — venue not verified on a fetched TMLR page]**.
5. Liu, Ge, Zhu. *Reward Learning From Preference With Ties.* arXiv: https://arxiv.org/abs/2410.05328 **[PP]**. (Uses the Rao-Kupper generalized BT model; the project brief's mention of Davidson does not match the fetched paper.)
6. Chen, Bennett, Collins-Thompson, Horvitz. *Pairwise Ranking Aggregation in a Crowdsourced Setting* (Crowd-BT). WSDM 2013. https://www.cs.cmu.edu/~pbennett/papers/wsdm2013-preference-chen-et-al.pdf **[PR]** (PDF fetched and text-extracted).
7. Shejole, Agarwal, Agarwal, Ghosh. *Finding the Signal in the Spam: Jointly Learning Rewards and Worker Reliability from Pairwise Comparisons.* UAI 2026, PMLR 337:6204–6231. https://proceedings.mlr.press/v337/shejole26a.html **[PR, PV — landing page verified; full PDF not text-extracted]**.
8. Peng, Bigham, Wu. *DesignPref: Capturing Personal Preferences in Visual Design Generation.* arXiv: https://arxiv.org/abs/2511.20513 **[PP]**.
9. Haghtalab, Procaccia, Shao, Wang, Yang. *Pluralistic Leaderboards.* arXiv: https://arxiv.org/abs/2606.02547 **[PP]**.
10. Shi, Ma, Liang, Diao, Ma, Vosoughi. *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge.* IJCNLP-AACL 2025, pp. 292–314. https://aclanthology.org/2025.ijcnlp-long.18/ **[PR, PV — landing page/abstract verified; PDF body not extracted]**.
11. Singh et al. *The Leaderboard Illusion.* arXiv: https://arxiv.org/abs/2504.20879 **[PP — abstract-level claims verified]**.
12. Liu et al. *am-ELO: A Stable Framework for Arena-based LLM Evaluation.* arXiv: https://arxiv.org/abs/2505.03475 **[PP; "ICML 2025" per page comment, venue page not fetched]**.
13. LMArena/LMSYS. *Does style matter? Disentangling style and substance in Chatbot Arena.* https://lmsys.org/blog/2024-08-28-style-control/ **[CT]**.
14. LMArena. *Sentiment Control.* https://arena.ai/blog/sentiment-control/ **[CT]** (two specific regression coefficients cited nowhere in this report because they were only search-snippet-sourced).
15. Design Arena. *About / methodology.* https://www.designarena.ai/about **[CT]**.

### 17.2 Agents, trajectories, benchmarks

16. Yao, Shinn, Razavi, Narasimhan. *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains.* arXiv: https://arxiv.org/abs/2406.12045 **[PP; later-venue claim not verified on fetched pages]**.
17. Barres, Dong, Ray, Si, Narasimhan. *τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment.* arXiv: https://arxiv.org/abs/2506.07982 **[PP]**.
18. Lu, Holleis, Zhang, et al. (Apple). *ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark for LLM Tool Use Capabilities.* Findings of NAACL 2025, pp. 1160–1183. https://aclanthology.org/2025.findings-naacl.65/ ; arXiv: https://arxiv.org/abs/2408.04682 **[PR]**.
19. Lù et al. *AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories.* arXiv: https://arxiv.org/abs/2504.08942 **[PP; COLM 2025 per project brief — not verified on fetched pages]**.
20. Boisvert, Thakkar, Gasse, Caccia, Drouin et al. *WorkArena++: Towards Compositional Planning and Reasoning-based Common Knowledge Work Tasks.* arXiv: https://arxiv.org/abs/2407.05291 **[PP; NeurIPS 2024 D&B per listings — venue not on fetched page]**.
21. Zhou, Xu, Zhu, et al. *WebArena: A Realistic Web Environment for Building Autonomous Agents.* arXiv: https://arxiv.org/abs/2307.13854 **[PP; ICLR 2024 per listings — venue not on fetched page]**.
22. El hattami, Thakkar, Chapados, Pal (ServiceNow). *WebArena Verified: Reliable Evaluation for Web Agents.* NeurIPS 2025 Workshop on Scaling Environments for Agents. Verified via https://neurips.cc/virtual/2025/124576 , https://github.com/ServiceNow/webarena-verified , https://servicenow.github.io/webarena-verified/ **[PV — the supplied OpenReview PDF (https://openreview.net/pdf?id=94tlGxmqkN) and alternates were blocked by OpenReview's verification wall; per-checker task counts were seen only in a search rendering and are not cited in this report]**.
23. Wang, Hu, Yang, Pan, Li, Guo. *Aligning Agents via Planning: A Benchmark for Trajectory-Level Reward Modeling* (introduces Plan-RewardBench). arXiv: https://arxiv.org/abs/2604.08178 **[PP]**.
24. Levy, Wiesel, Marreed, Oved, Yaeli, Mashkif, Shlomov (IBM). *ST-WebAgentBench: A Benchmark for Evaluating Safety and Trustworthiness in Web Agents.* arXiv: https://arxiv.org/abs/2410.06703 **[PP; "ICLR 2026" per page]**.
25. Chae et al. *Web-Shepherd: Advancing PRMs for Reinforcing Web Agents.* arXiv: https://arxiv.org/abs/2505.15277 **[PP; "NeurIPS 2025 Spotlight" per page]**.
26. Xi et al. *AgentPRM: Process Reward Models for LLM Agents via Step-Wise Promise and Progress.* arXiv: https://arxiv.org/abs/2511.08325 **[PP]**.
27. OpenAI. *Introducing SWE-bench Verified.* https://openai.com/index/introducing-swe-bench-verified/ **[CT, PV — canonical page returned 403; specifics mirror-verified via swebench.com, the HF dataset card (princeton-nlp/SWE-bench_Verified), and a full-text mirror; treat exact quotes as mirror-verified]**.

### 17.3 Accounting, finance, spreadsheets, benchmark construction

28. Benchek, Bennett, Kern, Stevens, Sultan, Ching, Popiel, Mittal, Mercier, Foody, Vidgen. *APEX-Accounting.* arXiv: https://arxiv.org/abs/2607.27189 **[CT/PP — Mercor + Ramp technical report; abs + HTML v2 fetched]**.
29. Ramp Labs. *Ramp Accounting: A Frontier Benchmark for Accounting Tasks.* https://labs.ramp.com/ramp-accounting-bench **[CT, PV — client-rendered SPA; all quotes extracted verbatim from the page's JS bundle (`RampAccountingBench-J8jNceDl.js`); CI-interval computation method not stated on the page]**.
30. Ramp Builders. *Stack Benchmarking.* https://builders.ramp.com/post/stack-benchmarking **[CT]**; *Financial benchmarks.* https://builders.ramp.com/post/financial-benchmarks **[CT]**.
31. Ma, Zhang, Zhang, et al. *SpreadsheetBench: Towards Challenging Real World Spreadsheet Manipulation.* NeurIPS 2024 (Spotlight per page). arXiv: https://arxiv.org/abs/2406.14991 **[PR]**.
32. Zhu, Zhang, Ma, et al. *SpreadsheetBench 2: Evaluating Agents on End-to-End Business Spreadsheet Workflows.* arXiv: https://arxiv.org/abs/2606.29955 **[PP]**.
33. Chen et al. *FinQA: A Dataset of Numerical Reasoning over Financial Data.* EMNLP 2021. https://aclanthology.org/2021.emnlp-main.300/ **[PR — abstract verified on Anthology; details via the ar5iv rendering of arXiv:2109.00122]**.
34. Chen, Li, Smiley, Ma, Shah, Wang. *ConvFinQA.* EMNLP 2022. arXiv: https://arxiv.org/abs/2210.03849 **[PR]**.
35. Krumdick, Koncel-Kedziorski, Lai, Reddy, Lovering, Tanner. *BizBench: A Quantitative Reasoning Benchmark for Business and Finance.* ACL 2024. https://aclanthology.org/2024.acl-long.452/ **[PR]**.
36. Islam, Kannappan, Kiela, Qian, Scherrer, Vidgen. *FinanceBench.* arXiv: https://arxiv.org/abs/2311.11944 **[PP]**.
37. Bommarito, Bommarito, Katz, Katz. *GPT as Knowledge Worker: A Zero-Shot Evaluation of (AI)CPA Capabilities.* arXiv: https://arxiv.org/abs/2301.04408 **[PP]**.
38. Liang, Bommasani, Lee, et al. *Holistic Evaluation of Language Models (HELM).* arXiv: https://arxiv.org/abs/2211.09110 **[PP; TMLR status not verified]**.
39. Kiela et al. *Dynabench: Rethinking Benchmarking in NLP.* NAACL 2021. https://aclanthology.org/2021.naacl-main.324/ **[PR]**.
40. White, Dooley, Roberts, et al. *LiveBench: A Challenging, Contamination-Limited LLM Benchmark.* arXiv: https://arxiv.org/abs/2406.19314 **[PP; "ICLR 2025 Spotlight" per page]**.
41. Sokol, Daly, Hind, Piorkowski, Zhang, Moniz, Chawla. *BenchmarkCards: Standardized Documentation for Large Language Model Benchmarks.* arXiv: https://arxiv.org/abs/2410.12974 **[PP]**.
42. Aleithan, Xue, Mohajer, Nnorom, Uddin, Wang. *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv: https://arxiv.org/abs/2410.06992 **[PP]**.
43. Prathifkumar, Mathews, Nagappan. *Does SWE-Bench-Verified Test Agent Ability or Model Memory?* arXiv: https://arxiv.org/abs/2512.10218 **[PP]**.

### 17.4 Vendor documentation used for the task taxonomy (fetched 2026-09-04)

Rillet: https://www.rillet.com/ , https://www.rillet.com/product/aura-ai · Campfire: https://campfire.ai/ · Basis: https://www.getbasis.ai/ (+ /solutions/cas-and-advisory, /solutions/tax, /solutions/audit, /solutions/corporate-accounting; note basis.so returned 403; usebasis.co redirects to basis.inc) · Numeric: https://www.numeric.io/ · Puzzle: https://puzzle.io/ · Digits: https://digits.com/ , https://digits.com/agl/ · Pilot: https://pilot.com/ , https://pilot.com/platform/ai-accountant (Meridian identified by URL only) · Intuit: https://www.intuit.com/intuitassist/ , https://investors.intuit.com/news-events/press-releases/detail/1258/intuit-introduces-ground-breaking-virtual-team-of-ai-agents-to-fuel-growth-for-businesses , QBO agents help article https://quickbooks.intuit.com/learn-support/en-us/help-article/accounting-bookkeeping/overview-agents-quickbooks-online/L9irCAtK4_US_en_US (one accountant-page quote search-snippet-only, flagged in §5) · Ramp: https://ramp.com/intelligence , https://ramp.com/accounting-automation-software , https://ramp.com/blog/accounting-agent-launch , https://ramp.com/accounts-payable , https://ramp.com/stack . All **[CT]**. Marketing performance claims on these pages (e.g., Digits' "outperforms frontier LLMs by 43%") are reported in §5 as vendor claims only and are used for taxonomy, not as evidence of capability.

### 17.5 Repository citations

All to `dmurguia/calibration-arena` @ `d478e45`: `backend/app/services/arena.py`, `ratings.py`, `leaderboard.py`, `reviewer.py`, `releases.py`, `backend/app/services/providers/professional.py`, `live.py`, `backend/app/models.py`, `schemas.py`, `scenarios.py`, `categories.py`, `config.py`, `backend/app/routers/battles.py`, `backend/pipeline/seed.py`, `frontend/src/components/workspace/PromptComposer.tsx`, `frontend/src/pages/JudgeSession.tsx`, `frontend/src/components/about/StatBand.tsx`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `backend/tests/test_ratings.py`. Repository documentation, seeded statistics, fictional vendors, and positioning language were treated throughout as untrusted design context, per the research brief.

---

## Appendix A: simulation code

Python 3, numpy only; deterministic seeds. Reproduces every number in §8.1 and §12. (Kept in-document rather than as repository code, per the no-product-code constraint of this research pass.)

```python
"""Simulations for the accounting-arena methodology report (2026-09-04).

Sim 1: 95% CI coverage of a prototype-style Bradley-Terry fit under
       evaluator- and scenario-clustered votes; naive iid vote bootstrap vs
       battle-cluster and evaluator-cluster bootstrap.
Sim 2: votes needed to identify the top model, by true Elo gap and noise.
Sim 3: pass^k under task heterogeneity (analytic).
Sim 4: gold-item (trap) discrimination of rater competence (binomial exact).

Mirrors the prototype's estimator: BT via MM with one virtual split game per
observed pairing (backend/app/services/ratings.py), Elo map 1200+400*log10.
"""
import numpy as np
from math import comb, sqrt

LN10 = np.log(10.0)


def fit_bt(pair_wins, M, iters=60, tol=1e-8):
    """pair_wins: {(i,j): [wins_i, wins_j]}, i<j. Prototype-style smoothing:
    +1 virtual split game per observed pairing; geometric-mean normalized."""
    pairs = list(pair_wins.keys())
    if not pairs:
        return np.zeros(M)
    idx_i = np.array([p[0] for p in pairs]); idx_j = np.array([p[1] for p in pairs])
    w_i = np.array([pair_wins[p][0] for p in pairs], float) + 0.5
    w_j = np.array([pair_wins[p][1] for p in pairs], float) + 0.5
    n_ij = w_i + w_j
    wins = np.zeros(M); np.add.at(wins, idx_i, w_i); np.add.at(wins, idx_j, w_j)
    p = np.ones(M)
    for _ in range(iters):
        dp = n_ij / (p[idx_i] + p[idx_j])
        denom = np.zeros(M); np.add.at(denom, idx_i, dp); np.add.at(denom, idx_j, dp)
        new_p = np.where(denom > 0, wins / np.maximum(denom, 1e-12), p)
        new_p = np.maximum(new_p, 1e-12)
        lp = np.log(new_p); lp -= lp.mean(); new_p = np.exp(lp)
        if np.max(np.abs(new_p - p)) < tol:
            p = new_p; break
        p = new_p
    return np.log(p)


def rating(beta):
    return 1200.0 + 400.0 * beta / LN10


def simulate_world(M, betas, n_eval, battles_per_eval, n_scen, sig_task, sig_eval, rng):
    """Bracket sessions. P(i beats j | e,s) = sigmoid((b_i+t_is+u_ie)-(b_j+t_js+u_je))."""
    task_fx = rng.normal(0, sig_task, size=(M, n_scen))
    votes, bid = [], 0
    for e in range(n_eval):
        eval_fx = rng.normal(0, sig_eval, size=M)
        for _ in range(battles_per_eval):
            s = rng.integers(n_scen)
            ms = rng.choice(M, size=4, replace=False)
            eff = betas[ms] + task_fx[ms, s] + eval_fx[ms]
            def duel(a, b):
                pa = 1.0 / (1.0 + np.exp(-(eff[a] - eff[b])))
                return (a, b) if rng.random() < pa else (b, a)
            w1, l1 = duel(0, 1); w2, l2 = duel(2, 3)
            wf, lf = duel(w1, w2); w3, l3 = duel(l1, l2)
            for w, l in [(w1, l1), (w2, l2), (wf, lf), (w3, l3)]:
                votes.append((ms[w], ms[l], bid, e))
            bid += 1
    return votes


def votes_to_pairs(votes):
    pw = {}
    for wi, li, _, _ in votes:
        i, j = (wi, li) if wi < li else (li, wi)
        pw.setdefault((i, j), [0, 0])[0 if wi == i else 1] += 1
    return pw


def bootstrap_ci(votes, M, scheme, B, rng):
    n = len(votes)
    if scheme != "vote":
        groups = {}
        key = 2 if scheme == "battle" else 3
        for v in votes:
            groups.setdefault(v[key], []).append(v)
        keys = list(groups.values())
    sam = np.empty((B, M))
    for b in range(B):
        if scheme == "vote":
            res = [votes[k] for k in rng.integers(n, size=n)]
        else:
            res = [v for g in rng.integers(len(keys), size=len(keys)) for v in keys[g]]
        sam[b] = rating(fit_bt(votes_to_pairs(res), M))
    return np.stack([np.percentile(sam, 2.5, axis=0),
                     np.percentile(sam, 97.5, axis=0)], axis=1)


def sim1(R=100, B=200):
    M = 8
    betas = np.linspace(0, 1.4, M); betas -= betas.mean()
    true_r = rating(betas)
    for label, sig, n_scen in [("iid, 1000 scen", 0.0, 1000),
                               ("fx sd=0.5, 1000 scen", 0.5, 1000),
                               ("fx sd=0.5, 5 scen", 0.5, 5)]:
        cov = {"vote": 0.0, "battle": 0.0, "eval": 0.0}
        for r in range(R):
            rng = np.random.default_rng(1000 + r)
            votes = simulate_world(M, betas, 40, 25, n_scen, sig, sig, rng)
            for scheme in cov:
                ci = bootstrap_ci(votes, M, scheme, B, rng)
                cov[scheme] += np.mean((ci[:, 0] <= true_r) & (true_r <= ci[:, 1]))
        print(label, {k: round(v / R, 3) for k, v in cov.items()})


def sim2b(reps=300):
    M = 8
    for gap, sig in [(35, 0.0), (35, 0.5), (70, 0.0), (70, 0.5)]:
        base = np.linspace(0, 1.2, M - 1)
        betas = np.concatenate([base, [base[-1] + gap * LN10 / 400]])
        betas -= betas.mean(); top = M - 1
        row = []
        for n_battles in [50, 125, 250, 500, 1000, 2000]:
            hits = 0
            for r in range(reps):
                rng = np.random.default_rng(7000 + r + n_battles)
                n_eval = max(1, n_battles // 25)
                votes = simulate_world(M, betas, n_eval, n_battles // n_eval,
                                       5 if sig > 0 else 1000, sig, sig, rng)
                hits += (np.argmax(fit_bt(votes_to_pairs(votes), M)) == top)
            row.append((4 * n_battles, round(hits / reps, 2)))
        print(gap, sig, row)


def sim3():
    for k in [1, 2, 4, 8]:
        pC = 1.0
        for i in range(k):
            pC *= (4 + i) / (5 + i)           # Beta(4,1): E[p^k]
        print(k, 0.8, round(0.8 ** k, 3), round(pC, 3))


def sim4():
    def p_pass_ge(n, thresh, q):
        kmin = int(np.ceil(thresh * n))
        return sum(comb(n, k) * q**k * (1 - q)**(n - k) for k in range(kmin, n + 1))
    for n in [5, 10, 20, 40]:
        print(n, round(p_pass_ge(n, 0.8, 0.60), 3), round(p_pass_ge(n, 0.8, 0.90), 3))
    z = 1.959964
    for q in [0.7, 0.8]:
        print("n for ±0.10 at q=%.1f:" % q, round(z * z * q * (1 - q) / 0.01))


if __name__ == "__main__":
    sim4(); sim3(); sim1(); sim2b()
```

Analytic head-to-head sample sizes (§12.2, Sim 2a) use n = (z_{α/2}·0.5 + z_β·√(p(1−p)))² / (p−0.5)² with z_{α/2}=1.96, z_β=0.8416.

*End of report.*





