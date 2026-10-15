# Benchmark reuse terms audit

Checked 2026-10-15 against the publisher pages cited in `benchmarks/registry.json` on the `/benchmarks` legibility branch (PR #26). This is a working note, not legal advice. Scores are facts and facts are weakly protected by copyright in the US, but site terms are contracts, compilations can carry selection-and-arrangement rights, and scraping clauses are enforced independently of copyright. Treat "link only" and "permission" below as the safe defaults until counsel says otherwise.

## What we do with each source

- **Board**: a publisher adapter copies the structured leaderboard (every model row) into `benchmarks/boards/*.json` and renders it as a ranked board.
- **Headline**: we copy one figure (leader, score, metric, date) into `results` and link to the source.
- **Link**: we list the benchmark and link out; no figure copied.

## Findings

| Publisher | We copy | Terms found | Risk | Action |
| --- | --- | --- | --- | --- |
| Vals AI (TaxEval v2, MortgageTax, Finance Agent v2, CorpFin v2, Vals Index) | 4 boards + headline | No website terms. Footer "All rights reserved". Methodology page: public validation sets are open, test sets "remain private at all times", a larger set is licensed to companies. No cite or reuse guidance. | Medium-high. Four of nine boards depend on one publisher with no stated permission. | Email Vals for written permission to mirror board rows with attribution. Until then keep boards unpublished or headline-only. |
| Mercor (APEX-Accounting, APEX-Agents IB) | 2 boards + headline | Terms of Service cover "the website(s), including www.mercor.com", which includes `/apex/`. §2.2 bars scrapers and data mining, §2.2(c) bars using site content for ML purposes, §2.2(e) and §4.2 bar reproducing, publishing or making derivative works of Mercor IP. No citation carve-out. APEX dev set is CC BY 4.0, but that covers the dataset, not the leaderboard page. | High for boards. | Request permission (Mercor sells "off-the-shelf data", so a listing with attribution is a reasonable ask). Interim: headline + link only. |
| Artificial Analysis (Finance & Accounting Index, GDPval-AA) | Headline | Website Terms of Use: license "solely for your own personal, noncommercial use"; no part may be "copied, reproduced, distributed, republished, downloaded"; scraping barred; "no implied licenses". Marks need written consent. | Medium for a single cited figure; high for anything structured. | Never build a board. Keep headline + link as citation. Consider asking for permission in writing, as the terms leave no safe harbour. |
| BenchLM (mirror used for Vals EMB) | Headline via mirror | CC BY-NC 4.0. "Commercial use, including redistributing the data or building a product on it, requires a license." Publisher measurements keep their own rights. | High as used: Calibration Arena is a commercial product. | Drop the mirror. Source EMB from Vals directly or mark `results_status: unknown`. |
| Rogo (BigFinanceBench) | Board + headline | No terms, license or copyright on the site. Dataset on Hugging Face, harness on GitHub, paper on arXiv. | Low-medium. | Check the Hugging Face dataset card and GitHub repo licenses; cite the paper. Email Rogo to confirm board mirroring is welcome. |
| DualEntry (Accounting AI Benchmark) | Board + headline | Enterprise Terms govern the paid product only. A separate "Website Terms of Use" is linked from the legal hub but the URL we tried returned 404. Vendor-run benchmark on private data. | Medium. | Find the website terms from the site footer, then ask. Keep the vendor-published flag. |
| Entendre (TaxBench) | Board + headline | Customer terms: no copying "any part of the Services", no derivative works of "our data", no aggregate data sets or indices from Entendre data, no disclosure of benchmarking analysis. Whether these bind a visitor to a research page is unclear. | Medium-high for a board. | Ask in writing. Interim: headline + link. |
| Ramp Labs (APEX-Accounting home, Ramp Accounting Bench) | Headline | `labs.ramp.com` pages carry no footer or terms; `ramp.com/legal` did not render. | Medium (unknown). | Locate Ramp's website terms and confirm they reach `labs.ramp.com`. |
| Digits (Beyond the Hype PDF) | Headline | Terms of Use: "You have no rights in or to the Content"; no retransmission without written consent "for each and every instance"; automated access barred; no quotation right stated. | Low-medium for one cited figure. | Headline + link only. Keep the vendor-report label. |
| Rillet (accounting agent benchmark post) | Headline | Terms bar scraping and copying of the Service (defined as the website). No reuse license, no citation clause. | Low-medium. | Headline + link only. |
| ChatCPA (AI accuracy page) | Headline | Content "owned by CHATCPA LLC"; no copying, scraping or derivative works; no attribution route. The acceptable-use policy covering "what we deliberately publish for free" was not reachable. | Low-medium. | Headline + link only; check the acceptable-use policy. |
| Handshake (BankerTool Bench) | Headline | Terms of Service cover the public site; no reuse license; crawling and bulk collection barred. Separate research terms exist. | Low. | Headline + link only. |
| Rivet (TaxBench) | Headline | Terms of Service are engagement terms; nothing on site content. | Low. | Headline + link. |
| Tax AI Consortium (TaxBench) | Headline | No terms; dataset linked on Hugging Face; submission portal exists. | Low. | Check the dataset license; cite. |
| Goodfin / NYU Stern (CFA Benchmark) | Headline | Page is script-rendered; no terms visible in the fetched HTML. | Low (unknown). | Re-check in a browser; cite. |
| IB-bench | Headline | "© 2026 IB-bench. All rights reserved." Methodology and rubrics open on GitHub, no license named. | Low. | Cite the GitHub repo. |
| FinanceBenchmark.ai (Avae) | Headline | No terms. Footer: "All benchmark scores attributed to their original publishers." It is itself an aggregator. | Low, but it is a mirror. | Prefer the primary publisher for each score; label `mirror` where used. |
| Agentic Accounting Index | Headline | No terms. Composite built from DualEntry, FinanceArena and Artificial Analysis. | Low, but it is a composite. | Label as composite; never treat its index as a publisher result. |
| AfterQuery (FinanceArena) | Headline | `financearena.ai` returned 404 on 2026-10-15. | n/a | Let `make benchmarks-check` flag it; set `archived` or `unknown`. |
| Meridian (BlueFin) | Headline | Blog URL returned 404 on 2026-10-15. | n/a | Same as above. |
| Academic sources (TAT-QA, SpreadsheetBench, FinMaster, Open FinLLM Leaderboard, Column Tax, FinTagging, XBRL-Agent, FinQA, ConvFinQA, FLUE, FinEval, FinGAIA, BizFinBench.v2, arXiv papers) | Headline | MIT, Apache-2.0, CC BY or standard academic publication. | Low. | Cite as normal; respect CC BY-NC on BizFinBench.v2 (no commercial reuse of the data itself; citing a score is fine). |

## Policy this implies

1. Three tiers in the registry: `open` (stated open license or academic publication: boards allowed), `cite_only` (no terms or restrictive terms: headline + link only), `permission_granted` (written OK on file: boards allowed, reference the email or agreement).
2. The build should refuse to emit a board for any benchmark that is not `open` or `permission_granted`.
3. Every board page shows "Mirrored with permission from <publisher>" or "Reproduced under <license>".
4. Mirrors and composites (BenchLM, FinanceBenchmark.ai, Agentic Accounting Index) are never the `results.source_url` when a primary source exists.
5. Re-run this audit when `make benchmarks-check` reports a changed hash on any terms URL; add terms URLs to `source-state.json` so they are tracked.

## Permission request template

Subject: Listing <benchmark> on Calibration Arena's public benchmark directory

We maintain a public directory of finance and accounting AI benchmarks at calibrationarena.ai/benchmarks. We would like to mirror your <benchmark> leaderboard as a per-model board, refreshed from your page, with your name, logo and a link on every view, and a note that the results are yours. We never re-score, combine or rank across benchmarks. May we have your permission to do so? If you would prefer a headline figure and link only, we will do that instead.
