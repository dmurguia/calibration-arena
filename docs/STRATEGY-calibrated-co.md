# Calibrated Co. — where to start (founder memo)

**Date:** 2026-09-06 · **Author:** Claude (research + strategy pass) for David Murguia
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

- **Corsac**: an eval control plane with a real engine. ~870 packs, ~15.6K graded cases, a discovery → plan → draft → judge → publish pipeline, vaulted answer keys, and a scaffold for interop with Harvey's LAB task format. You have already generated an eval pack *about* Mercor. The pipeline is the one thing in your stack a Tier-1 vendor does not have and cannot build in a week.
- **Corsac Expert Network**: application → credential upload → qualification quiz → admin approval → timed harness → earnings. Four offerings sketched (custom eval creation, domain scoring, review queue, agent QA audit). Manus-built, working, no customers.
- **Calibration Arena**: a Bradley–Terry arena for professional work product with credential tiers, hidden gold-standard traps, a behavioral timing floor, weighted votes, company boards, and a release radar. Runs on seeded synthetic votes; sign-in codes show in the UI; live model generation is wired but keyless.

The honest observation: these are three surfaces for one thesis, and none has a paying customer or a verified panel. The missing piece is not a fourth surface. It is twenty-five real CPAs and one buyer.

---

## 3. Where your positioning actually sits

**The "accounting benchmark" lane is already occupied.** Mercor built APEX-Accounting with Ramp (160 tasks in 10 simulated worlds, expert-authored and rubric-graded; best model 56.4% Mean Criteria@3, no model above 21.5% Pass@8) ([arXiv](https://arxiv.org/abs/2607.27189)). Micro1 publishes Realm Financial (103 tasks: IFRS reconciliation workbooks, backtests, term sheets) and Realm Tax (full Form 1040 from source documents, 20+ criteria per task, 44% of criteria unsolved by any model) ([micro1](https://www.micro1.ai/benchmark/realm-tax)). AfterQuery has FinanceQA and SpreadsheetBench 2. Vals runs a finance-agent eval where frontier models fail 52% of tasks. Column Tax's TaxCalcBench and Rivet's TaxBench cover tax computation. Anyone you pitch "an accounting benchmark" to will name three of these.

**The "independent rating agency" lane is partly occupied by Vals**, which is a16z-backed, cited in model cards, and already ranks legal AI products. That overlaps with the arena's "vendor products on the board" story.

**What I could not find anyone doing:** publishing the calibration of the experts who graded the benchmark, shipping per-rater accuracy alongside the data, or running a public panel with an inspectable track record. Every vendor vets at the door (résumé, AI interview, sample task) and keeps quality signal internal. That gap is real. Two honest caveats:

1. It is a *quality-of-supply* differentiator. Whether a lab pays a premium for it, versus treating it as table stakes, is the single most important thing you have not tested.
2. The mechanic is copyable. Mercor could add trap items and a rater score in a quarter. The defensible part is the panel, its track record, and the task library, so speed to a real panel matters more than polish.

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

Cost estimate **[mine]**: 150 tasks × ~4 expert hours × $90 ≈ $54K, plus grading and review, ≈ $70–90K all-in. A 50-task pilot version is ≈ $25–30K. That is the number to fund from savings, a friends-and-family note, or a design partner's pilot fee.

### Weeks 4–12: sell to the buyer most likely to say yes, in this order

1. **Accounting-AI vendors** (Rillet is the warm one). Certified evaluation at $10–40K, private-first, publish on the board is their call. Fastest yes, smallest check, and it creates the "vendors compete here" story the arena needs.
2. **Tier-1 data vendors as a channel.** Mercor, Handshake, Micro1, and AfterQuery all run partner and white-label pools, and Handshake and xAI have publicly pivoted toward finance and health specialists. Offer calibrated CPA capacity as a subcontract, with calibration reports per batch. This is also the test for caveat 1 above: do they pay a premium for measured raters, or only a seat at the standard rate?
3. **Application-layer finance and legal AI, and post-training shops.** Legora buys from AfterQuery; Harvey published LAB; Applied Compute (customers include Harvey, Handshake, Mercor) needs expert task sets to run its RL stack on. These companies buy evals and task sets directly and are more reachable than a lab.
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
| T2 | Buyers value per-rater calibration metadata | Ask three human-data ops managers at Tier-1 vendors or labs whether it changes price or vendor choice | None will pay a premium → sell certified vendor evaluations only, and keep calibration as an internal QA tool |
| T3 | An accounting-AI vendor will pay ≥ $10K for a certified evaluation | Rillet first, then two cold vendors | Zero of three after a demo of a 50-task set |
| T4 | Corsac's pipeline can produce close tasks CPAs rate as realistic | Generate 50 worlds; have 5 CPAs rate realism | Under 80% rated "would see this at work" |
| T5 | You can float 30–60 days of expert payroll on a pilot | Model cash from the $25–30K pilot | Negative cash before the first invoice clears |

---

## 6. Naming and brand

No direct collision found for "Calibrated" in AI data. Adjacent names: Calibrate Ventures, Calibrate Group, Calibre Labs, and "Arena Calibrate" (a BI product at thearena.ai), which is close enough to "Calibration Arena" to be worth a trademark search. I did not check domain availability.

## 7. What the landing page claims, and what you must be able to defend

`landing/index.html` mirrors the AfterQuery/Micro1 skeleton (hero → trust strip → problem → offerings → verticals → loop → boards → two audiences → research → company → CTA) but is light, numerate, and shows the product, which the teardown says is exactly where both competitors are weak. Claims on it and their source:

- 870 eval packs, 15,600 graded cases: Corsac README.
- Five comparisons per session with one hidden trap; 80% trap floor; 1.5× and 2× vote weights: arena code and PRD.
- "94.1%" panel accuracy and reviewer names: illustrative, labeled as such on the page. Replace with real figures before you show a lab.
- "US-licensed reviewers," "two founding seats per vertical," "paid weekly": commitments, not facts yet. Make them true or take them down.
- Contact address is a placeholder (`hello@calibrated.co`) set in one constant at the bottom of the file.

---

## Appendix: research sources

AfterQuery: [BusinessWire Series A](https://www.businesswire.com/news/home/20260409469482/en/AfterQuery-Raises-$30-Million-Series-A-Round-at-$300-Million-Valuation) · [TechCrunch $3.2B](https://techcrunch.com/2026/09/01/afterquery-reportedly-becomes-y-combinators-fastest-ever-unicorn-now-valued-at-3-2b/) · [afterquery.com/products](https://www.afterquery.com/products). Micro1: [TechCrunch Aug 2026](https://techcrunch.com/2026/08/20/ai-data-startup-micro1-reaches-500m-gross-run-rate-amid-ai-training-boom/) · [Realm Tax](https://www.micro1.ai/benchmark/realm-tax) · [Realm Financial](https://www.micro1.ai/benchmark/realm-financial). Mercor: [Sacra](https://sacra.com/c/mercor/) · [Dealroom](https://dealroom.co/news/137121-mercor-doubles-to-2b-gross-revenue-run-rate-as-ai-labs-buy-expert-data/) · [APEX-Accounting](https://arxiv.org/abs/2607.27189) · [TechCrunch breach](https://techcrunch.com/2026/04/09/after-data-breach-10b-valued-startup-mercor-is-having-a-month) · [CPA listing $60–80/hr](https://himalayas.app/companies/work-mercor/jobs/accountant-upto-80-hr). Surge: [Contrary](https://research.contrary.com/company/surge-ai) · [Sacra](https://sacra.com/c/surge-ai/). Handshake: [Sacra](https://sacra.com/c/handshake/) · [AI Native GTM](https://ainativegtm.substack.com/p/how-handshake-reinvented-itself-for) · [Breaking Even review](https://breakingeven.online/blog/handshake-ai-review). Scale: [TechCrunch OpenAI drops Scale](https://techcrunch.com/2025/06/18/openai-drops-scale-ai-as-a-data-provider-following-meta-deal). Vals: [TechTimes](https://www.techtimes.com/articles/324479/20260814/vals-ai-raises-40m-a16z-frontier-models-fail-52-real-finance-analyst-tasks.htm). Benchmarks: [GDPval](https://openai.com/index/gdpval/) · [HealthBench](https://openai.com/index/healthbench/) · [Harvey LAB](https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark) · [TaxCalcBench](https://github.com/column-tax/tax-calc-bench) · [TaxBench](https://www.rivet.tax/taxbench). Rates: [Built In](https://builtin.com/articles/train-ai-side-hustle) · [Alignerr](https://breakingeven.online/blog/alignerr-review-2026) · [DataAnnotation accounting](https://www.dataannotation.tech/accounting). Market structure: [Wing VC](https://www.wing.vc/content/who-will-win-the-rl-environment-market--and-why) · [RL List](https://www.rl-list.com/).
