# Calibrated Co. — where to start (founder memo)

**Date:** 2026-09-06, revised 2026-09-08 · **Author:** Claude (research + strategy pass) for David Murguia
**Question:** What would it take to build a vertical expert-data company that competes with, or sells into, Mercor / Surge / Micro1 / AfterQuery, starting from Calibration Arena, Corsac, and the Corsac Expert Network, with no traction yet?

Every number below carries a source. Items I could not confirm from a primary or reputable secondary source are marked **[unverified]** or **[single source]**. Where I make a judgment call, I say what it is grounded in and what you would need to test to trust it.

---

## 1. The market as of September 2026

**Concentration.** A directory tally counts 50+ vendors selling data and RL environments to labs, roughly $8.5B combined, with more than 75% held by Scale, Surge, Mercor, and Handshake ([RL List](https://www.rl-list.com/)) **[single source]**.

| Vendor | Scale signal | Economics | What they sell now |
|---|---|---|---|
| Mercor | $2.0B gross run-rate (Jun 2026); 300K+ expert pool, 30K weekly active; $10B valuation, reportedly in talks at $20B **[unverified]** | ~30% take, 35–40% GM **[single source]** | Expert marketplace, APEX benchmarks, RL environments (acquired Sepal, Deeptune), off-the-shelf datasets ([Sacra](https://sacra.com/c/mercor/), [Dealroom](https://dealroom.co/news/137121-mercor-doubles-to-2b-gross-revenue-run-rate-as-ai-labs-buy-expert-data/)) |
| Surge AI | ~$1.2B 2024 revenue, bootstrapped, ~12 lab customers make up most of it | Charges "50% to 10× more than competitors" | RLHF, evals, RL environments, red-teaming; owns DataAnnotation ([Contrary](https://research.contrary.com/company/surge-ai)) |
| Micro1 | $500M gross run-rate (Aug 2026); "130K+ vetted candidates, 100+ domains" | Retains 60–70%; 80–90% GM on off-the-shelf datasets | Realm (evals + RL envs for labs), Cortex (agent eval SaaS), Robotics; Zara AI interviewer ([TechCrunch](https://techcrunch.com/2026/08/20/ai-data-startup-micro1-reaches-500m-gross-run-rate-amid-ai-training-boom/)) |
| AfterQuery | YC W25; $300M valuation Apr 2026 → $3.2B Sep 1 2026; ARR "hundreds of millions"; "300,000+ verified practitioners" | Profitable | SFT, RL + rubrics, agent environments, computer-use trajectories; published benchmarks (FinanceQA, Terminal-Bench, Legora BAR) ([TechCrunch](https://techcrunch.com/2026/09/01/afterquery-reportedly-becomes-y-combinators-fastest-ever-unicorn-now-valued-at-3-2b/)) |
| Handshake AI | ~$1B gross annualized (Apr 2026) | ~45% net of contractor pay | Expert RLHF/evals off the student graph; pilots $100K–$500K expanding to multimillion ([AI Native GTM](https://ainativegtm.substack.com/p/how-handshake-reinvented-itself-for)) |
| Vals AI | $40M Series A at $400M (Aug 2026, a16z); cited in model cards from OpenAI, Anthropic, Google | n/a | Independent evals in law, finance, tax, medicine ([TechTimes](https://www.techtimes.com/articles/324479/20260814/vals-ai-raises-40m-a16z-frontier-models-fail-52-real-finance-analyst-tasks.htm)) |

**What labs buy has shifted.** Preference pairs are no longer the headline product. The three things being bought are expert-authored eval sets with rubrics, long-horizon agentic trajectories inside simulated "worlds" of files and tools, and RL environments. The clearest public proof that a small expert dataset moves a model: Applied Compute post-trained GLM-4.7 on fewer than 1,000, then ~2,000, Mercor expert legal tasks and moved it from 17th to 4th on APEX-Agents, with a +7.7 point transfer to GDPval ([Mercor blog](https://www.mercor.com/blog/scaling-data-apex-agents/)). Terms are undisclosed, and Applied Compute lists Mercor as *its* customer ([case study](https://www.appliedcompute.com/case-studies/mercor)), so treat it as a co-marketing partnership, not evidence of what a dataset sells for. At Mercor's public legal rates, 2,000 long-horizon tasks is on the order of $0.5–1M of expert time **[my estimate]**.

**Rates paid to professionals (public listings, 2026).** CPAs: $60–80/hr at Mercor for bookkeeping RL environments, $50–60 at DataAnnotation, up to $150 at Alignerr. Lawyers: $110–130 (Mercor). Physicians: $130–200 (Mercor, AfterQuery, Handshake). Sources in the research appendix.

**Failure modes with 2025–26 examples.** Neutrality loss (Scale lost OpenAI, Google, xAI within weeks of the Meta stake). Security incident (Mercor's March 2026 breach; Meta paused all work; five class actions). Labs in-housing (Cohere; xAI's own tutor org). Generalist supply being cut (xAI fired 500 generalist tutors to 10× specialists in medicine, finance, STEM; Handshake narrowed to finance and health). Misclassification suits (Surge, Mercor, Scale). Expert churn from empty queues and late pay (Handshake at 55% negative sentiment across 1,654 Reddit posts; Mercor "Project L" mass offboarding). Customer concentration (Surge). AI grading compressing human hours (Mercor's grader at 89% agreement with humans).

---

## 2. What you have already built (my read of the three repos)

- **Corsac**: an eval control plane with a real engine. ~870 packs, ~15.6K graded cases, a discovery → plan → draft → judge → publish pipeline, vaulted answer keys, and a scaffold for interop with Harvey's LAB task format. You have already generated an eval pack *about* Mercor. The pipeline is the one thing in your stack a Tier-1 vendor does not have and cannot build in a week (what that is worth, concretely, is in §4).
- **Corsac Expert Network**: application → credential upload → qualification quiz → admin approval → timed harness → earnings. Four offerings sketched (custom eval creation, domain scoring, review queue, agent QA audit). Manus-built, working, no customers.
- **Calibration Arena**: a Bradley–Terry arena for professional work product with credential tiers, hidden gold-standard traps, a behavioral timing floor, weighted votes, company boards, and a release radar. Runs on seeded synthetic votes; sign-in codes show in the UI; live model generation is wired but keyless.

The honest observation: these are three surfaces for one thesis, and none has a paying customer or a verified panel. The missing piece is not a fourth surface. It is twenty-five real CPAs and one buyer.

---

## 3. Where your positioning actually sits

**The "accounting benchmark" lane is already occupied.** Mercor built APEX-Accounting with Ramp (160 tasks in 10 simulated worlds, expert-authored and rubric-graded; best model 56.4% Mean Criteria@3, no model above 21.5% Pass@8) ([arXiv](https://arxiv.org/abs/2607.27189)). Micro1 publishes Realm Financial (103 tasks: IFRS reconciliation workbooks, backtests, term sheets) and Realm Tax (full Form 1040 from source documents, 20+ criteria per task, 44% of criteria unsolved by any model) ([micro1](https://www.micro1.ai/benchmark/realm-tax)). AfterQuery has FinanceQA and SpreadsheetBench 2. Vals runs a finance-agent eval where frontier models fail 52% of tasks. Column Tax's TaxCalcBench and Rivet's TaxBench cover tax computation. Anyone you pitch "an accounting benchmark" to will name three of these.

**The "independent rating agency" lane is partly occupied by Vals**, which is a16z-backed, cited in model cards, and already ranks legal AI products. That overlaps with the arena's "vendor products on the board" story.

**Rater calibration is proof, not the pitch.** *Revised after your pushback, and you are right.* A buyer has no way to vet the judges themselves and no baseline to compare a "94% calibrated panel" against, so leading with it asks them to trust a number they cannot check. It stays as the mechanism that makes a grade defensible when someone challenges it, and as one line in the security and provenance story. It comes off the headline.

**The pitch a Rillet-shaped buyer can act on.** "APEX-Accounting, Realm Financial, Realm Tax, FinanceQA, TaxCalcBench are all benchmarks. Knowing how to *use* them is the value. I run an arena of licensed accountants who measure models against those benchmarks and against live close work, tell you which criteria you lose points on and why, and produce the tasks and grading that move the score." Grounded in: the Applied Compute × Mercor case, where a ~2,000-task expert set plus a competent post-training shop produced a top-4 public leaderboard result and both parties used it as marketing; Micro1 and AfterQuery both growing on benchmark posts rather than listed gigs; Vals being cited in model cards because labs want an outside number they did not produce themselves.

What is true today versus what you have to make true before saying it out loud:

| Claim in the pitch | Status today | What makes it true |
|---|---|---|
| "An arena of accountants measuring models in real time" | The mechanics exist; the votes are seeded and synthetic | About 10 CPAVerify-verified CPAs running weekly sessions on live model output (§8), and one board switched from seeded to live generation |
| "Against all of them" | Partly possible. FinanceQA (AfterQuery), TaxCalcBench (Column Tax), and GDPval's public gold subset are downloadable and can run through Corsac now. Realm Financial/Tax and the Vals finance-agent set are private. Whether Mercor released the APEX-Accounting tasks or only the paper I could not confirm **[unverified]** | Say "the public accounting benchmarks, plus a private held-out set built the same way as the ones you can't download." Replicating the private benchmarks' methodology (criteria per task, source-document worlds) is legitimate; claiming to run them is not |
| "Help you score higher on complex accounting benchmarks" | The honest version is a loop: diagnostic → private held-out eval → training tasks or RL environment → re-measure | Never train on the public set itself. Any buyer's ML lead will ask about contamination in the first call, and the held-out set is your answer |

What this buys you that "measured judges" did not: a question the buyer already has ("where do we lose points?"), a cheap first deliverable (a benchmark diagnostic on a 50-task set), and a reason to publish (the public board is the free version of the diagnostic).

---

## 4. The founder call: Panel → Artifact → Customer in 90 days

This is my recommendation. Each step names what it is grounded in and what would falsify it.

### Weeks 0–2: pick the wedge inside accounting

Two candidates.

- **Month-end close: reconciliation, accruals, flux, journal entries.** Grounded in: demonstrated lab demand (Mercor built exactly this with Ramp), year-round supply, your arena already has these primitives, and the vendor ICP (Rillet, Numeric, Basis, Puzzle, Digits) lives here.
- **Tax return preparation.** Grounded in: the worst public scores (TaxCalcBench under one-third of returns correct; TaxBench regressing across model releases), which means labs have a visible problem. Against it: Micro1 already sells Realm Tax and Prospera, Column Tax and Rivet publish benchmarks, and CPA supply is seasonal (your own PRD notes the mid-April to June and post-October 15 windows).

**Recommendation: close and reconciliation first, tax as season two.** This is a judgment call. Validate it with five conversations: two accounting-AI vendors, two data-vendor ops managers, one lab human-data person. If three of five say tax is what they cannot source, flip it.

### Weeks 0–4: recruit 25 verified CPAs, not 500

Grounded in: AfterQuery's demand-first genesis; Surge's ~50K curated experts versus DataAnnotation's million gig workers; xAI and Handshake both cutting generalists for specialists. Twenty-five calibrated CPAs who show up weekly are worth more to a buyer than a thousand applicants.

- Use the arena as the funnel (free session, calibration score, credential), CPAVerify for tier 2.
- Pay $80–100/hr for paid work. Market is $60–80 at Mercor and up to $150 at Alignerr. Paying at the top of the CPA range is cheap relative to churn.
- Pay weekly, on time, with no unpaid "training" hours. Late and partial pay is the top reported churn driver in 2026 and the basis of the misclassification suits.
- Channels from your PRD still hold: r/Accounting, Fishbowl, Going Concern, state societies, CPA-exam communities for the trainee tier, plus your own network.

Kill criterion: fewer than 10 CPAVerify-verified reviewers with three completed sessions each after 30 days means the funnel does not work and you should recruit by direct outreach instead.

### Weeks 2–8: build one licensable artifact

Grounded in: Micro1's 80–90% gross margin on off-the-shelf datasets versus 30–35% on hours at Mercor; Applied Compute's result that 1–2K expert tasks measurably move a model; AfterQuery's growth on published benchmarks rather than listed gigs.

The artifact: **100–200 closed-universe close-and-reconciliation tasks**, each a synthetic company world (ledger extract, bank statements, sub-ledgers, policies, a terse controller brief), solved by a CPA, with 20+ fact-anchored pass/fail criteria, graded by a calibrated panel, with per-rater calibration metadata in the export. Corsac's pipeline generates the worlds and drafts the rubrics; CPAs solve, correct, and grade. That is your actual unfair advantage: the generator plus the measured panel.

Cost estimate **[mine]**: 150 tasks × ~4 expert hours × $90 ≈ $54K, plus grading and review, ≈ $70–90K all-in. A 50-task pilot version is ≈ $25–30K. That is the number to fund from a design partner's pilot fee or, with the guardrails in §9, from the pre-seed float.

#### What "Corsac's generator is the unfair advantage" means

The expensive part of an expert task set is not the grading. It is authoring the *world*: the trial balance, the sub-ledgers, the bank statements, the policies, the seeded errors, the answer key, and the 20+ criteria per task. Mercor and Ramp built APEX-Accounting as 160 tasks inside 10 hand-built worlds; Micro1's Realm Tax carries 20+ criteria per return. When a person authors all of that, you pay CPA rates for hours of scaffolding before any judgment happens. My estimate is 3–6 expert hours per task from scratch **[mine; no vendor publishes this]**, and that is the number behind the $25–30K pilot figure above.

Corsac already has the discovery → plan → draft → judge → publish pipeline and vaulted answer keys across ~870 packs. If it can generate the closed-universe world and seed the exceptions programmatically, three things change:

1. **Cost per task drops.** CPAs verify, correct, and adjudicate instead of authoring. My guess is 1–1.5 expert hours per task instead of 4, which either halves the pilot cost or doubles the task count for the same money.
2. **Ground truth is known by construction.** The seeded exceptions *are* the answer key, so most criteria become programmatically checkable and experts only rule on the ambiguous ones. That is the shape a post-training shop needs for RL (a verifiable reward), not a static list of graded answers.
3. **Instances are cheap.** Regenerating a world with new numbers gives you a contamination-resistant held-out set and a fresh environment per training rollout. A hand-built 160-task set cannot do either, which is why the incumbents' benchmarks go stale and why they cannot sell "the same thing again, unseen."

What I have not verified: how many of the 870 packs are accounting, and whether a Corsac-generated close world passes a CPA realism check. That is T4, and it is the test to run first, because the entire cost argument rests on it. If fewer than 80% of generated worlds are rated "I would see this at work," the generator is a rubric drafter, useful but not an unfair advantage.

### Weeks 4–12: sell to the buyer most likely to say yes, in this order

1. **Accounting-AI vendors, Rillet first.** The package, in the order they can buy it:
   - *Benchmark diagnostic.* Run their model or product through the public finance benchmarks and a 50-task private held-out set built the same way, graded by the panel, returned as a criteria-level failure taxonomy: which criteria fail, whether the miss is cutoff, classification, policy, or arithmetic, and which tasks to fix first. $10–25K **[my estimate]**, two to three weeks.
   - *Exception bench.* A standing panel of CPAs that reviews the exceptions their system misses or flags with low confidence, returns adjudicated labels weekly, and feeds them back as eval and training data. This was your suggestion and it is the best-shaped offer in the list: a retainer, not a project, sitting on the workflow where close-automation products lose customers. Grounded in my read of the Rillet, Numeric, and Basis product surfaces, **not** in any conversation with them; confirm on the first call that exception handling is where their support load lives.
   - *Training tasks or an RL environment* from Corsac worlds, priced per task, only if they post-train. Verify that on the first call; if they only prompt and retrieve, sell the first two and skip this.
2. **Post-training shops and application-layer companies** (Applied Compute-shaped, Harvey-shaped). These are the buyers that most resemble the one public case where an expert set demonstrably moved a model: they need a domain task set plus the expertise to grade it, and they market on the leaderboard result. Applied Compute lists Harvey, Handshake, and Mercor as customers; Legora buys from AfterQuery; Harvey published LAB. More reachable than a lab, and they already know what a verifiable reward is.
3. **Tier-1 data vendors as a channel.** Mercor, Handshake, Micro1, and AfterQuery all run partner and white-label pools, and Handshake and xAI have publicly pivoted toward finance and health specialists. Offer calibrated CPA capacity as a subcontract, with calibration reports per batch. This is also the test for T2: do they pay a premium for measured raters, or only a seat at the standard rate?
4. **A frontier lab directly.** OpenAI has a public data-partnerships form; Anthropic and OpenAI both staff human-data operations managers who orchestrate outside vendors. Lowest probability without a named artifact and one reference, so do it last and with the artifact in hand.

Keep pilot asks at $25–75K. The $100K–$500K pilots reported at Handshake come with a track record you do not yet have. I found no public data on sub-$100K pilots for small vendors **[unverified]**, so treat that range as a hypothesis.

### What the arena is for, and what to stop building

The arena is the recruiting funnel, the public track record, and the credential. It is not the product. Engineering worth doing on it in the next 90 days: real email delivery for sign-in, CPAVerify tier-2 verification, and live model generation on one board so the boards stop being seeded. Everything else waits. The cheapest PR artifact is *State of Finance AI, Issue 1*, generated from the release radar, because AfterQuery and Micro1 both grew on benchmark posts.

Fold the Corsac Expert Network into Calibrated's panel operations (application, vetting, harness, and earnings already exist there) rather than running it as a separate brand. Park the Corsac "OS for enterprises" motion; it is a slower sale to a different buyer.

### Security and provenance as a feature

Grounded in: the Mercor breach cost them Meta overnight; Micro1 markets a US-only, no-adversary workforce; Surge had a document leak in 2025. A small vendor can be cleaner than a 300K-person marketplace: registry-verified US-licensed reviewers, synthetic documents so there is no client data to lose, no screen-scraping tools, and only the PII a license lookup needs. Put it in the pitch on day one; get SOC 2 Type I when the first lab conversation asks for it, not before.

---

## 5. Things to go test, with kill criteria

| # | Hypothesis | Test | Kill if |
|---|---|---|---|
| T1 | CPAs will do three free arena sessions and then accept paid work at ~$90/hr | Recruit through the arena for 30 days | Fewer than 10 verified reviewers with 3 sessions |
| T2 | Buyers pay a premium for per-rater calibration metadata (now a proof point, not the pitch) | Ask three human-data ops managers at Tier-1 vendors or labs whether it changes price or vendor choice | None will pay a premium → sell certified vendor evaluations only, and keep calibration as an internal QA tool |
| T3 | An accounting-AI vendor will pay ≥ $10K for a certified evaluation | Rillet first, then two cold vendors | Zero of three after a demo of a 50-task set |
| T4 | Corsac's pipeline can produce close tasks CPAs rate as realistic | Generate 50 worlds; have 5 CPAs rate realism | Under 80% rated "would see this at work" |
| T5 | You can float 30–60 days of expert payroll on a pilot | Model cash from the $25–30K pilot | Negative cash before the first invoice clears |
| T6 | A Rillet-shaped vendor will pay for a benchmark diagnostic plus an exception-bench retainer | Pitch the §4 package to Rillet and two cold accounting-AI vendors | Zero of three take the diagnostic at ≥ $10K → the buyer is the post-training shop, not the vendor; reorder §4 |
| T7 | The §8 funnel yields 12 verified CPAs in 4 weeks for under $7K of recruiting spend | Run §8 as written and measure each stage | Fewer than 12 passers by week 4, or cost per verified CPA above $600 → change targeting before adding channels |

---

## 6. Naming and brand

No direct collision found for "Calibrated" in AI data. Adjacent names: Calibrate Ventures, Calibrate Group, Calibre Labs, and "Arena Calibrate" (a BI product at thearena.ai), which is close enough to "Calibration Arena" to be worth a trademark search. I did not check domain availability.

## 7. What the landing page claims, and what you must be able to defend

`landing/index.html` mirrors the AfterQuery/Micro1 skeleton (hero → trust strip → problem → offerings → verticals → loop → boards → two audiences → research → company → CTA) but is light, numerate, and shows the product, which the teardown says is exactly where both competitors are weak. After the repositioning in §3 the page leads with "Accounting AI, scored by accountants" and a benchmark diagnostic, with rater calibration kept as a proof point lower down. Claims on it and their source:

- 870 eval packs, 15,600 graded cases: Corsac README.
- Five comparisons per session with one hidden trap; 80% trap floor; 1.5× and 2× vote weights: arena code and PRD.
- "Measure models against the public accounting benchmarks and against real close work": defensible once FinanceQA, TaxCalcBench, and the GDPval subset run through Corsac with a verified panel grading. Until then it is the plan, so keep the page in draft or soften to "built to".
- "The best models clear only about half the criteria on expert-authored accounting tasks": APEX-Accounting's 56.4% Mean Criteria@3.
- The hero instrument is an illustrative diagnostic (criteria passed, three failure rows) and is labeled illustrative. Replace it with a real one from the first pilot.
- "US-licensed reviewers," "paid weekly," "two founding seats per vertical": commitments; §8 makes the first two true.
- Contact address is a placeholder (`hello@calibrated.co`) set in one constant at the bottom of the file, and "Join the panel" still anchors to a section rather than the intake form (§8, Channel F).

---

## 8. Panel acquisition plan: 25 verified CPAs in six weeks

The channels you named (AI-gig subreddits, r/Accounting, LinkedIn "AI trainer CPA"), grounded in how those places actually behave in 2026. Numbers are my planning estimates unless sourced; the point of the plan is to replace them with your measured rates by week 3.

### Sequencing: recruit first, but only to the assessment line

Your question was whether to recruit the CPAs first. My answer is yes to the cheap, reversible half of recruiting, and no to the expensive half until a buyer has named a price.

- **Start the funnel now.** Outreach, intake, CPAVerify, and paid assessments cost about $4–7K total and have a four-to-six-week lead time, so waiting for a buyer before starting them means the buyer waits six weeks for a panel. The assessments also produce the T4 realism data you need before spending on the artifact.
- **Run the five buyer conversations in the same two weeks** (§4, Weeks 0–2): Rillet, one more accounting-AI vendor, one post-training shop, one data-vendor ops manager, one lab human-data contact. You are not selling yet; you are asking what they would pay for the diagnostic and the exception bench.
- **Do not promise guaranteed hours to anyone until one of two things is true:** a signed pilot or design-partner fee, or a deliberate decision to fund the 50-task artifact as spec work from the pre-seed float (§9). The guaranteed-hours line is the only part of the offer that can hurt you, because it is a promise to people who have been burned by exactly that promise before.
- **The minimum you need to sell the diagnostic** is roughly 6–8 verified CPAs and 20–30 held-out tasks, not 25 and 150. So cohort 1 can be small and still unlock the first paid deliverable.

Grounded in: AfterQuery's demand-first genesis (a lab asked before they recruited), the memo's kill criteria, and the churn data on empty queues. The judgment call is mine.

### Who you are recruiting

- **Primary: CPAs who already do AI-trainer work.** People whose LinkedIn headline or experience reads "AI Trainer," "AI Tutor," "Expert Contributor," "Subject Matter Expert (Accounting)," or "Domain Expert" at Outlier, Mercor, DataAnnotation, Alignerr, Turing, Micro1, or Handshake AI. Why they are the best first cohort: they have passed a vendor screen, they know rubric grading and pairwise comparison, they are already set up as 1099 contractors, and (from the platform subreddits) they are chronically short of tasks. Mercor's "Project L" offboarding and Handshake's 55% negative sentiment across 1,654 Reddit posts (§1) describe exactly the pool you want.
- **Secondary: CPAs doing close and reconciliation today** with no AI-gig history. Controllers, accounting managers, senior accountants, Big 4 audit seniors who have run client closes. Higher realism, slower onboarding.
- **Licensure is the gate, not the pitch.** Active license confirmed on CPAVerify (NASBA's free national lookup) before any paid hour. A trainee tier from r/CPA candidates is season two.

### The offer, written against what these workers complain about

The recurring complaints in r/DataAnnotationTech, r/outlier_ai, and the Mercor and Handshake threads are unpaid assessments and onboarding, empty queues after passing, deactivation without explanation, late or partial pay, and (since March 2026) how platforms handle identity documents. Each line of the offer answers one of them.

| Complaint | Your offer | Cost to you |
|---|---|---|
| Unpaid assessments | $100 flat for a ~75-minute assessment that is real work (below). Everyone who completes it is paid, pass or fail | ~$4K for 40 assessments |
| Empty queues | Guaranteed minimum of 5 paid hours a week for the first 4 weeks for the cohort you accept | 12 CPAs × 5 h × 4 wk × $90 ≈ $21.6K, which has to be pilot work, not overhead. Size cohort 1 to the pilot you have funded; go to 25 on the first invoice |
| Rate secrecy | $90/hr stated in the first message. Mercor lists $60–80 for accountants; Alignerr up to $150 | Already in the pilot estimate |
| Deactivation without explanation | Reviewers see their own calibration score, the 80% floor is published, and you give two weeks' notice | Nothing; the arena already computes it |
| Late pay | Paid every Friday through a real payout rail (below) | Fees only |
| PII exposure | License verified against the public registry; identity and tax documents handled by the payout provider, never stored by you | Nothing, and it lands after the Mercor breach |
| No portable credential | A verified arena profile and a "Calibrated Panel · Accounting · Season 1" line they can put on LinkedIn | Nothing |

### Channel A: LinkedIn, "AI trainer CPA"

The highest-yield channel and the one to run every day.

- **Search.** Sales Navigator Boolean on headline and current title: `("AI Trainer" OR "AI Tutor" OR "Expert Contributor" OR "Subject Matter Expert" OR "Domain Expert") AND CPA`, United States. A second list for `(Outlier OR Mercor OR DataAnnotation OR Alignerr OR Turing OR Micro1 OR Handshake) AND CPA`. A third for the secondary profile: `CPA AND ("month-end close" OR reconciliations OR Controller OR "Accounting Manager")` with the Open to Work filter.
- **Tooling reality.** Free LinkedIn caps invitations at roughly 100 a week and throttles search after a few hundred results (the "commercial use limit"). Sales Navigator is about $100 a month with Boolean search, saved lead lists, and ~50 InMails; Recruiter Lite is about $170 with ~30. Prices are approximate and change. Automation tools (PhantomBuster, Dux-Soup, and the like) violate LinkedIn's terms and get accounts restricted, which would take your own profile down with it. Do it by hand: 20–25 personalized sends a day, five days a week.
- **Message shape.** A 300-character connection note, a longer follow-up on accept, InMail for the ones who do not accept within a week. State the rate, the paid assessment, and the cohort size in the first message. Copy is at the end of this section.
- **Response planning.** LinkedIn's own guidance puts InMail response around 18–25% in general. A message that says "you already do this work; here it is at a stated rate with a paid assessment" should do better, but plan on 20% and measure.
- **Funnel, planning estimates:** 300 sends over 3 weeks → ~60 replies → ~35 assessments booked → ~25 completed → ~15 pass (60%) → 12–15 verified. That is cohort 1 from LinkedIn alone.
- **Secondary: a LinkedIn job post.** "Contract CPA, AI evaluation panel, $90/hr, remote, US-licensed." Free posts get little reach; promotion runs on a daily budget you set. Mercor's "AI trainer" posts draw hundreds of applicants, so expect cheap but noisy inbound. Worth one post; do not rely on it.

### Channel B: the AI-gig subreddits

r/DataAnnotationTech and r/outlier_ai are the large ones; platform-specific subs for Mercor, Alignerr, and Handshake exist or have existed under varying names, so verify each before posting. Also r/forhire (allows `[Hiring]` posts if pay is stated), r/WorkOnline, and r/RemoteJobs.

How they behave: the front page is complaint threads (empty queue, deactivated, pay late), "is X legit?" questions, and a steady stream of fake-recruiter scams, so members are wary by default and mods generally ban self-promotion and recruiting posts.

What works there, in order:

1. Message the mods first and ask for one transparent post. Some will say no; r/forhire will say yes in its format.
2. The post is a founder note, not a job ad: who you are, the rate, the paid assessment, the pay rail, the cohort size, why licensure is required, and links to the landing page and the live arena. Answer every comment for 48 hours; the comment thread is where credibility is built or lost.
3. DM the people who comment and identify as CPAs. Reddit chat is fine for that; keep it to people who engaged.
4. Do not post the same thing in five subs the same day. One account, transparent, low volume.

Planning estimate: 30–80 inbound per successful post, 10–20% of whom hold a CPA license, so 5–15 assessments per post. The larger value is second-order: being known in those threads as the one who pays for assessments.

### Channel C: r/Accounting and the professional subs

r/Accounting is large and, like most professional subs, restricts or bans job postings; r/taxpros requires professional verification and prohibits advertising; r/CPA is exam candidates; r/Bookkeeping is not CPAs. Read the current rules before doing anything; they change.

What works: do not post an ad. Search for and reply in the recurring threads about AI side work ("has anyone done Mercor or Outlier as a CPA?", "AI trainer gigs for accountants") as the founder, explicitly identified, with the rate and the paid assessment. Those threads recur every few weeks and the people asking are your secondary profile. Expect a handful of qualified conversations a week, not a flood, and a real chance of a ban if you look like a spammer, so treat this as supplementary.

### Channel D: where accountants already congregate (secondary)

- **Fishbowl.** The Big 4 bowls are where disillusioned seniors are. Official recruiting there is a paid product; an organic founder post can work. Anonymous, so expect low reply identification.
- **Going Concern.** Its audience is exactly Big 4 leavers. Ask about sponsored placement cost; I did not verify the current state of its jobs board.
- **State CPA society classifieds** (CalCPA, TXCPA, NYSSCPA, and your home state). Cheap, slow, highest trust per lead.
- **#TaxTwitter on X.** Season two, for the tax wedge.

### Channel E: referrals, from week 4

$150 per referred CPA who passes the assessment and completes 10 paid hours. DataAnnotation and Outlier both run referral programs, and CPAs know CPAs. Planning estimate: 0.5 qualified referrals per active panelist over the first two months.

### Channel F: the arena as the landing

Every outreach links to one "Join the panel" page. Today the landing page's button anchors to the panel section and the contact is a mailto; wire it to an intake form (Tally or Typeform) that collects name, state of licensure, license number, specialty (close/recon, tax, audit), hours available per week, platforms worked, LinkedIn URL, and rate expectations. The form triggers the CPAVerify check and the assessment invite. Free arena sessions stay as the try-before-you-apply path (T1), but do not depend on them for cohort 1.

### The paid assessment (~75 minutes, $100 flat)

1. **One arena session**: five blind comparisons with one hidden trap. Already built.
2. **One closed-universe reconciliation** from a Corsac world with 4–6 seeded exceptions. Score on exceptions found, false positives, and time. This doubles as T4 data.
3. **Grade one model answer against a rubric and write three criteria of your own.** Measures grading and authoring, which is what lead reviewers do.

Pass: the trap correct, at least 70% of seeded exceptions found **[threshold mine; tune after the first 20]**, and time above the behavioral floor. Results within 48 hours; offers the same week.

### Verification, contracts, and pay

- **License**: CPAVerify by name and state, free. State board lookup where CPAVerify is missing a state.
- **Contract**: independent-contractor agreement with IP assignment, confidentiality on your tasks, non-exclusive, no non-compete. W-9 collected by the payout rail.
- **Payout rail**: Stripe Connect (handles KYC, 1099s, and weekly transfers; you never see identity documents), or Gusto's contractor-only plan (roughly $35 a month plus a few dollars per contractor). Deel works but is priced for global employment. Prices approximate.
- **Classification**: the Surge, Mercor, and Scale suits are about control (set schedules, screen monitoring, per-minute tracking). Do not set hours, do not monitor screens, pay per task or per session against a rate card. California's AB5 exempts licensed accountants from the ABC test (the older Borello test applies), which helps, but confirm with counsel before cohort 1 is paid.
- **Do not** ask recruits to share task content from other platforms; their contributor agreements forbid it and it is not yours.

### Six-week schedule

| Week | Do |
|---|---|
| 0 | Intake form live, assessment built from the arena plus one Corsac world, payout rail and contract in place, CPAVerify process written down, landing "Join the panel" wired to the form. Start a Sales Navigator trial. |
| 1–3 | LinkedIn: 20–25 sends a day. One mod-approved subreddit post in week 1, a second in week 3. Reply in r/Accounting threads as they appear. One Fishbowl post. |
| 2–4 | Assessments in two batches a week, results in 48 hours, offers the same week. |
| 4 | Cohort 1 (12) starts guaranteed hours on the pilot tasks. Referral program opens. |
| 5–6 | Cohort 2 to 25, funded by the first invoice. Second-round posts carry cohort-1 quotes and a real (not illustrative) diagnostic. |

Seasonality: tax-side CPAs disappear from late January to April 15 and around October 15; close-side accountants are unavailable the first five business days of each month and quarter-end weeks. Book assessments in the second half of the month. September to December is the best window for tax-side recruits, and you are in it.

### Budget, my estimates

| Item | Amount |
|---|---|
| 40 paid assessments | $4,000 |
| Sales Navigator, two months | ~$200 |
| Referral bonuses, 10 | $1,500 |
| Payout rail fees and form tooling | $100–300 |
| **Recruiting overhead** | **~$6–7K** |
| Cohort 1 guaranteed hours (pilot work, not overhead) | ~$21.6K |

### Measure per channel, with kill criteria

Track sends, replies, assessments booked, completed, passed, and active after four weeks, per channel.

- LinkedIn reply rate under 8% after 150 sends → rewrite the message and targeting before sending more.
- Fewer than 10 licensed CPAs from Reddit in two weeks → drop it to opportunistic replies only.
- Assessment pass rate under 35% → the assessment is miscalibrated or the targeting is; find out which before recruiting more.
- Active-after-four-weeks under 60% → an offer problem (queue empty or pay late), not a sourcing problem.

### Copy to start from

**LinkedIn connection note (under 300 characters):**

> Hi [First name], I'm building Calibrated, an accounting-AI evaluation panel of US-licensed CPAs. I saw you do AI-trainer work at [platform]. $90/hr, weekly pay, and the 75-min assessment is paid ($100). Open to a look?

**Follow-up on accept:**

> Thanks for connecting. Short version: I run Calibration Arena, where licensed CPAs grade AI models on close and reconciliation work against the public accounting benchmarks. I'm hiring the first cohort of 12 for a paid pilot: $90/hr, minimum 5 hrs/week for the first month, paid every Friday, license verified on CPAVerify, no unpaid onboarding. The assessment is 75 minutes of real work and pays $100 whether or not you join. Here's the intake form: [link]. Happy to answer anything first.

**Subreddit post (after mod approval):**

> Founder here, not a recruiter. I'm building a paid panel of licensed CPAs to evaluate AI models on month-end close work. Rate is $90/hr, paid weekly by [rail], no unpaid training. The 75-minute assessment pays $100 whether or not you're accepted. First cohort is 12 people with a guaranteed 5 hrs/week for the first month. You need an active CPA license (checked on CPAVerify); we don't collect ID documents ourselves. Site and the live arena: [links]. Ask me anything below; I'll answer everything.

---

## 9. Guardrails for floating this on $25–50K of pre-seed money

You said you can float coordination from the pre-seed. $25–50K is 280–550 CPA hours at $90, which is exactly one 50-task pilot artifact plus one small cohort's guaranteed month. It is not two attempts. These are the guardrails I would put in place; the ones grounded in something specific say so, the rest are judgment.

**Tranche the money against gates, not a calendar.**

| Tranche | Amount | Spend on | Release gate |
|---|---|---|---|
| 1 | $5–7K | Recruiting overhead, 40 paid assessments, tooling (§8) | None; this is the reversible part |
| 2 | $20–25K | 50-task held-out artifact (CPA solve, grade, adjudicate) and cohort 1's guaranteed month | T4 realism ≥ 80% on generated worlds **and** either a signed pilot fee or a design partner's written commitment to evaluate the diagnostic |
| 3 | Remainder | Cohort 2, tasks 51–150 | Customer revenue only. If tranche 3 comes from the pre-seed, something in tranche 2 failed |

**Cash and payroll.**

- A separate account or sub-ledger for panel payroll, funded weekly from the tranche, so overspend is visible the week it happens and not at month end. Fund the payout rail from that account only.
- No payment before a signed contractor agreement and a CPAVerify record on file. No assessment payment before intake. Pay weekly, Fridays, without exception: late pay is the top churn driver in §1 and the basis of the misclassification suits.
- Guaranteed hours are committed in four-week blocks with a written end date, sized to funded work. Never roll a guarantee forward on the hope of a pilot.
- Cap paid assessments at 40 in cohort 1. If you hit the cap without 12 passers, the targeting is wrong (T7), and more assessments do not fix that.

**Legal and classification.**

- Contractor agreement with IP assignment on every task, criterion, and grade. The dataset is the asset the pre-seed is buying; if a contractor owns a piece of it you cannot license it. Non-exclusive, no non-compete, confidentiality limited to your task content.
- Do not set schedules, monitor screens, or track minutes. Pay per session, per task, or against a rate card. This is what the Surge, Mercor, and Scale suits turn on. Have counsel confirm the AB5 professional exemption for licensed accountants before cohort 1 is paid.
- Synthetic worlds only in the pilot. The moment you accept a buyer's real ledgers you need a DPA, a security questionnaire, and eventually SOC 2, none of which $25–50K covers. "We never touch client data" is both the security pitch and the cheapest guardrail you have.

**Quality of the artifact, so the money buys something a buyer will pay for.**

- T4 before tranche 2. Five CPAs rate 50 generated worlds; under 80% "I would see this at work" and you author worlds by hand at 4 hours each, which changes the budget.
- Two graders per task on the held-out set, with a third CPA adjudicating disagreements. Agreement rate is a number a post-training shop will ask for **[my expectation from how eval sets are reviewed; no vendor publishes theirs]**.
- Every task has a vaulted answer key (Corsac already does this) and a criteria list a CPA has signed off on. Nothing generated goes to a buyer without a CPA's name on it.
- Keep a contamination log: which public benchmark items have been run, by which model, when. The held-out set stays out of every prompt and every training run, including your own. This is the first question a buyer's ML lead asks.

**Commercial.**

- Do not build the artifact to one buyer's spec unless they pay for the customization. License the base set non-exclusively so the same 50 tasks can go to Rillet, a post-training shop, and a data vendor. Micro1's 80–90% margin on off-the-shelf datasets exists because they sell the same thing more than once.
- Price the diagnostic at cost-plus, not for margin. Its job is a reference and a real (not illustrative) result for the landing page.
- Ninety-day clock. If by day 60 there is no paid pilot and no design partner, stop guaranteed hours at the end of the current block and keep the arena running free. The panel survives; the payroll does not.

**Investor hygiene.**

- Say in writing to your pre-seed investors what this money buys: a verified CPA panel and a licensable 50-task accounting eval set, and the tests (T3, T4, T6, T7) that decide whether to spend more. If the round was raised on a different product story, say that this is the wedge and why. I do not know what you raised on, so check this against the deck.
- A one-page weekly log: spend against tranche, passers, tasks produced, buyer pipeline stage. It takes ten minutes and it is what you will need for the seed anyway.
- No equity for panelists, no "founding seat" language without a written rate and term. Cash and a credential, as the offer says.

---

## Appendix: research sources

AfterQuery: [BusinessWire Series A](https://www.businesswire.com/news/home/20260409469482/en/AfterQuery-Raises-$30-Million-Series-A-Round-at-$300-Million-Valuation) · [TechCrunch $3.2B](https://techcrunch.com/2026/09/01/afterquery-reportedly-becomes-y-combinators-fastest-ever-unicorn-now-valued-at-3-2b/) · [afterquery.com/products](https://www.afterquery.com/products). Micro1: [TechCrunch Aug 2026](https://techcrunch.com/2026/08/20/ai-data-startup-micro1-reaches-500m-gross-run-rate-amid-ai-training-boom/) · [Realm Tax](https://www.micro1.ai/benchmark/realm-tax) · [Realm Financial](https://www.micro1.ai/benchmark/realm-financial). Mercor: [Sacra](https://sacra.com/c/mercor/) · [Dealroom](https://dealroom.co/news/137121-mercor-doubles-to-2b-gross-revenue-run-rate-as-ai-labs-buy-expert-data/) · [APEX-Accounting](https://arxiv.org/abs/2607.27189) · [TechCrunch breach](https://techcrunch.com/2026/04/09/after-data-breach-10b-valued-startup-mercor-is-having-a-month) · [CPA listing $60–80/hr](https://himalayas.app/companies/work-mercor/jobs/accountant-upto-80-hr). Surge: [Contrary](https://research.contrary.com/company/surge-ai) · [Sacra](https://sacra.com/c/surge-ai/). Handshake: [Sacra](https://sacra.com/c/handshake/) · [AI Native GTM](https://ainativegtm.substack.com/p/how-handshake-reinvented-itself-for) · [Breaking Even review](https://breakingeven.online/blog/handshake-ai-review). Scale: [TechCrunch OpenAI drops Scale](https://techcrunch.com/2025/06/18/openai-drops-scale-ai-as-a-data-provider-following-meta-deal). Vals: [TechTimes](https://www.techtimes.com/articles/324479/20260814/vals-ai-raises-40m-a16z-frontier-models-fail-52-real-finance-analyst-tasks.htm). Benchmarks: [GDPval](https://openai.com/index/gdpval/) · [HealthBench](https://openai.com/index/healthbench/) · [Harvey LAB](https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark) · [TaxCalcBench](https://github.com/column-tax/tax-calc-bench) · [TaxBench](https://www.rivet.tax/taxbench). Rates: [Built In](https://builtin.com/articles/train-ai-side-hustle) · [Alignerr](https://breakingeven.online/blog/alignerr-review-2026) · [DataAnnotation accounting](https://www.dataannotation.tech/accounting). Market structure: [Wing VC](https://www.wing.vc/content/who-will-win-the-rl-environment-market--and-why) · [RL List](https://www.rl-list.com/).
