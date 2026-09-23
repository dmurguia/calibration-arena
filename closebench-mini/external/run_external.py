"""Run external public benchmarks through the claude CLI (no tools), graded by each repo's own grader.

python external/run_external.py finbalance --models ... [--n 60]
python external/run_external.py taxcalc   --models ...
Per-item outputs: external/runs/<bench>/<model>/<item>.json (+ .cost.json). Resumable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "finbalance"))
sys.path.insert(0, os.path.join(HERE, "tax-calc-bench"))

from closebench.cli import claude_call  # noqa: E402

SYSTEM = "Follow the user's instructions exactly. Respond with your final answer only."
LOCK = threading.Lock()


def spent():
    from closebench.run import spent_usd
    return spent_usd()


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"), indent=1, default=str)
    os.replace(tmp, path)


def call_with_retry(prompt, model, timeout=1800):
    import time
    for attempt in range(4):
        res = claude_call(prompt, model=model, system=SYSTEM, timeout=timeout, safe_mode=True)
        if res.get("error_kind") in ("rate_limit", "overloaded", "api_error", "no_json"):
            time.sleep([30, 120, 600, 1200][attempt] if res.get("error_kind") == "rate_limit" else [15, 60, 180, 300][attempt])
            continue
        return res
    return res


# ------------------------------------------------------------------------------ FinBalance
def finbalance_items(n):
    """Stratified by difficulty level 1-5: per level, 8 standard + 4 negative-control records (n=60),
    seeded. (The repo's stratified_sample_records round-robins groups in file order and yields only
    standard records skewed to low difficulty, so we sample explicitly.)"""
    import random
    from finbalance.benchmark.dataset import load_records
    recs = load_records(os.path.join(HERE, "finbalance", "data", "main", "records.jsonl"))
    rng = random.Random(20260923)
    per = n // 5
    n_neg = per // 3
    out = []
    for lvl in range(1, 6):
        std = sorted([r for r in recs if r.difficulty_level == lvl and not r.expected_inconsistency], key=lambda r: r.record_id)
        neg = sorted([r for r in recs if r.difficulty_level == lvl and r.expected_inconsistency], key=lambda r: r.record_id)
        out += rng.sample(std, per - n_neg) + rng.sample(neg, n_neg)
    return out


def finbalance_one(model, rec, budget):
    from finbalance.benchmark.analysis import analyze_submission
    from finbalance.benchmark.parser import SubmissionParseError, parse_submission
    from finbalance.benchmark.prompt import build_prompt
    from finbalance.benchmark.runner import _empty_submission
    out = os.path.join(HERE, "runs", "finbalance", model, f"{rec.record_id}.json")
    if os.path.exists(out):
        return "cached"
    if spent() >= 0.9 * budget:
        return "budget"
    res = call_with_retry(build_prompt(rec), model)
    if res.get("is_error"):
        save(out.replace(".json", ".error.json"), res)
        return "error"
    text = res.get("result") or ""
    ok, err = False, ""
    parsed = _empty_submission()
    try:
        parsed, ok = parse_submission(text), True
    except SubmissionParseError as e:
        err = str(e)
    a = analyze_submission(rec, parsed, parse_success=ok)
    save(out.replace(".json", ".cost.json"), {k: res.get(k) for k in ("total_cost_usd", "usage", "modelUsage", "wall_s", "duration_ms")})
    save(out, {"record_id": rec.record_id, "industry": rec.industry, "difficulty_level": rec.difficulty_level,
               "period_type": rec.metadata.get("period_type"), "expected_inconsistency": rec.expected_inconsistency,
               "metrics": a["metrics"], "parse_success": ok, "parse_error": err, "response_text": text})
    return "done"


# ------------------------------------------------------------------------------ TaxCalcBench TY24
def taxcalc_items(_n):
    d = os.path.join(HERE, "tax-calc-bench", "tax_calc_bench", "ty24", "test_data")
    return sorted(os.listdir(d))


def taxcalc_one(model, case, budget):
    from tax_calc_bench.tax_return_evaluator import TaxReturnEvaluator
    from tax_calc_bench.ty24_prompt import TAX_RETURN_GENERATION_PROMPT
    out = os.path.join(HERE, "runs", "taxcalc_ty24", model, f"{case}.json")
    if os.path.exists(out):
        return "cached"
    if spent() >= 0.9 * budget:
        return "budget"
    d = os.path.join(HERE, "tax-calc-bench", "tax_calc_bench", "ty24", "test_data", case)
    prompt = TAX_RETURN_GENERATION_PROMPT.format(tax_year="2024", tool_use_hint="",
                                                 input_data=open(os.path.join(d, "input.json")).read())
    res = call_with_retry(prompt, model)
    if res.get("is_error"):
        save(out.replace(".json", ".error.json"), res)
        return "error"
    text = res.get("result") or ""
    ev = TaxReturnEvaluator().evaluate(text, open(os.path.join(d, "output.xml")).read(), tax_year="ty24")
    save(out.replace(".json", ".cost.json"), {k: res.get(k) for k in ("total_cost_usd", "usage", "modelUsage", "wall_s", "duration_ms")})
    save(out, {"case": case, "strictly_correct_return": ev.strictly_correct_return,
               "lenient_correct_return": ev.lenient_correct_return,
               "correct_by_line_score": ev.correct_by_line_score,
               "lenient_correct_by_line_score": ev.lenient_correct_by_line_score,
               "response_text": text})
    return "done"


BENCH = {"finbalance": (finbalance_items, finbalance_one, lambda r: r.record_id),
         "taxcalc": (taxcalc_items, taxcalc_one, lambda c: c)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench", choices=list(BENCH))
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--budget", type=float, default=300.0)
    a = ap.parse_args()
    items_fn, one_fn, key = BENCH[a.bench]
    items = items_fn(a.n)
    save(os.path.join(HERE, "runs", a.bench, "sample.json"), [key(i) for i in items])
    jobs = [(m, it) for it in items for m in a.models]
    print(f"{a.bench}: {len(items)} items x {len(a.models)} models", flush=True)
    counts = {}
    with ThreadPoolExecutor(a.concurrency) as ex:
        futs = [ex.submit(one_fn, m, it, a.budget) for m, it in jobs]
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception as e:
                r = f"exception:{type(e).__name__}:{e}"[:120]
            counts[r] = counts.get(r, 0) + 1
            with LOCK:
                print(counts, flush=True)
    print("final", counts, flush=True)


if __name__ == "__main__":
    main()
