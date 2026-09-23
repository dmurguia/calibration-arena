#!/usr/bin/env bash
# Regenerate everything: worlds, runs, external benchmarks, metrics, report.
# Requires: Python 3.11+, git, and a logged-in `claude` CLI (Claude Code). No API keys.
# Resumable: completed runs are never re-run. Set BUDGET (list-price-equivalent USD) to cap spend.
set -euo pipefail
cd "$(dirname "$0")"
MODELS="claude-fable-5-1 claude-opus-5 claude-sonnet-5 claude-haiku-4-5-20251001"
BUDGET="${BUDGET:-300}"

[ -d .venv ] || python3.11 -m venv .venv
.venv/bin/pip install -q pydantic numpy lxml python-dotenv requests

# 1. Benchmark: deterministic worlds + tasks from seed 20260923
.venv/bin/python -m closebench.build
.venv/bin/python -m closebench.multiperiod build

# 2. CloseBench-mini runs (k=4) + multi-period stretch (k=2)
.venv/bin/python -m closebench.run --models $MODELS --k 4 --concurrency 4 --budget "$BUDGET"
.venv/bin/python -m closebench.multiperiod run --models $MODELS --k 2

# 3. External benchmarks at pinned commits (graded by each repo's own grader)
[ -d external/finbalance ] || { git clone -q https://github.com/Devansh1105/finbalance external/finbalance; git -C external/finbalance checkout -q a1062b7; }
[ -d external/tax-calc-bench ] || { git clone -q https://github.com/column-tax/tax-calc-bench external/tax-calc-bench; git -C external/tax-calc-bench checkout -q ee0e2ca; }
.venv/bin/python external/run_external.py finbalance --models $MODELS --n 60 --concurrency 3 --budget "$BUDGET"
.venv/bin/python external/run_external.py taxcalc --models $MODELS --concurrency 5 --budget "$BUDGET"

# 4. Grade (re-uses cached judge verdicts), aggregate, render
.venv/bin/python -m closebench.regrade
.venv/bin/python -m closebench.metrics
.venv/bin/python -m closebench.report
