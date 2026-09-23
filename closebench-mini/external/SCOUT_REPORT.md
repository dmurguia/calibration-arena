# Accounting benchmark scout report

Scouted 2026-09-23. I only read sources: I called no LLMs and spent no money. I used `curl` against the arXiv, Hugging Face, GitHub and raw.githubusercontent APIs and pages, plus shallow `git clone`. Every number below was read directly from the fetched source. Where I could not find something, it says NOT FOUND.

Local layout (all under `closebench-mini/external/`):

| Path | What | Size |
|---|---|---|
| `apex_accounting/` | Full HF `mercor/apex-accounting` dev set (120 files) | 4.1 MB |
| `apex_accounting/harbor/` | Text/code files of HF `mercor/apex-accounting-harbor` (the three docker image tarballs, 3.7 GB + 746 MB + 574 MB, were **not** downloaded) | 1.5 MB |
| `archipelago/` | Sparse clone of `Mercor-Intelligence/archipelago` @ `c7c6016`, with only `grading/runner/evals/output_llm`, `scoring_methods`, `main.py` and `utils/llm*` | small |
| `finbalance/` | Shallow clone of `Devansh1105/finbalance` @ `a1062b7` | 164 MB |
| `tax-calc-bench/` | Shallow clone of `column-tax/tax-calc-bench` @ `ee0e2ca` | 326 MB |

Note: `finbalance/`, `tax-calc-bench/` and `archipelago/` contain their own `.git` directories, so they are nested repos inside this worktree. You probably want to add `closebench-mini/external/*/` to `.gitignore` (or delete them) before committing.

---

## Summary: what can be run with a plain text prompt and no tools

| Benchmark | Public data? | Gated? | Grader | Text-only feasible? | Verdict |
|---|---|---|---|---|---|
| **FinBalance** | Yes, 710 main + 143 coverage records (plus a fresh-seed copy of each) | No | Deterministic Python (`analyze_submission`); **I checked it offline** | **Yes, natively.** Its prompts are already all text (OCR text inlined); p50 about 22k chars | **Best fit. Runnable today.** |
| **TaxCalcBench TY24** | Yes, 51 cases, JSON input | No | Deterministic Python (`TaxReturnEvaluator.evaluate`); **I checked it offline** | **Yes.** Input is JSON text | **Runnable today.** It is tax, not accounting |
| **TaxCalcBench TY25** | Yes, 50 cases, PDF input plus JSON | No | Same evaluator; I checked it offline against a saved Claude Opus 5.5 output | Partly. The official harness attaches the PDFs natively. `pdftotext` works but the layout is messy | Runnable. The text-only variant is a deviation from the official harness |
| **APEX-Accounting (dev)** | Yes, 10 tasks and 89 rubric criteria. The 160-task scored set is closed | No | LLM judge, one criterion at a time. The open-source template is in Archipelago; the leaderboard's template is not released | Only with caveats. Context is up to 440k tokens per task, and the harness is agentic | Runnable as a **text-stuffed variant** for about 4–5 tasks. Results are not comparable to the leaderboard |
| AuditBench (financial auditing) | Data only (GitHub JSON) | No | **NOT FOUND** (no grader code) | Yes (text tables) | Would need our own grader. The repo has no license |
| DualEntry Accounting AI Benchmark | **No** (questions not published) | n/a | Deterministic (per the page), not released | n/a | Scores are for reference only |
| Penrose AccountingBench | **No** (real company data) | n/a | Not released | n/a | Blog/experiment only |

---

## 1. APEX-Accounting (Mercor × Ramp)

### Paper
- https://arxiv.org/abs/2607.27189 **exists**. Title: "APEX-Accounting". Authors: Julien Benchek, Austin Bennett, Jasmin Kern, Ryan Stevens, Rene Sultan, Charis Ching, Hayley Popiel, Vaibhav Mittal, Felix Mercier, Brendan Foody, Bertie Vidgen. citation_date 2026/07/29, online 2026/07/30. The Comments field reads "Public dev set:" and links https://huggingface.co/datasets/mercor/apex-accounting.
- Numbers from the abstract: the private eval set has 160 tasks across 10 worlds. Claude-Fable-5 (Max) leads with 56.4% Mean Criteria@3, followed by Muse-Spark-1.1 (xHigh) at 52.6%. The best Pass^8 is 2.6% (GPT-5.6-Sol) and the best Pass@8 is 21.5%.

### Hugging Face searches
- `https://huggingface.co/api/datasets?search=apex&limit=50`, `search=accounting`, `author=mercor` and `search=mercor` all returned results. The relevant hits:
  - `mercor/apex-accounting`: gated **False**, license cc-by-4.0, lastModified 2026-07-31, 1476 downloads.
  - `mercor/apex-accounting-harbor`: gated **False**, cc-by-4.0, lastModified 2026-09-17. This is a runnable Harbor packaging of the same 10 tasks.
  - The other Mercor datasets (not accounting) are apex-agents (gated=auto), apex-agents-v1.1, APEX-SWE, ACE and APEX-v1-extended.
- I downloaded every file anonymously through `https://huggingface.co/datasets/mercor/apex-accounting/resolve/main/<path>`, with no login and no terms to accept.

### Dev split contents (`apex_accounting/`)
- `data/dev.jsonl` has 10 records with the fields `task_id, task_name, world_id, prompt, context_files[], rubric[{id, criterion_type, description}], gold_output, metadata{category, subcategory, output_type, world_entity_type, estimated_completion_hours, author_role, reviewer_role}`.
- `tasks/*.json` holds the same 10 records, pretty-printed.
- `world/`: one world, "World 9", Sterling, Marsh & Associates LLP, a Philadelphia law firm at its Dec-2024 close. It contains 90 files: 7 in `world/apps_data/quickbooks/` (CSV/XLSX QBO exports) and 83 in `world/filesystem/` (xlsx workpapers, CSV registers, PDF bank statements and invoices).
- `task_files/<task>/`: 16 task-specific files across 8 tasks (PDF, XLSX, TXT, CSV and one DOCX).
- Tasks: World 9 tasks 4, 5, 6, 7, 13, 14, 17, 23, 26 and 30. Categories are Reconciliation, Data Entry, Variance Analysis, and Schedules & Accruals. Every task has `output_type: console_text`, meaning the answer is a single final text message and no files are graded.
- Rubric criteria per task are 2/4/12/5/12/24/6/16/3/5, 89 in total. Each criterion is binary and states an exact value or an acceptable range. For example: "States the AR exposure for the Aging Bucket current is 72.80% (Acceptable value is 72.80%)".
- Every `context_files` entry resolves to a downloaded file. I checked all 10 tasks and none are missing.
- License: CC BY 4.0. The README notes that the dev world is the easiest of 11. The dev and held-out scores are not comparable, and the README says dev results "should not be reported as APEX-Accounting scores".
- The README's dev-set table (Mean Criteria@3) lists Claude-Fable-5 (Max) at 67.9%, GPT-5.6-Sol at 62.3% and Claude-Opus-4.8 (Max) at 61.8%, among others.

### Task format as the official harness runs it
- The harness is agentic. The model receives only `prompt`; it is **not** given the `context_files` list and has to find its own evidence. It works over MCP tools (filesystem, spreadsheets, PDFs, mail, code exec) rooted at `/filesystem`. Limits are 500 steps and 5M tokens.
- The accounting-software tool layer used on the leaderboard is not released. The QBO data ships only as static exports.
- Agent system prompt: `apex_accounting/harbor/agent/apex_accounting_loop_agent/apex_accounting_loop_agent.py`, `_AGENT_SYSTEM_PROMPTS["loop_agent"]`.

### Grader
- Leaderboard judge: **DeepSeek-v4-Flash at temperature 0.1**, with a GEPA-optimized template that is **not released**. It grades one criterion at a time from the task prompt, the criterion text and the model's final output. It never sees the trajectory, and it returns Met or Not Met.
- Open-source grader (Harbor edition): `harbor/tasks/<task>/tests/grade.py` runs the Archipelago `runner.main` with `eval_defn_id: "output_llm"`, and the scoring is `"template"`, a simple mean of the per-criterion 0/1 scores.
  - Default judge model: `vertex_ai/gemini-3-flash-preview`. You can override it with the env var `GRADING_MODEL`, which takes any LiteLLM model string.
  - Judge prompt source: `archipelago/grading/runner/evals/output_llm/utils/prompts.py`. The relevant constants are `GRADING_SYSTEM_PROMPT`, `STRICT_CRITERION_MATCHING`, `TOLERANCE_NOTES`, `GRADING_BASE_USER_PROMPT_TEMPLATE` and `JSON_OUTPUT_GRADING`. The expected output is JSON `{rationale, is_criteria_true}`.
  - Aggregation: `archipelago/grading/runner/scoring_methods/template/main.py`, which computes `final_score = mean(verifier scores)`.
- **The rubrics differ between the two releases.** The Harbor `tests/grading_config.json` rubrics are the source of record. Tasks 4, 5, 6, 7 and 17 differ from `data/dev.jsonl`: task 7 has new criterion IDs, task 6 accepts $49,500 or $48,000, and task 4's "one JE" criterion was reworded. Otherwise the differences are whitespace. **Use the Harbor `grading_config.json` rubrics.**
- Each task has a gold answer in `gold_output` (also in `harbor/tasks/*/tests/golden_reference.txt`). You can use it to sanity-check any judge, since it should score 100%.

### Converting to a no-tools, text-only test (our own variant, not official)
1. Build the prompt: an instruction preamble, then the task `prompt`, then the text of each file in `context_files`, each introduced by a `=== FILE: <name> ===` header.
   - Giving the model `context_files` leaks the author's file selection, which the official harness hides. Say so in any write-up.
   - The alternative is to include the whole world, but that is about 4.6M chars (about 1.15M tokens), which is not practical.
2. File conversion:
   - **PDF**: `pdftotext -layout` gives clean text. All of these PDFs are text PDFs; I checked bank statements, memos and the WIP schedule.
   - **CSV / TXT**: use as-is.
   - **DOCX**: unzip `word/document.xml` and strip the tags. The one DOCX, `Management Memo.docx`, is a short memo.
   - **XLSX**: convert every sheet to CSV or a markdown table. **Caution:** the workpapers contain formulas whose cached values are **empty** (for example `<f>SUM(C5:C36)</f><v></v>` in `workpaper_ar_aging_2024_12_31.xlsx` and `workpaper_payroll_accrual_2024_12_31.xlsx`). Either recalculate first (for example `soffice --headless --convert-to xlsx`, then read with openpyxl `data_only=True`), or render the formula text (`=SUM(C5:C36)`) so the model can compute it. A plain openpyxl `data_only=True` read will show blanks.
3. Approximate text size of each task's `context_files`, measured with my stdlib extractor (chars/4 is roughly tokens):

| Task | Approx. tokens | Notes |
|---|---|---|
| 30 (AR aging) | ~4k | fits easily |
| 23 (collections variance) | ~10k | fits |
| 7 (WIP rollforward) | ~14k | fits |
| 17 (payroll rec by group) | ~33k | fits |
| 4 (contingency JE) | ~230k | dominated by `qbo_journal_entry_register_2024.xlsx` (~890k chars) |
| 13, 14, 5, 6 | ~250–275k | dominated by `qbo_general_ledger_detail_2024.xlsx` (~950k chars) |
| 26 (partner true-up) | ~440k | dominated by `clio_time_entries_2024.csv` (1.7M chars) |

   Tasks 7, 17, 23 and 30 fit easily. Tasks 4, 5, 6, 13 and 14 need a model with a context window of 300k tokens or more. Task 26 needs about 450k. A no-tools model also has to do large aggregations over thousands of GL rows in its head, which is a very different test from the agentic one, where it gets code exec.
4. Grading with the benchmark's own grader. There are two options:
   - (a) Run `harbor/tasks/<task>/tests/grade.py` by wrapping the model's final text as the last assistant message of a minimal ATIF trajectory at `/logs/agent/trajectory.json`. See `tests/atif.py` for the format. This needs the Archipelago grading project installed (`GRADING_PROJECT`), or the `apex-verifier` docker image.
   - (b) Lighter: for each verifier in `grading_config.json`, call your judge with Archipelago's `output_llm` system and user prompts, filled with the task prompt, the criterion and the final answer. Then score = mean(is_criteria_true).
   - Either way the judge is an LLM, so it costs money, and the leaderboard's DeepSeek-v4-Flash template is unavailable.

---

## 2. FinBalance

### Paper and repo
- https://arxiv.org/abs/2606.15949 **exists**. Title: "FinBalance: A Multi-Document Accounting Reconciliation Benchmark". Authors: Tumpati, Agarwal, Kedia, Neekhra, Mandal, Garg, Sinha, Gupta, Kumar. Dated 2026-06-14. The Comments field says "Code and data: github.com/Devansh1105/finbalance". The README says it was accepted to EMNLP 2026 Findings.
- https://api.github.com/repos/Devansh1105/finbalance: exists, license Apache-2.0, created 2026-06-14, last pushed 2026-08-30. Data is CC BY 4.0 (`DATA_LICENSE.md`).
- The GitHub release `emnlp-2026-camera-ready` includes `finbalance-main-dataset-v1.tar.zst` (2.2 MB) and `finbalance-paper-results-v1.tar.zst` (9.0 MB, the saved model outputs). I did not download these; the data is already in the repo.

### Data
- `data/main/records.jsonl`: **710 records** (21 MB). `data/coverage/records.jsonl`: **143 records** (4.1 MB). There is also a `data/fresh_seed_20260712/{main,coverage}` copy (710/143) for a new-seed stability check. Each record also has rendered PDF assets under `assets/`, but they are not needed because OCR text is inlined.
- Main split composition:
  - Difficulty levels 1–5 have 106, 136, 126, 166 and 176 records.
  - 8 industries: professional_services 217, subscription_saas 102, wholesale_distribution 90, and 60–61 each for the rest.
  - Periods: month 290, quarter 210, year 210.
  - **480 standard records and 230 negative controls** (expected_inconsistency=true), covering 23 inconsistency codes.
  - Documents per record range from 5 to 52, with a mean of 19.
- Record fields: `record_id, industry, difficulty_level, period_start/end, opening_balance, allowed_accounts[], documents[{doc_id, doc_type, role, title, date, asset_path, ocr_text, metadata}], expected_entries[{doc_refs, debit_account, credit_account, amount, posting_date, label}], expected_balance_sheet{assets, liabilities, equity, totals, balanced}, expected_inconsistency, expected_inconsistency_codes, inconsistency_reasons, metadata`.
- Known issue from the README: 39 of the 710 frozen-v1 records have metadata quirks. The README says these move the headline metrics by at most 0.97 pp.

### Exact model input
- `finbalance/benchmark/prompt.py::build_prompt(record, prompt_variant="baseline", visibility_variant="normal")` returns a single plain-text string. It contains:
  - task rules (about 45 bullet lines),
  - record context (industry, difficulty, period, entity, currency, tax regime),
  - the allowed account names as JSON,
  - the allowed inconsistency codes as JSON with descriptions,
  - the output JSON shape and an example for an inconsistent packet,
  - then every document as `Document ID / Type / Title / OCR Text`.
- The documents' role labels (posting, support, distractor) are **not** shown to the model.
- Measured prompt lengths: main split min 12.6k, p50 22.0k, p90 33.2k and max 47.7k chars, which is about 3k–12k tokens. Coverage split: p50 21.3k and max 46.1k chars.
- Paper settings: temperature 0.0 and max_tokens 8192 (`runner.py`). There are no tools in the baseline.
- To dump a prompt from the repo root: `python -m finbalance prompt-preview --dataset data/coverage/records.jsonl --record-id COV_PRO_M1_0000`. A saved example is at `scratchpad/fb_prompt_example.txt`, outside the repo.

### Expected output
The model must return strict JSON with exactly these keys:
```json
{"has_inconsistency": false, "inconsistency_codes": [], "inconsistency_notes": [],
 "entries": [{"doc_refs": ["D003"], "debit_account": "...", "credit_account": "...", "amount": 1250.0}],
 "balance_sheet": {"assets": {}, "liabilities": {}, "equity": {}}}
```
- For an inconsistent packet: `has_inconsistency: true`, at least one allowed code, and empty entries and balance-sheet sections.
- The parser (`parser.py::parse_submission`) accepts a bare object, a fenced ```json block, or the first `{` to last `}`. It also strips thousands separators on retry.
- Parsing fails on an unknown inconsistency code or a non-numeric amount. A parse failure is scored as an empty submission.

### Grader (deterministic, no LLM)
- Entrypoint: `finbalance.benchmark.analysis.analyze_submission(record, parsed, parse_success=True, amount_tol=0.01, balance_tol=0.01)["metrics"]`. `scoring.py::score_submission` wraps it, and `summarize_results(results)` aggregates.
- **BS_exact** is `final_balance_sheet_matches`: the reported balance sheet equals the expected one, per account, within 0.01, ignoring zero lines.
- **BS_recon** is `predicted_entries_reconstruct_correct_final_balance_sheet`: replay the model's entries through `finbalance/ledger.py` from the opening balance, then compare.
- The summary rates (over the standard records only) are:
  - `final_balance_sheet_matches_rate` (BS_exact)
  - `predicted_entries_reconstruct_correct_final_balance_sheet_rate` (BS_recon)
  - `journal_entries_exact_record_match_rate` (entries including doc_refs)
  - `journal_entries_accounting_record_match_rate` (entries ignoring doc_refs)
  - `final_balance_sheet_and_journal_entries_match_rate` (the strict end-to-end metric)
- Over the negative controls: `inconsistency_flag_match_rate`, `inconsistency_code_match_rate` and `false_inconsistency_alarm_rate`.
- **I checked it offline** in a Python 3.11 venv with only pydantic, python-dotenv, requests and numpy, on coverage record `COV_PRO_M1_0000`:
  - Gold JSON: all metrics True.
  - Cash off by $5 in the reported balance sheet: BS_exact False, BS_recon True.
  - One wrong doc_ref: exact-entry match False, accounting match True, BS True.
- Paper baseline table (480 standard records in the main split; appendix `tab:no-gap-mechanism`):

| Model | BS_exact | BS_recon |
|---|---|---|
| Gemini 3 Flash | 0.235 | 0.548 |
| GPT-5 | 0.465 | 0.463 |
| Claude Haiku 4.5 | 0.029 | 0.292 |
| Grok-4.3 | 0.310 | 0.350 |
| DeepSeek Chat | 0.067 | 0.473 |
| Qwen 3 235B | 0.013 | 0.302 |

### How to run it with no tools (our own harness)
```python
# cwd = external/finbalance ; Python >= 3.11 ; pip install pydantic numpy python-dotenv requests
from finbalance.benchmark.dataset import load_records
from finbalance.benchmark.prompt import build_prompt
from finbalance.benchmark.parser import parse_submission, SubmissionParseError
from finbalance.benchmark.analysis import analyze_submission, summarize_results
recs = load_records("data/main/records.jsonl")          # or data/coverage/records.jsonl
results = []
for r in recs:
    prompt = build_prompt(r)                              # single user message, plain text
    text = call_model(prompt)                             # <-- your model call (temp 0, max_tokens >= 8192)
    try: parsed, ok = parse_submission(text), True
    except SubmissionParseError: parsed, ok = <empty ParsedSubmission>, False   # see runner.py::_empty_submission
    a = analyze_submission(r, parsed, parse_success=ok)
    results.append({"metrics": a["metrics"], "record_id": r.record_id, "industry": r.industry,
                    "difficulty_level": r.difficulty_level, "period_type": r.metadata.get("period_type")})
print(summarize_results(results))
```
- The official CLI (`python -m finbalance evaluate-openrouter ...` or `evaluate-ablations --backend openrouter|deepseek|gemini|vertex`) only calls those providers. It has no direct Anthropic backend, so use the loop above for Claude. OpenRouter slugs would also work.
- Package dependencies (`pyproject.toml`): matplotlib, numpy, pydantic, pydantic-ai, python-dotenv, requests. Only pydantic and numpy are needed for prompting and scoring. It requires Python 3.11 or newer; the system `python3` here is 3.9, but `/opt/homebrew/bin/python3.11` exists.
- No file attachments are needed.

---

## 3. APEX dev download
Done. The dev set is not gated and is 4.1 MB, well under 500 MB. See section 1. I skipped only the Harbor docker images (about 5 GB). You need those, and Docker plus `harbor==0.20.0`, only for the official agentic run.

---

## 4. Fallbacks

### TaxCalcBench (column-tax/tax-calc-bench)
- Repo: https://github.com/column-tax/tax-calc-bench. It exists, is MIT licensed, and was last pushed 2026-09-23. The paper is https://arxiv.org/abs/2507.16126 (I did not fetch its abs page). It requires Python 3.13 or newer; dependencies are google-genai, litellm, python-dotenv, lxml and numpy.
- **TY25 (default, v2):** 50 cases in `tax_calc_bench/ty25/test_data/`, 10 each for us, ca, il, ny and va.
  - Each case has `input/*.pdf` (W-2, 1099, prior-year 1040 and so on), `input/remaining_data.json` (question/answer pairs), and `output.xml` (expected e-file XML).
  - Prompt: `ty25_prompt.py::build_ty25_tax_return_prompt(jurisdiction, remaining_data_json, pdf_filenames)`. The PDFs are **attached natively** (base64 document blocks for Anthropic).
  - Output format: lines of the form `Line N: <desc> | <explanation> | <amount>`.
- **TY24 (v1):** 51 cases in `tax_calc_bench/ty24/test_data/<name>/`, with `input.json` (5–14 KB) and `output.xml`, federal 1040 only.
  - Prompt: the `ty24_prompt.py::TAX_RETURN_GENERATION_PROMPT` constant, used as `.format(input_data=...)`. **It is pure text, so it is ideal for no-tools.**
- Grader (deterministic):
  - Entrypoint: `tax_calc_bench.tax_return_evaluator.TaxReturnEvaluator().evaluate(generated_text, expected_xml, tax_year="ty25"|"ty24", jurisdiction="ca"|...)`. It returns `strictly_correct_return`, `lenient_correct_return` (every line within $5), `correct_by_line_score` and `lenient_correct_by_line_score`.
  - Offline re-scoring of saved outputs: `tax-calc-bench --quick-eval`.
  - **I checked it offline:** the saved `claude-opus-5-5` ultrathink output for ty25-ca-001 scores strict True and 100% by line. I imported only the evaluator, with lxml, on Python 3.11.
- Saved outputs for many models, Claude included, are in the repo under `ty25/results/` and `ty24/results/`.
- README leaderboard, TY25 strict / lenient (no tools):
  - Claude Opus 5.5: 38.00% / 48.00%
  - Claude Fable 5.1: 38.00% / 48.00%
  - Claude Opus 5: 20.00% / 30.00%
  - Claude Opus 4.8: 18.00% / 20.00%
  - Claude Sonnet 5: 6.00% / 10.00%
  - With web search, the top entry is GPT-6 Sol at 64.00% strict.
- For no-tools runs:
  - **TY24**: feed the prompt text as-is and grade with `evaluate(..., tax_year="ty24")`.
  - **TY25**: either attach the PDFs (the official method) or substitute `pdftotext -layout` output. I checked the W-2 and 1099-G: box values extract, but column layout is interleaved, for example box-12 "Code" letters stack vertically. Substituting text is a deviation from the official method.
- Caveat: this is individual income tax, not bookkeeping or close.

### AuditBench
- There is no public AuditBench for accounting on Hugging Face. Searching `search=auditbench` returns only unrelated alignment-auditing research datasets (PaulR11, djroytburg, asher577, PranavViswanath...).
- GitHub search found `Oppugno-Rushi/AuditBench-Benchmarking-LLMs-for-Financial-Auditing` ("AuditBench: A Benchmark for Large Language Models in Financial Statement Auditing", Wang et al., UIUC/Stevens, AI4Research workshop). Details:
  - 5 stars, last pushed 2025-03-08, **no license**.
  - It is data only: `Error_insertion/wrong_table_data.json` (1,484 records), `wrong_table_data_multiple_errors.json`, `Raw_table_data/` and `transaction_data/`.
  - Record fields: `Modified Financial Statement with Errors` (text table), `General Judgement` (Correct/Incorrect), `Error Identification` {Error Type, Problematic Entry row}, `Error Resolution` (prose), `Standards Citation`, `gt_table`, `gt_transaction_data`.
  - **Grader code: NOT FOUND.** The repo contains only JSON, PNG and README files.
  - It is text-only, so it is feedable, but you would have to write the scoring (exact match on judgement, error type and row; LLM judge for the resolution). I did not clone it.

---

## 5. Published leaderboards (reference only, not runnable)

### DualEntry Accounting AI Benchmark
- URL: https://www.dualentry.com/accounting-ai-benchmark. It returned 200, and `dualentry.com/...` redirects to `www`. The page is server-rendered, so the numbers are in the HTML.
- Title: "Accounting AI Benchmark 2026: AI Model Accuracy | DualEntry". Heading: "The 2026 Accounting AI Benchmark".
- **49 models** are listed. **Top score: Grok 4.5, 84.2%** (SpaceXAI, Closed).
- Claude entries, verbatim as "Model — Overall Accuracy":
  - Claude Fable 5 — 83.2%
  - Claude Opus 4.6 — 80.2%
  - Claude Opus 5.5 — 79.6%
  - Claude Opus 4.5 — 78.2%
  - Claude Fable 5.1 — 75.7%
  - Claude Sonnet 4.5 — 75.3%
  - Claude Opus 4.8 — 75.3%
  - Claude Sonnet 5 — 73.3%
  - Claude Opus 4.7 — 73.3%
  - Claude Opus 5 — 72.3%
  - Claude Haiku 4.5 — 70.3%
  - Claude Sonnet 4.6 — 70.3%
- Date: the page's JSON-LD says `datePublished`/`dateModified` "2026-02-20". That date is probably stale, because the list includes later models such as Opus 5.5. The HTTP `last-modified` header was the fetch time. There is no explicit "as of" date for the scores.
- Methodology (paraphrased):
  - The questions are task-oriented, not trivia, written against a provisioned chart of accounts with minimal context.
  - Each run happens in an isolated environment.
  - Grading is deterministic and binary.
  - Multiple runs are allowed, reporting accuracy and std per category and difficulty tier.
  - Agents may use tooling such as `delegate_to_record_draft`.
- Categories and question counts: Transaction Classification 13, Journal Entry Creation 13, Accounts Payable 13, Accounts Receivable 12, Bank Reconciliation 12, Financial Reporting 13, Month-End Close 12, AI Accounting Knowledge 13 (multiple-choice). That is 101 questions, which matches scores in steps of about 0.99%.
- Questions and grader: **NOT FOUND / not published.**

### Penrose AccountingBench
- `https://accountingbench.penrose.com` did not resolve (curl code 000). `https://penrose.com/accountingbench` returned 404. **`https://accounting.penrose.com` returned 200**, titled "Can LLMs Do Accounting? | Penrose".
- One-line description, from the page's own text in its JS bundle: AccountingBench measures whether models can "close the books" month by month for a real SaaS company, using a year of its real source data (Ramp, Rippling, Stripe, Mercury). The finding is that the strongest models match expert accountants in the first months, then accumulate compounding errors and produce incoherent results over longer horizons.
- The page is a JS-rendered SPA. The text I could read from the bundle mentions Claude 4 / Sonnet / Opus, Grok 4, o3, o4-mini and Gemini 2.5 Pro, which suggests it dates from 2025. **I did not extract numeric scores**: the charts are data-driven and I did not reverse-engineer the chart data.
- Dataset and grader: **NOT FOUND.** It is real company data, and the page does not link a public release.

---

## What worked and what failed (log)

**Worked:**
- arXiv abs pages for 2607.27189 and 2606.15949.
- HF API: search, dataset info, `tree/main?recursive=true`, and `resolve/main` downloads, all anonymous.
- GitHub API: repos, `git/trees`, releases and the search endpoint.
- Shallow and sparse `git clone`.
- DualEntry HTML scrape.
- Reading the Penrose static JS bundle.
- Offline grader checks for FinBalance and TaxCalcBench.

**Failed or not found:**
- `accountingbench.penrose.com` (no DNS or connection); `penrose.com/accountingbench` (404).
- Penrose numeric scores (not extracted).
- DualEntry questions and grader (not published).
- An AuditBench grader.
- The APEX leaderboard judge template (not released by Mercor).
- The first sparse-checkout attempt errored on a file path; I fixed it with `--no-cone`.

**Not attempted:**
- Downloading the APEX Harbor docker images (about 5 GB).
- The FinBalance release tarballs (the data is already in the repo).
- The TaxCalcBench arXiv abs page.
- The Mercor leaderboard page (https://www.mercor.com/apex/apex-accounting-leaderboard/).
