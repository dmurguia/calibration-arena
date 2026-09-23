"""Recompute grade.json for every completed run from the current tasks/*.json.

Judge verdicts are cached per run (judge_<criterion>.json) and reused, so this only re-runs the
deterministic checks (plus any judge call that previously errored).
python -m closebench.regrade
"""
from __future__ import annotations

import glob
import json
import os

from .grade import grade_run
from .run import ROOT, fallback_grade, load_task


def main():
    n = changed = 0
    for d in sorted(glob.glob(os.path.join(ROOT, "runs", "*", "T*", "*"))):
        if not (os.path.exists(os.path.join(d, "cost.json")) and os.path.exists(os.path.join(d, "final_state.json.gz"))):
            continue
        task = load_task(d.split(os.sep)[-2])
        old = json.load(open(os.path.join(d, "grade.json"))) if os.path.exists(os.path.join(d, "grade.json")) else {}
        g = grade_run(task, d, judge=True)
        json.dump(g, open(os.path.join(d, "grade.json"), "w"), indent=1)
        fb = os.path.join(d, "grade_fallback.json")
        if os.path.exists(fb):
            os.remove(fb)
        fallback_grade(task, d, g, True)
        n += 1
        if old.get("all_pass") != g["all_pass"]:
            changed += 1
            print(f"changed {d.split('runs/')[1]}: {old.get('all_pass')} -> {g['all_pass']}")
    print(f"regraded {n} runs, all_pass changed in {changed}")


if __name__ == "__main__":
    main()
