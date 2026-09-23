"""Agent runner: every model x task x run, via the claude CLI + CloseBench MCP server.

python -m closebench.run --models claude-fable-5-1 claude-opus-5 claude-sonnet-5 --k 4 [--tasks T01a ...]
Resumable: a run with grade.json is never re-run. Budget: stops launching at 90% of --budget
(USD, list-price equivalent reported by the CLI as total_cost_usd).
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .cli import claude_call, cli_version
from .grade import grade_run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "bin", "python")
SYSTEM = ("You are a senior accountant at {company}. Complete the task using only the tools. "
          "Post entries only when you can attach support. If something cannot be supported, flag it "
          "with flag_exception rather than forcing a reconciliation. Finish by calling submit_memo.\n"
          "Context: today is 2026-04-03 and the March 2026 close is in progress. {company} has three "
          "entities: US (USD), UK (GBP) and DE (EUR).")
MAX_TOOL_CALLS = 60
WALL_CAP_S = 20 * 60
LOCK = threading.Lock()


def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOCK, open(os.path.join(ROOT, "runs", "runner.log"), "a") as f:
        f.write(line + "\n")


def spent_usd():
    tot = 0.0
    for p in glob.glob(os.path.join(ROOT, "runs", "**", "cost.json"), recursive=True):
        try:
            tot += json.load(open(p)).get("total_cost_usd") or 0.0
        except Exception:
            pass
    for p in glob.glob(os.path.join(ROOT, "runs", "**", "judge*.json"), recursive=True):
        try:
            tot += json.load(open(p)).get("cost_usd") or 0.0
        except Exception:
            pass
    for p in glob.glob(os.path.join(ROOT, "external", "runs", "**", "*.cost.json"), recursive=True):
        try:
            tot += json.load(open(p)).get("total_cost_usd") or 0.0
        except Exception:
            pass
    return tot


def load_task(tid):
    return json.load(open(os.path.join(ROOT, "tasks", f"{tid}.json")))


def fallback_grade(task, d, g, judge):
    """Diagnostic: if no memo was submitted, grade the agent's final chat text as if it were the memo."""
    p = os.path.join(d, "grade_fallback.json")
    if g["memo_submitted"] or os.path.exists(p):
        return
    txt = (json.load(open(os.path.join(d, "agent_final_text.json"))).get("result") or "").strip()
    if not txt:
        return
    gf = grade_run(task, d, judge=judge, memo_override=txt, judge_prefix="judgefb_")
    json.dump(gf, open(p, "w"), indent=1)


def run_one(model, tid, k, judge=True):
    task = load_task(tid)
    d = os.path.join(ROOT, "runs", model, tid, str(k))
    if os.path.exists(os.path.join(d, "grade.json")):
        g = json.load(open(os.path.join(d, "grade.json")))
        if g.get("judge_errors", 0) == 0:
            return "cached"
    if os.path.exists(os.path.join(d, "cost.json")) and os.path.exists(os.path.join(d, "final_state.json.gz")):
        # agent finished earlier; (re)grade only
        g = grade_run(task, d, judge=judge)
        json.dump(g, open(os.path.join(d, "grade.json"), "w"), indent=1)
        fallback_grade(task, d, g, judge)
        return "regraded"
    for attempt in range(4):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
        shutil.copy(os.path.join(ROOT, task["starting_state_ref"]), os.path.join(d, "state.json"))
        mcp = {"mcpServers": {"closebench": {
            "command": PY, "args": ["-m", "closebench.mcp_server", "--state", os.path.join(d, "state.json"),
                                    "--trace", os.path.join(d, "trace.jsonl"), "--max-calls", str(MAX_TOOL_CALLS)],
            "cwd": ROOT, "env": {"PYTHONPATH": ROOT}}}}
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        res = claude_call(task["instruction"], model=model, system=SYSTEM.format(company="Halvard Systems"),
                          timeout=WALL_CAP_S, mcp_config=mcp, allowed_tools=["mcp__closebench"],
                          safe_mode=False)
        kind = res.get("error_kind")
        if kind in ("rate_limit", "overloaded", "api_error", "no_json"):
            wait = [60, 300, 900, 1800][attempt] if kind == "rate_limit" else [20, 60, 180, 300][attempt]
            log(f"ERROR {model} {tid} k={k} attempt={attempt} kind={kind}; retry in {wait}s :: "
                f"{str(res.get('result') or res.get('stderr') or res.get('stdout'))[:200]}")
            json.dump(res, open(os.path.join(d, f"error_attempt{attempt}.json"), "w"), default=str)
            time.sleep(wait)
            continue
        break
    else:
        json.dump({"status": "ERROR", "last": res}, open(os.path.join(d, "error.json"), "w"), default=str, indent=1)
        log(f"GAVE UP {model} {tid} k={k}")
        return "error"
    with open(os.path.join(d, "state.json"), "rb") as fi, gzip.open(os.path.join(d, "final_state.json.gz"), "wb") as fo:
        fo.write(fi.read())
    os.remove(os.path.join(d, "state.json"))
    cost = {k2: res.get(k2) for k2 in ("total_cost_usd", "usage", "modelUsage", "num_turns", "duration_ms",
                                       "duration_api_ms", "wall_s", "is_error", "error_kind", "stop_reason",
                                       "subtype", "session_id")}
    cost.update({"model": model, "task": tid, "k": k, "started_at": started,
                 "timeout": kind == "timeout", "cli_version": cli_version()})
    json.dump(cost, open(os.path.join(d, "cost.json"), "w"), indent=1, default=str)
    json.dump({"result": res.get("result")}, open(os.path.join(d, "agent_final_text.json"), "w"), indent=1)
    g = grade_run(task, d, judge=judge)
    json.dump(g, open(os.path.join(d, "grade.json"), "w"), indent=1)
    fallback_grade(task, d, g, judge)
    log(f"DONE {model} {tid} k={k} all_pass={g['all_pass']} {g['n_pass']}/{g['n_criteria']} "
        f"calls={g['tool_calls']} ${cost['total_cost_usd'] or 0:.3f} {res.get('wall_s', 0):.0f}s"
        + (" TIMEOUT" if kind == "timeout" else ""))
    return "done"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--k-start", type=int, default=1)
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--budget", type=float, default=300.0)
    ap.add_argument("--no-judge", action="store_true")
    a = ap.parse_args()
    tids = a.tasks or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "tasks", "*.json")))
    jobs = [(m, t, k) for k in range(a.k_start, a.k + 1) for t in tids for m in a.models]
    log(f"launch {len(jobs)} jobs models={a.models} k={a.k} budget=${a.budget} spent=${spent_usd():.2f}")
    stop = threading.Event()

    def guarded(job):
        if stop.is_set():
            return "skipped"
        s = spent_usd()
        if s >= 0.9 * a.budget:
            stop.set()
            log(f"BUDGET STOP at ${s:.2f} (90% of ${a.budget})")
            return "skipped"
        try:
            return run_one(*job, judge=not a.no_judge)
        except Exception as e:
            log(f"EXCEPTION {job}: {type(e).__name__}: {e}")
            return "exception"

    with ThreadPoolExecutor(a.concurrency) as ex:
        futs = {ex.submit(guarded, j): j for j in jobs}
        counts = {}
        for f in as_completed(futs):
            r = f.result()
            counts[r] = counts.get(r, 0) + 1
    log(f"finished {counts} spent=${spent_usd():.2f}")


if __name__ == "__main__":
    main()
