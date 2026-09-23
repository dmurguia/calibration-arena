# CloseBench-mini v0

CloseBench-mini is an accounting-agent benchmark that grades **execution inside a ledger**, not artifacts about a frozen snapshot. Each task is delegated in a controller's voice to an agent that can act only through 15 ledger tools (MCP). The agent must explore a seeded synthetic company (US/UK/DE), post and reverse entries, attach support, request approvals, flag exceptions and submit a memo. Grading covers three dimensions: **outcome** (ledger state diff against ground truth), **auditability** (support, approvals, citations) and **integrity** (flag what cannot be supported; never plug).

**Results:** [`results/README.md`](results/README.md) (morning brief, tables, methodology, caveats, failure gallery) · [`results/index.html`](results/index.html) · [`results/results.json`](results/results.json) (every number).

## Layout

```
closebench/world.py        seeded world generator (company, CoA, Q1 ledger, bank, documents, policy)
closebench/tasks_def.py    24 task overlays (12 areas x 2), expected entries and criteria; 9 integrity traps
closebench/build.py        builds worlds/<task>/{start,expected}.json and tasks/<task>.json
closebench/tools.py        the 15 ledger tools (the agent's only interface)
closebench/mcp_server.py   stdio MCP server; logs every call to trace.jsonl; 60-call cap
closebench/grade.py        deterministic checks + fixed LLM judge (claude-sonnet-5)
closebench/run.py          runner via the `claude` CLI (resumable, retries, budget stop)
closebench/multiperiod.py  stretch: two sequential closes (April starts from the agent's March)
closebench/regrade.py      recompute all grades from disk (cached judge verdicts)
closebench/metrics.py      results.json: pass rates, Pass^k, integrity index, bootstrap CIs, judge_audit.csv
closebench/report.py       results/README.md and results/index.html
external/run_external.py   FinBalance and TaxCalcBench TY24 via the CLI, graded by each repo's own grader
runs/<model>/<task>/<k>/   trace.jsonl, final_state.json.gz, grade.json, cost.json, judge_*.json
```

## Reproduce

Requirements: Python 3.11+, git, and a logged-in [Claude Code](https://claude.com/claude-code) CLI (`claude`). No API keys are used.

```bash
./reproduce.sh
```

This one command rebuilds all worlds and tasks from seed `20260923`, runs 4 models × 24 tasks × k=4 plus the multi-period stretch, runs the external benchmarks at pinned commits, then regrades, aggregates and renders. It is resumable; set `BUDGET=<usd>` to cap list-price-equivalent spend (the runner stops launching at 90%).

To rebuild only the report from the committed runs, at no cost:

```bash
.venv/bin/python -m closebench.regrade && .venv/bin/python -m closebench.metrics && .venv/bin/python -m closebench.report
```

To add a model: `.venv/bin/python -m closebench.run --models <claude-model-id> --k 4`.

## Status

v0. It has 24 tasks on one synthetic company, has had no accounting-expert review, and used a single judge pass per verdict (a 30-verdict human audit sheet is in `results/judge_audit.csv`). See the Caveats section of `results/README.md` before citing any number.
