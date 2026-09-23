"""Render results/README.md and results/index.html from results/results.json.

Hand-written sections (brief, surprises, failure gallery) live in results/_brief.md and
results/_gallery.md and are spliced in verbatim; every number in them must come from results.json
or a cited run file.
"""
from __future__ import annotations

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def p(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def ci(t):
    if not t or t[0] is None:
        return "n/a"
    return f"{100 * t[0]:.1f}% ({100 * t[1]:.0f}–{100 * t[2]:.0f})"


def money(x):
    return "n/a" if x is None else f"${x:.2f}"


def table1(r):
    hdr = ["Model (exact ID)", "Runs (tasks×k)", "Criteria pass", "All-pass@1", "Pass^k", "Close Integrity Index",
           "Outcome", "Auditability", "Integrity", "Det.-only all-pass@1", "Cost/task", "Min/task", "Errors"]
    rows = []
    for m, d in r["closebench"].items():
        if not d.get("n_runs"):
            rows.append([f"`{m}`", "0", *["n/a"] * 10, str(d.get("errors", 0))])
            continue
        rows.append([f"`{m}`", f"{d['n_runs']} ({d['n_tasks']}×{d['k_max']})", ci(d["criteria_pass"]), ci(d["all_pass_at_1"]),
                     f"{ci(d['pass_hat_k'])} [k={d['k_max']}, n={d['pass_hat_k_n_tasks']}]", ci(d["close_integrity_index"]),
                     ci(d["dim_outcome"]), ci(d["dim_auditability"]), ci(d["dim_integrity"]),
                     ci(d["deterministic_only_all_pass_at_1"]), money(d["cost_per_task_usd"]),
                     f"{d['min_per_task']:.1f}", f"{d['errors']} err / {d['timeouts']} timeout"])
    return hdr, rows


def table2(r):
    hdr = ["Model (exact ID)", "FinBalance BS_exact", "FinBalance BS_recon", "FinBalance inconsistency-flag match",
           "TaxCalcBench TY24 strict", "TaxCalcBench TY24 lenient (±$5)", "DualEntry overall (published, reference only)"]
    rows = []
    for m in r["closebench"]:
        fb, tc = r["finbalance"].get(m), r["taxcalc_ty24"].get(m)
        de = r["dualentry_reference"]["claude"].get(m)
        rows.append([f"`{m}`",
                     f"{p(fb['BS_exact'])} (n={fb['n_standard']})" if fb else "not run",
                     f"{p(fb['BS_recon'])} (n={fb['n_standard']})" if fb else "not run",
                     f"{p(fb['inconsistency_flag_match'])} (n={fb['n_negative']})" if fb else "not run",
                     f"{p(tc['strict_correct_return'])} (n={tc['n']})" if tc else "not run",
                     f"{p(tc['lenient_correct_return'])} (n={tc['n']})" if tc else "not run",
                     f"{de['overall_accuracy']}% (n=101, as \"{de['listed_as']}\")" if de else "not listed"])
    return hdr, rows


TABLE3 = (["Benchmark", "Task source", "Environment", "Grading", "Reliability metric", "Auditability graded?", "Governance"],
          [["CloseBench-mini v0 (this work)", "Synthetic, seeded generator (1 company, 3 entities)", "Live execution in a tool-exposed ledger (state changes)", "83% deterministic state-diff/trace checks; 17% LLM judge (claude-sonnet-5)", "Pass^k (k=4) + Close Integrity Index", "Yes (support attached, approvals, citations)", "Independent, single author; no expert review yet"],
           ["APEX-Accounting (Mercor × Ramp)", "Expert-authored tasks on realistic firm worlds", "Agentic over files/QBO exports (snapshot)", "LLM judge per rubric criterion", "Pass^8 / Pass@8 reported in paper", "No (final output only)", "Academic/vendor (Mercor); eval split private"],
           ["FinBalance", "Synthetic multi-document packets (710 main)", "Static prompt (documents inlined)", "Deterministic (balance sheet / entry replay)", "None (single run)", "Partly (doc_refs in entries)", "Academic (EMNLP 2026 Findings)"],
           ["DualEntry Accounting AI Benchmark", "Vendor-written, 101 questions", "Provisioned CoA; tool use allowed", "Deterministic binary (not published)", "Std over runs (per page)", "No", "Vendor-run; questions not public"],
           ["AccountingBench (Penrose)", "Real SaaS company books", "Multi-month close (live-ish)", "Not released", "Not reported", "Not public", "Vendor/blog; data private (reference only)"]])


def md_table(hdr, rows):
    out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def html_table(hdr, rows):
    def cell(c):
        s = html.escape(str(c)).replace("`", "")
        return s
    h = "<table><thead><tr>" + "".join(f"<th>{cell(x)}</th>" for x in hdr) + "</tr></thead><tbody>"
    for r in rows:
        h += "<tr>" + "".join(f"<td>{cell(c)}</td>" for c in r) + "</tr>"
    return h + "</tbody></table>"


def per_task_table(r):
    models = list(r["closebench"])
    tasks = sorted({t for d in r["closebench"].values() for t in d.get("per_task", {})})
    tm = {t: json.load(open(os.path.join(ROOT, "tasks", f"{t}.json"))) for t in tasks}
    hdr = ["Task", "Area", "Trap"] + [m for m in models]
    rows = []
    for t in tasks:
        row = [t, tm[t]["area"], "yes" if tm[t]["trap"]["present"] else ""]
        for m in models:
            v = r["closebench"][m].get("per_task", {}).get(t)
            row.append(f"{sum(v['all_pass'])}/{len(v['all_pass'])}" if v else "–")
        rows.append(row)
    return hdr, rows


def main():
    r = json.load(open(os.path.join(RES, "results.json")))
    brief = open(os.path.join(RES, "_brief.md")).read() if os.path.exists(os.path.join(RES, "_brief.md")) else "(brief pending)"
    gallery = open(os.path.join(RES, "_gallery.md")).read() if os.path.exists(os.path.join(RES, "_gallery.md")) else "(gallery pending)"
    method = open(os.path.join(RES, "_method.md")).read() if os.path.exists(os.path.join(RES, "_method.md")) else ""
    t1, t2, pt = table1(r), table2(r), per_task_table(r)
    md = f"""# CloseBench-mini v0 — results

{brief}

## Table 1 — CloseBench-mini v0 (24 tasks, execution-graded)

Rates are point estimates with 95% bootstrap CIs over tasks in parentheses (B={r['bootstrap']['B']}, seed {r['bootstrap']['seed']}).
All-pass@1 = mean over tasks of the per-task share of runs in which **every** criterion passed. Pass^k = share of tasks where **all k** runs all-passed.
Close Integrity Index = share of runs with zero unflagged plug/forced entries. Outcome/Auditability/Integrity = share of runs in which all criteria of that dimension passed.
"Det.-only" = all-pass@1 using only the {r['n_deterministic']} deterministic criteria (no judge). Cost = CLI-reported list-price-equivalent USD for the agent only (judge excluded).

{md_table(*t1)}

Per-task all-pass counts (runs all-passed / runs):

{md_table(*pt)}

## Table 2 — External public benchmarks (k=1) — different scales, do not compare across columns

{md_table(*t2)}

What these do **not** measure: FinBalance and TaxCalcBench are single-shot text-in/text-out — no execution inside a ledger, no auditability trail, no integrity traps, no Pass^k. DualEntry's questions and grader are unpublished and the numbers are vendor-reported (published by DualEntry, not reproduced here).

## Table 3 — What each benchmark measures

{md_table(*TABLE3)}

{method}

## Failure gallery

{gallery}
"""
    open(os.path.join(RES, "README.md"), "w").write(md)

    css = """
:root{--paper:#F4F1E9;--ink:#464643;--muted:#656460;--rule:#70543E;--line:#d9d4c7}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#F4F1E9;--ink:#464643;--muted:#656460}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 'IBM Plex Sans',system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:40px 16px 80px}
h1{font-weight:600;font-size:28px;margin:0 0 6px}.rule{height:1px;background:var(--rule);border:0;margin:0 0 28px}
h2{font-size:18px;font-weight:600;margin:40px 0 10px}p,li{max-width:80ch}.muted{color:var(--muted)}
.wrap{overflow-x:auto;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:12px}td{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:12.5px}
td:first-child{white-space:nowrap}
"""
    def mdish(s):
        out = []
        for line in s.splitlines():
            if line.startswith("- "):
                out.append(f"<li>{html.escape(line[2:])}</li>")
            elif line.strip():
                out.append(f"<p>{html.escape(line)}</p>")
        return "\n".join(out).replace("</li>\n<li>", "</li><li>")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CloseBench-mini v0 Results</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{css}</style></head><body><main>
<h1>CloseBench-mini v0 — results</h1><hr class="rule">
<p class="muted">24 execution-graded accounting tasks in a seeded synthetic ledger · Claude models via Claude Code CLI · run {html.escape(str(next(iter(r['closebench'].values())).get('run_dates')))} · every number from results/results.json</p>
<h2>Morning brief</h2><ul>{mdish(brief.split('## ')[0])}</ul>
<h2>Table 1 — CloseBench-mini v0</h2><p class="muted">95% bootstrap CIs over tasks in parentheses. Pass^k: all k runs must all-pass. Cost is list-price-equivalent USD reported by the CLI (agent only).</p>
<div class="wrap">{html_table(*t1)}</div>
<h2>Per-task all-pass counts</h2><div class="wrap">{html_table(*pt)}</div>
<h2>Table 2 — External public benchmarks (k=1)</h2><p class="muted">Different benchmarks, different scales — do not compare across columns. DualEntry numbers are published by DualEntry, not reproduced here.</p>
<div class="wrap">{html_table(*t2)}</div>
<h2>Table 3 — What each benchmark measures</h2><div class="wrap">{html_table(*TABLE3)}</div>
<p class="muted">Methodology, caveats, failure gallery and reproduction steps: results/README.md.</p>
</main></body></html>"""
    open(os.path.join(RES, "index.html"), "w").write(page)
    print("wrote README.md and index.html")


if __name__ == "__main__":
    main()
