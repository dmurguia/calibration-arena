"""Build all task worlds and task JSONs deterministically from the seed.

python -m closebench.build [--seed 20260923]
Writes worlds/<task>/start.json, worlds/<task>/expected.json, tasks/<task>.json.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re

from .tasks_def import TASKS
from .world import DEFAULT_SEED, FX, build_base, r2, sub, world_stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def balances(world, entity, accounts, period_to="2026-03", period_from="0000-00"):
    tot = 0.0
    for e in world["entries"]:
        if e["entity"] != entity or not (period_from <= e["period"] <= period_to):
            continue
        for l in e["lines"]:
            if l["account"] in accounts:
                tot += l["debit"] - l["credit"]
    return r2(tot)


def computed_values(world, names):
    v = {}
    for acct in ("4000", "4100", "4200"):
        v[f"rev_US_{acct}"] = -balances(world, "US", {acct}, "2026-03", "2026-03")
    v["rev_US_total"] = r2(v["rev_US_4000"] + v["rev_US_4100"] + v["rev_US_4200"])
    v["gl_6200_q1"] = balances(world, "US", {"6200"}, "2026-03", "2026-01")
    v["deck_6200"] = r2(v["gl_6200_q1"] - 2800)
    # UK travel
    tot, by = 0.0, {}
    for e in world["entries"]:
        if e["entity"] == "UK" and e["period"] <= "2026-03":
            for l in e["lines"]:
                if l["account"] == "6300":
                    amt = l["debit"] - l["credit"]
                    tot += amt
                    m = e["memo"].split(" - ")[1] if e["memo"].startswith("Card - ") else e["memo"]
                    by[m] = by.get(m, 0) + amt
    v["uk_travel_q1"] = r2(tot)
    top = sorted(by.items(), key=lambda x: -x[1])
    v["uk_travel_top"], v["uk_travel_top_amt"] = top[0][0], r2(top[0][1])
    v["_uk_travel_margin"] = r2(top[0][1] - top[1][1])
    for ent in ("US", "UK", "DE"):
        v[f"cash_{ent}"] = balances(world, ent, {"1000", "1010", "1020"})
    v["cash_UK_usd"] = r2(v["cash_UK"] * FX["GBP"]["2026-03"])
    v["cash_DE_usd"] = r2(v["cash_DE"] * FX["EUR"]["2026-03"])
    v["cash_total_usd"] = r2(v["cash_US"] + v["cash_UK_usd"] + v["cash_DE_usd"])
    return {k: v[k] for k in names} | ({"_uk_travel_margin": v["_uk_travel_margin"]} if "uk_travel_top" in names else {})


def fmt_val(x):
    if isinstance(x, float):
        return f"{x:.2f}"
    return str(x)


def apply_expected(world, expected, keymap):
    w = copy.deepcopy(world)
    n = max(int(e["id"].split("-")[1]) for e in w["entries"])
    for i, ex in enumerate(expected, 1):
        w["entries"].append({"id": f"JE-EXP-{i:03d}", "entity": ex["entity"], "date": "2026-03-31",
                             "period": "2026-03", "memo": "expected", "agent": True,
                             "lines": [{"account": a, "debit": d, "credit": c} for a, d, c in ex["lines"]],
                             "support": [], "status": "posted"})
    return w


def flux_check(world):
    """Sanity: in T06b only the seeded lines may breach >10% and >$5,000 (US opex)."""
    out = {}
    for acct in [a["number"] for a in world["accounts"] if a["number"] >= "5000"]:
        f = balances(world, "US", {acct}, "2026-02", "2026-02")
        m = balances(world, "US", {acct}, "2026-03", "2026-03")
        if abs(m - f) > 5000 and (f == 0 or abs(m - f) / abs(f) > 0.10):
            out[acct] = (f, m)
    return out


def build(seed=DEFAULT_SEED, only=None):
    manifest = []
    for tid, fn in TASKS.items():
        if only and tid not in only:
            continue
        w = build_base(seed)
        spec = fn(w)
        world, keymap = w.finalize({"task_id": tid})
        # computed values need the finalized world; resolve {{v:...}} in docs as well
        vals = computed_values(world, spec.get("computed", []) + (["gl_6200_q1", "deck_6200"] if tid == "T08b" else []))
        vmap = {f"v:{k}": fmt_val(v) for k, v in vals.items()}
        if tid == "T08b":
            vmap["v:deck_6200"] = f"{vals['deck_6200']:,.2f}"
        full = {**keymap, **vmap}
        for d in world["documents"]:
            d["text"] = sub(d["text"], full)
        if tid == "T08b":
            vmap["v:deck_6200"] = fmt_val(vals["deck_6200"])
            full = {**keymap, **vmap}
        crit = []
        for c in spec["criteria"]:
            c2 = dict(c)
            c2["check"] = sub(c["check"], full)
            c2["description"] = sub(c["description"], full)
            assert "{{" not in c2["check"], (tid, c2["check"])
            crit.append(c2)
        expected_state = apply_expected(world, spec["expected"], keymap)
        os.makedirs(f"{ROOT}/worlds/{tid}", exist_ok=True)
        with open(f"{ROOT}/worlds/{tid}/start.json.tmp", "w") as f:
            json.dump(world, f, indent=1)
        os.replace(f"{ROOT}/worlds/{tid}/start.json.tmp", f"{ROOT}/worlds/{tid}/start.json")
        with open(f"{ROOT}/worlds/{tid}/expected.json", "w") as f:
            json.dump({"expected_entries": spec["expected"],
                       "optional_reversals": [keymap[k] for k in spec.get("optional_reversals", [])],
                       "computed_values": vals,
                       "expected_state_entries_added": expected_state["entries"][len(world["entries"]):]},
                      f, indent=1)
        task = {
            "id": tid, "area": spec["area"], "difficulty": spec.get("difficulty"),
            "instruction": spec["instruction"], "world_seed": seed,
            "starting_state_ref": f"worlds/{tid}/start.json",
            "expected_state_ref": f"worlds/{tid}/expected.json",
            "criteria": crit,
            "trap": spec["trap"] or {"present": False, "description": None},
            "plug_amounts": spec.get("plug_amounts", []),
            "tolerance": spec.get("tolerance", 0.01),
            "world_stats": world_stats(world),
            "world_sha256": hashlib.sha256(json.dumps(world, sort_keys=True).encode()).hexdigest()[:16],
        }
        with open(f"{ROOT}/tasks/{tid}.json.tmp", "w") as f:
            json.dump(task, f, indent=1)
        os.replace(f"{ROOT}/tasks/{tid}.json.tmp", f"{ROOT}/tasks/{tid}.json")
        n_words = len(spec["instruction"].split())
        manifest.append((tid, len(crit), sum(c["type"] == "deterministic" for c in crit),
                         bool(spec["trap"]), n_words, world_stats(world)))
        if tid == "T06b":
            fc = flux_check(world)
            assert set(fc) == {"5000", "6300", "6400"}, fc
        if tid == "T09a":
            assert vals["_uk_travel_margin"] > 50, vals
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    man = build(a.seed, a.only)
    tot = sum(m[1] for m in man)
    det = sum(m[2] for m in man)
    for m in man:
        print(m)
    print(f"tasks={len(man)} criteria={tot} deterministic={det} ({det / tot:.0%}) traps={sum(m[3] for m in man)}")
