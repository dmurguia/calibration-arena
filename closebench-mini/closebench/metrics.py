"""Aggregate runs/ and external/runs/ into results/results.json (+ judge_audit.csv).

python -m closebench.metrics
Every number in the report is computed here from files on disk.
"""
from __future__ import annotations

import csv
import glob
import gzip
import json
import os
import random
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
B = 10_000
SEED = 20260923


def pct_ci(vals_by_task: dict, stat, B=B, seed=SEED):
    """95% percentile bootstrap over tasks. vals_by_task: task -> value(s); stat: list -> float."""
    tasks = sorted(vals_by_task)
    if not tasks:
        return None, None, None
    rng = random.Random(seed)
    point = stat([vals_by_task[t] for t in tasks])
    bs = []
    for _ in range(B):
        samp = [vals_by_task[rng.choice(tasks)] for _ in tasks]
        bs.append(stat(samp))
    bs.sort()
    return point, bs[int(0.025 * B)], bs[int(0.975 * B) - 1]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def load_runs(model):
    out = {}
    for d in sorted(glob.glob(os.path.join(ROOT, "runs", model, "T*", "*"))):
        tid, k = d.split(os.sep)[-2], int(d.split(os.sep)[-1])
        rec = {"task": tid, "k": k, "dir": d}
        if os.path.exists(os.path.join(d, "error.json")):
            rec["status"] = "ERROR"
        elif os.path.exists(os.path.join(d, "grade.json")) and os.path.exists(os.path.join(d, "cost.json")):
            rec["status"] = "OK"
            rec["grade"] = json.load(open(os.path.join(d, "grade.json")))
            rec["cost"] = json.load(open(os.path.join(d, "cost.json")))
            fb = os.path.join(d, "grade_fallback.json")
            rec["fallback"] = json.load(open(fb)) if os.path.exists(fb) else None
            rec["judge_cost"] = sum((json.load(open(p)).get("cost_usd") or 0)
                                    for p in glob.glob(os.path.join(d, "judge*.json")))
        else:
            rec["status"] = "INCOMPLETE"
        out.setdefault(tid, []).append(rec)
    return out


def det_all_pass(g):
    return all(c["pass"] for c in g["criteria"] if c["type"] == "deterministic")


def model_metrics(model, tasks_meta):
    runs = load_runs(model)
    ok = {t: [r for r in rs if r["status"] == "OK" and r["grade"]["all_pass"] is not None] for t, rs in runs.items()}
    ok = {t: v for t, v in ok.items() if v}
    n_err = sum(1 for rs in runs.values() for r in rs if r["status"] == "ERROR")
    n_judge_err = sum(1 for rs in runs.values() for r in rs if r["status"] == "OK" and r["grade"]["all_pass"] is None)
    all_runs = [r for v in ok.values() for r in v]
    if not all_runs:
        return {"model": model, "n_runs": 0, "errors": n_err}
    ks = [len(v) for v in ok.values()]
    kmax = max(ks)
    per_task_allpass = {t: [bool(r["grade"]["all_pass"]) for r in v] for t, v in ok.items()}
    per_task_crit = {t: [r["grade"]["n_pass"] / r["grade"]["n_criteria"] for r in v] for t, v in ok.items()}
    per_task_det = {t: [det_all_pass(r["grade"]) for r in v] for t, v in ok.items()}
    full_k = {t: v for t, v in per_task_allpass.items() if len(v) == kmax}

    m = {"model": model, "n_tasks": len(ok), "n_runs": len(all_runs), "k_max": kmax,
         "runs_per_task_min": min(ks), "errors": n_err, "judge_errors_unresolved": n_judge_err,
         "timeouts": sum(1 for r in all_runs if r["cost"].get("timeout")),
         "no_memo_runs": sum(1 for r in all_runs if not r["grade"]["memo_submitted"])}
    m["criteria_pass"] = pct_ci(per_task_crit, lambda s: mean(mean(x) for x in s))
    m["all_pass_at_1"] = pct_ci(per_task_allpass, lambda s: mean(mean(x) for x in s))
    m["pass_hat_k"] = pct_ci(full_k, lambda s: mean(all(x) for x in s))
    m["pass_hat_k_n_tasks"] = len(full_k)
    m["deterministic_only_all_pass_at_1"] = pct_ci(per_task_det, lambda s: mean(mean(x) for x in s))
    # fallback-memo diagnostic (final chat text graded as memo when submit_memo was never called)
    fb = {t: [bool((r["fallback"] or r["grade"])["all_pass"]) for r in v] for t, v in ok.items()}
    m["all_pass_at_1_if_final_text_counted_as_memo"] = pct_ci(fb, lambda s: mean(mean(x) for x in s))
    # integrity
    per_task_int = {t: [r["grade"]["integrity_clean"] for r in v] for t, v in ok.items()}
    m["close_integrity_index"] = pct_ci(per_task_int, lambda s: mean(mean(x) for x in s))
    m["unflagged_plug_entries"] = sum(1 for r in all_runs for p in r["grade"]["plug_entries"] if not p["flagged"])
    trap_tasks = [t for t in ok if tasks_meta[t]["trap"]["present"]]
    trap_runs = [r for t in trap_tasks for r in ok[t]]
    m["trap_runs"] = len(trap_runs)
    m["trap_flagged_runs"] = sum(1 for r in trap_runs if any(c["id"] == "I-flag" and c["pass"] for c in r["grade"]["criteria"]))
    m["trap_forced_runs"] = sum(1 for r in trap_runs if any(c["id"] in ("I-noplug", "I-nopost") and not c["pass"] for c in r["grade"]["criteria"]))
    for dim in ("outcome", "auditability", "integrity"):
        per = {t: [r["grade"]["dimension_all_pass"].get(dim, True) for r in v] for t, v in ok.items()}
        m[f"dim_{dim}"] = pct_ci(per, lambda s: mean(mean(x) for x in s))
    m["cost_per_task_usd"] = mean(r["cost"].get("total_cost_usd") or 0 for r in all_runs)
    m["judge_cost_per_task_usd"] = mean(r["judge_cost"] for r in all_runs)
    m["total_agent_cost_usd"] = sum(r["cost"].get("total_cost_usd") or 0 for r in all_runs)
    m["min_per_task"] = mean((r["cost"].get("wall_s") or 0) / 60 for r in all_runs)
    m["tool_calls_per_task"] = mean(r["grade"]["tool_calls"] for r in all_runs)
    m["per_task"] = {t: {"all_pass": per_task_allpass[t], "criteria_pass": [round(x, 3) for x in per_task_crit[t]]}
                     for t in sorted(ok)}
    # per-criterion failure counts
    fails = {}
    for r in all_runs:
        for c in r["grade"]["criteria"]:
            if not c["pass"]:
                key = f"{r['task']}:{c['id']}"
                fails[key] = fails.get(key, 0) + 1
    m["criterion_fail_counts"] = dict(sorted(fails.items(), key=lambda x: -x[1]))
    started = [r["cost"].get("started_at") for r in all_runs if r["cost"].get("started_at")]
    m["run_dates"] = [min(started)[:10], max(started)[:10]] if started else None
    m["cli_version"] = sorted({r["cost"].get("cli_version") for r in all_runs})
    return m


def finbalance_metrics(model):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "external", "finbalance"))
    files = [p for p in glob.glob(os.path.join(ROOT, "external", "runs", "finbalance", model, "*.json"))
             if not p.endswith((".cost.json", ".error.json"))]
    errs = glob.glob(os.path.join(ROOT, "external", "runs", "finbalance", model, "*.error.json"))
    if not files:
        return None
    from finbalance.benchmark.analysis import summarize_results
    res = [json.load(open(p)) for p in files]
    s = summarize_results(res)
    std = [r for r in res if not r["expected_inconsistency"]]
    neg = [r for r in res if r["expected_inconsistency"]]
    costs = [json.load(open(p.replace(".json", ".cost.json"))).get("total_cost_usd") or 0 for p in files]
    by_lvl = {}
    for r in std:
        by_lvl.setdefault(r["difficulty_level"], []).append(bool(r["metrics"].get("final_balance_sheet_matches")))
    return {"n": len(res), "n_standard": len(std), "n_negative": len(neg), "errors": len(errs),
            "BS_exact": s.get("final_balance_sheet_matches_rate"),
            "BS_recon": s.get("predicted_entries_reconstruct_correct_final_balance_sheet_rate"),
            "JE_accounting_match": s.get("journal_entries_accounting_record_match_rate"),
            "inconsistency_flag_match": s.get("inconsistency_flag_match_rate"),
            "parse_success": mean(r["parse_success"] for r in res),
            "BS_exact_by_difficulty": {k: round(mean(v), 3) for k, v in sorted(by_lvl.items())},
            "cost_per_item_usd": mean(costs), "summary_raw": s}


def taxcalc_metrics(model):
    files = [p for p in glob.glob(os.path.join(ROOT, "external", "runs", "taxcalc_ty24", model, "*.json"))
             if not p.endswith((".cost.json", ".error.json"))]
    errs = glob.glob(os.path.join(ROOT, "external", "runs", "taxcalc_ty24", model, "*.error.json"))
    if not files:
        return None
    res = [json.load(open(p)) for p in files]
    costs = [json.load(open(p.replace(".json", ".cost.json"))).get("total_cost_usd") or 0 for p in files]
    return {"n": len(res), "errors": len(errs),
            "strict_correct_return": mean(bool(r["strictly_correct_return"]) for r in res),
            "lenient_correct_return": mean(bool(r["lenient_correct_return"]) for r in res),
            "correct_by_line": mean(r["correct_by_line_score"] for r in res),
            "cost_per_item_usd": mean(costs)}


def judge_audit(models, n=30):
    rows = []
    for m in models:
        for p in sorted(glob.glob(os.path.join(ROOT, "runs", m, "T*", "*", "grade.json"))):
            g = json.load(open(p))
            d = os.path.dirname(p)
            for c in g["criteria"]:
                if c["type"] == "judge" and c.get("judge") and c["judge"].get("judge_model"):
                    rows.append({"model": m, "task": g["task_id"], "run": os.path.basename(d),
                                 "criterion_id": c["id"], "criterion": c["description"],
                                 "judge_verdict": c["judge"]["verdict"], "judge_rationale": c["judge"]["rationale"],
                                 "memo_file": os.path.relpath(os.path.join(d, "final_state.json.gz"), ROOT),
                                 "human_verdict": "", "human_notes": ""})
    rng = random.Random(SEED)
    # stratify: equal share per model, mix of PASS and FAIL
    out = []
    per = max(1, n // max(1, len(models)))
    for m in models:
        mr = [r for r in rows if r["model"] == m]
        rng.shuffle(mr)
        passes = [r for r in mr if r["judge_verdict"] == "PASS"]
        failsr = [r for r in mr if r["judge_verdict"] == "FAIL"]
        take = passes[: per // 2] + failsr[: per - per // 2]
        if len(take) < per:
            take += [r for r in mr if r not in take][: per - len(take)]
        out += take
    out = out[:n]
    for r in out:
        d = os.path.join(ROOT, os.path.dirname(r["memo_file"]))
        st = json.load(gzip.open(os.path.join(d, "final_state.json.gz")))
        r["memo_excerpt"] = (st.get("memo") or "(no memo)")[:1500]
    with open(os.path.join(RES, "judge_audit.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "task", "run", "criterion_id", "criterion", "judge_verdict",
                                          "judge_rationale", "memo_excerpt", "memo_file", "human_verdict", "human_notes"])
        w.writeheader()
        w.writerows(out)
    return len(out), len(rows)


def main():
    os.makedirs(RES, exist_ok=True)
    tasks_meta = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(ROOT, "tasks", "*.json"))}
    models = json.load(open(os.path.join(RES, "models_run.json")))["models"]
    crit = [c for t in tasks_meta.values() for c in t["criteria"]]
    out = {
        "benchmark": "CloseBench-mini v0",
        "n_tasks": len(tasks_meta), "n_criteria": len(crit),
        "n_deterministic": sum(c["type"] == "deterministic" for c in crit),
        "n_judge": sum(c["type"] == "judge" for c in crit),
        "n_trap_tasks": sum(t["trap"]["present"] for t in tasks_meta.values()),
        "criteria_by_dimension": {d: sum(c["dimension"] == d for c in crit) for d in ("outcome", "auditability", "integrity")},
        "bootstrap": {"B": B, "seed": SEED, "unit": "task"},
        "closebench": {m: model_metrics(m, tasks_meta) for m in [x["id"] for x in models]},
        "finbalance": {m["id"]: finbalance_metrics(m["id"]) for m in models},
        "taxcalc_ty24": {m["id"]: taxcalc_metrics(m["id"]) for m in models},
        "dualentry_reference": json.load(open(os.path.join(RES, "reference_published.json"))),
    }
    n_audit, n_judged = judge_audit([x["id"] for x in models])
    out["judge_audit"] = {"exported": n_audit, "judge_verdicts_total": n_judged}
    json.dump(out, open(os.path.join(RES, "results.json"), "w"), indent=1, default=str)
    print(json.dumps({m: {k: v for k, v in d.items() if k in ("n_runs", "all_pass_at_1", "pass_hat_k", "close_integrity_index", "cost_per_task_usd")}
                      for m, d in out["closebench"].items()}, indent=1, default=str))


if __name__ == "__main__":
    main()
