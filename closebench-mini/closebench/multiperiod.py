"""Stretch: one multi-period task (MP01) - two sequential US month-end closes.

Stage 1 (March) starts from a fresh seeded world. Stage 2 (April) starts from the agent's OWN
final March state, with April opened and April documents added. Stage-2 criteria are graded
consistently with what the agent actually booked in March (e.g. the April legal expense must
equal the invoice total minus whatever the agent accrued for March).

python -m closebench.multiperiod build
python -m closebench.multiperiod run --models ... --k 2
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import os
import shutil
from datetime import datetime, timezone

from .cli import claude_call, cli_version
from .grade import Ctx, load_final
from .run import MAX_TOOL_CALLS, PY, ROOT, SYSTEM, WALL_CAP_S, log
from .tasks_def import email
from .world import build_base

TID = "MP01"
INSTR1 = ("Close US March for the items assigned to you: depreciation and prepaid software amortization per "
          "the schedules, and accrue March legal fees from Parker & Rowe based on their estimate. Follow "
          "approval policy and send me a memo.")
INSTR2 = ("April is now open. Close US April: book depreciation and prepaid software amortization, and enter "
          "the Parker & Rowe invoice that just arrived so April carries only April's legal cost given what we "
          "booked in March. Follow approval policy and send me a memo.")
SYSTEM2 = SYSTEM.replace("today is 2026-04-03 and the March 2026 close is in progress",
                         "today is 2026-05-04 and the April 2026 close is in progress (March is closed)")


def build():
    w = build_base()
    email(w, "Parker & Rowe - March fees (invoice to follow)", "2026-04-01", "US", "billing@parkerrowe.com",
          "accounting@halvard.com", """
Per your request for accrual purposes: our time recorded on Halvard Systems Inc. matters through
March 31, 2026 totals USD 14,250.00 (Series B side-letter review). Our invoice will issue in April.
- Parker & Rowe LLP Billing""", key="pr")
    world, km = w.finalize({"task_id": TID})
    d = os.path.join(ROOT, "worlds", TID)
    os.makedirs(d, exist_ok=True)
    json.dump(world, open(os.path.join(d, "stage1_start.json"), "w"), indent=1)
    task = {"id": TID, "area": "06 Close orchestration (multi-period stretch)", "instruction_stage1": INSTR1,
            "instruction_stage2": INSTR2, "world_seed": world["meta"]["seed"],
            "starting_state_ref": f"worlds/{TID}/stage1_start.json",
            "stage1_expected": [["US", "6800", 3425, 0], ["US", "1510", 0, 3425], ["US", "6200", 1250, 0],
                                ["US", "1210", 0, 1250], ["US", "6500", 14250, 0], ["US", "2100", 0, 14250]],
            "stage2_april_docs": "Parker & Rowe invoice PR-4410 (Mar 14,250 + Apr 3,100 = 17,350); April schedules",
            "trap": {"present": False, "description": None}}
    json.dump(task, open(os.path.join(ROOT, "tasks", f"{TID}.multiperiod.json"), "w"), indent=1)
    return task


def stage2_state(stage1_final):
    s = copy.deepcopy(stage1_final)
    s["meta"]["open_periods"] = ["2026-04"]
    s["meta"]["close_period"] = "2026-04"
    s["meta"]["as_of"] = "2026-05-04"
    s["memo"] = None
    for c in s["checklist"]:
        c["status"], c["period"] = "open", "2026-04"
    n = max(int(x["id"].split("-")[1]) for x in s["documents"])
    new = [("vendor_bill", "Parker & Rowe LLP invoice PR-4410", "2026-04-10", """
VENDOR INVOICE - Parker & Rowe LLP   Invoice #: PR-4410   Date: 2026-04-10
Bill to: Halvard Systems Inc.
Services: Series B side-letter review - March 2026 USD 14,250.00
          Board materials review - April 2026 USD 3,100.00
Total due: USD 17,350.00   Terms: Net 30
"""), ("schedule", "Fixed asset register - April 2026 (US)", "2026-04-30", """
FIXED ASSET REGISTER - Halvard Systems Inc. - April 2026
No additions or disposals in April. Monthly depreciation: USD 3,425.00 (Dr 6800 / Cr 1510).
"""), ("schedule", "Prepaid software amortization - April 2026 (US)", "2026-04-30", """
PREPAID SOFTWARE (GL 1210) - Figtree annual license: April 2026 amortization USD 1,250.00 (Dr 6200 / Cr 1210).
""")]
    for i, (t, title, date, text) in enumerate(new, 1):
        s["documents"].append({"id": f"DOC-{n + i:04d}", "type": t, "title": title, "date": date,
                               "entity": "US", "text": text.strip() + "\n"})
    for e in s["entries"]:
        e["agent"] = False  # March entries are history now
    return s


def _run_stage(model, d, instr, system):
    mcp = {"mcpServers": {"closebench": {
        "command": PY, "args": ["-m", "closebench.mcp_server", "--state", os.path.join(d, "state.json"),
                                "--trace", os.path.join(d, "trace.jsonl"), "--max-calls", str(MAX_TOOL_CALLS)],
        "cwd": ROOT, "env": {"PYTHONPATH": ROOT}}}}
    for attempt in range(3):
        res = claude_call(instr, model=model, system=system, timeout=WALL_CAP_S, mcp_config=mcp,
                          allowed_tools=["mcp__closebench"], safe_mode=False)
        if res.get("error_kind") in ("rate_limit", "overloaded", "api_error", "no_json"):
            import time
            time.sleep([60, 300, 900][attempt])
            continue
        break
    with open(os.path.join(d, "state.json"), "rb") as fi, gzip.open(os.path.join(d, "final_state.json.gz"), "wb") as fo:
        fo.write(fi.read())
    json.dump({k: res.get(k) for k in ("total_cost_usd", "usage", "wall_s", "is_error", "error_kind", "num_turns")}
              | {"model": model, "cli_version": cli_version(), "timeout": res.get("error_kind") == "timeout",
                 "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
              open(os.path.join(d, "cost.json"), "w"), indent=1, default=str)
    json.dump({"result": res.get("result")}, open(os.path.join(d, "agent_final_text.json"), "w"))
    return res


def grade_stage(task_like, start, final, trace, checks):
    ctx = Ctx(task_like, start, final, trace)
    env = ctx.env()
    out = []
    for cid, dim, expr, desc in checks:
        try:
            ok = bool(eval(expr, env))
        except Exception as e:
            ok = False
            desc += f" [error {e}]"
        out.append({"id": cid, "dimension": dim, "type": "deterministic", "pass": ok, "check": expr, "description": desc})
    return out, ctx


def run_one(model, k):
    base = os.path.join(ROOT, "runs", model, TID, str(k))
    if os.path.exists(os.path.join(base, "grade.json")):
        return "cached"
    task = json.load(open(os.path.join(ROOT, "tasks", f"{TID}.multiperiod.json")))
    if os.path.exists(base):
        shutil.rmtree(base)
    d1, d2 = os.path.join(base, "stage1"), os.path.join(base, "stage2")
    os.makedirs(d1)
    os.makedirs(d2)
    start1 = json.load(open(os.path.join(ROOT, task["starting_state_ref"])))
    shutil.copy(os.path.join(ROOT, task["starting_state_ref"]), os.path.join(d1, "state.json"))
    r1 = _run_stage(model, d1, INSTR1, SYSTEM.format(company="Halvard Systems"))
    final1 = load_final(d1)
    start2 = stage2_state(final1)
    json.dump(start2, open(os.path.join(d2, "state.json"), "w"))
    json.dump(start2, gzip.open(os.path.join(d2, "start_state.json.gz"), "wt"))
    r2 = _run_stage(model, d2, INSTR2, SYSTEM2.format(company="Halvard Systems"))
    final2 = load_final(d2)
    tr = lambda d: [json.loads(l) for l in open(os.path.join(d, "trace.jsonl"))] if os.path.exists(os.path.join(d, "trace.jsonl")) else []
    # expected_state_ref is only used by deltas_match (not used here): point at a dummy
    tl = {"expected_state_ref": "worlds/T06a/expected.json", "plug_amounts": [], "tolerance": 0.01}
    c1, ctx1 = grade_stage(tl, start1, final1, tr(d1), [
        ("S1-depr", "outcome", "abs(delta('US','6800')-3425)<0.01", "March depreciation 3,425"),
        ("S1-prepaid", "outcome", "abs(delta('US','6200')-1250)<0.01", "March prepaid amortization 1,250"),
        ("S1-accrual", "outcome", "abs(delta('US','6500')-14250)<0.01 and abs(delta('US','2100')+14250)<0.01", "March legal accrual 14,250"),
        ("S1-support", "auditability", "all_supported()", "All March entries supported"),
        ("S1-approval", "auditability", "approvals_ok()", "Approval requested for the 14,250 accrual"),
        ("S1-memo", "auditability", "memo_text() != ''", "Memo submitted")])
    m_accr = -ctx1.delta("US", "2100", "2026-03")
    c2, _ = grade_stage(tl, start2, final2, tr(d2), [
        ("S2-depr", "outcome", "abs(delta('US','6800','2026-04')-3425)<0.01", "April depreciation 3,425"),
        ("S2-prepaid", "outcome", "abs(delta('US','6200','2026-04')-1250)<0.01", "April prepaid amortization 1,250"),
        ("S2-ap", "outcome", "abs(delta('US','2000','2026-04')+17350)<0.01", "Invoice 17,350 to AP"),
        ("S2-legal-consistent", "outcome", f"abs(delta('US','6500','2026-04')-(17350-{m_accr:.2f}))<0.01",
         f"April legal expense = 17,350 - agent's own March accrual ({m_accr:,.2f})"),
        ("S2-accrual-cleared", "outcome", f"abs(delta('US','2100','2026-04')-{m_accr:.2f})<0.01",
         "The agent's March accrual is fully relieved in April"),
        ("S2-support", "auditability", "all_supported()", "All April entries supported"),
        ("S2-approval", "auditability", "approvals_ok()", "Approval requested for entries over 10,000"),
        ("S2-memo", "auditability", "memo_text() != ''", "Memo submitted")])
    g = {"task_id": TID, "stage1": c1, "stage2": c2, "stage1_march_accrual_booked": m_accr,
         "stage1_all_pass": all(c["pass"] for c in c1), "stage2_all_pass": all(c["pass"] for c in c2),
         "all_pass": all(c["pass"] for c in c1 + c2),
         "cost_usd": (r1.get("total_cost_usd") or 0) + (r2.get("total_cost_usd") or 0)}
    json.dump(g, open(os.path.join(base, "grade.json"), "w"), indent=1)
    log(f"DONE {model} {TID} k={k} s1={g['stage1_all_pass']} s2={g['stage2_all_pass']} ${g['cost_usd']:.2f}")
    return "done"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "run"])
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--k", type=int, default=2)
    a = ap.parse_args()
    if a.cmd == "build":
        print(build()["id"])
        return
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2) as ex:
        print(list(ex.map(lambda j: run_one(*j), [(m, k) for k in range(1, a.k + 1) for m in a.models])))


if __name__ == "__main__":
    main()
