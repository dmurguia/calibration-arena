"""Open, update or close one GitHub issue that flags broken benchmark sources.

Runs after every daily refresh and watchdog check. Problems are listed per
board with the fix location, the issue is assigned to the maintainer, and it
is closed automatically once a refresh comes back clean.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

import httpx

from pipeline.verify_benchmarks import health_errors

TITLE = "Benchmark pipeline needs attention"
LABEL = "benchmark-pipeline"
FIX_HINT = {
    "failed": "Inspect the evidence artifact. If the publisher moved, renamed or versioned the page, update `benchmarks/sources.json` "
              "(new URL, or `frozen` for an archived board plus a new entry for the successor). "
              "If the methodology text changed on purpose, approve the candidate in `benchmarks/refresh-approvals.json`.",
    "attention": "Set the board to `frozen` in `benchmarks/sources.json` and, if there is a successor, add it as a new board.",
}


def problems(report: dict | None, catalog: dict | None, now: datetime, job_status: str | None) -> list[dict]:
    found = []
    for bid, state in (report or {}).get("sources", {}).items():
        if state.get("status") == "failed":
            found.append({"board": bid, "kind": "failed", "detail": str(state.get("error", ""))[:300],
                          "last_good": state.get("last_successful_check")})
        elif state.get("attention"):
            found.append({"board": bid, "kind": "attention", "detail": state["attention"]})
    seen = {p["board"] for p in found}
    if catalog is not None:
        for error in health_errors(catalog, now):
            bid = error.split(":", 1)[0]
            if bid not in seen:
                found.append({"board": bid if ":" in error else None, "kind": "health", "detail": error})
    if job_status and job_status != "success" and not found:
        found.append({"board": None, "kind": "workflow", "detail": "A workflow step failed outside the source checks (tests, publication or browser verification)."})
    return found


def signature(found: list[dict]) -> str:
    return sha256(json.dumps(sorted((p["board"] or "", p["kind"]) for p in found)).encode()).hexdigest()[:16]


def body(found: list[dict], run_url: str | None) -> str:
    lines = ["The daily benchmark pipeline hit problems. Healthy boards were still published; broken boards keep their last verified data.", ""]
    for p in found:
        name = f"`{p['board']}`" if p["board"] else "Pipeline"
        line = f"- **{name}** ({p['kind']}): {p['detail']}"
        if p.get("last_good"):
            line += f" Last good check: {p['last_good']}."
        lines.append(line)
    hints = {p["kind"] for p in found} & FIX_HINT.keys()
    if hints:
        lines += ["", "**How to fix**"] + [f"- {kind}: {FIX_HINT[kind]}" for kind in sorted(hints)]
    if run_url:
        lines += ["", f"Run and evidence: {run_url}"]
    lines += ["", f"<!-- signature: {signature(found)} -->"]
    return "\n".join(lines)


def plan(existing: dict | None, found: list[dict], close: bool = True) -> str:
    """Return one of: none, create, update, close."""
    if found:
        if existing is None:
            return "create"
        old = re.search(r"<!-- signature: (\w+) -->", existing.get("body") or "")
        return "none" if old and old.group(1) == signature(found) else "update"
    return "close" if existing is not None and close else "none"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def sync_issue(repo: str, found: list[dict], run_url: str | None, assignee: str | None, close: bool) -> str:
    issues = json.loads(gh("issue", "list", "--repo", repo, "--label", LABEL, "--state", "open", "--json", "number,body", "--limit", "1"))
    existing = issues[0] if issues else None
    action = plan(existing, found, close)
    text = body(found, run_url) if found else ""
    if action == "create":
        gh("label", "create", LABEL, "--repo", repo, "--color", "B60205", "--description", "Benchmark source checks", "--force")
        args = ["issue", "create", "--repo", repo, "--title", TITLE, "--label", LABEL, "--body", text]
        gh(*args, *(["--assignee", assignee] if assignee else []))
    elif action == "update":
        number = str(existing["number"])
        gh("issue", "edit", number, "--repo", repo, "--body", text)
        gh("issue", "comment", number, "--repo", repo, "--body", "The set of broken boards changed:\n\n" + text.split("<!--")[0])
    elif action == "close":
        number = str(existing["number"])
        gh("issue", "close", number, "--repo", repo, "--comment", f"All benchmark sources checked clean. {run_url or ''}".strip())
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="evidence/report.json from the refresh")
    parser.add_argument("--catalog", type=Path, help="Published benchmarks.json; defaults to the public feed")
    parser.add_argument("--url", default="https://calibrationarena.ai/benchmark-feed/benchmarks.json")
    parser.add_argument("--job-status")
    parser.add_argument("--no-close", action="store_true", help="Only open or update; never close (watchdog)")
    args = parser.parse_args()
    report = json.loads(args.report.read_text()) if args.report and args.report.exists() else None
    try:
        catalog = json.loads(args.catalog.read_text()) if args.catalog else httpx.get(args.url, timeout=20, follow_redirects=True).json()
    except (OSError, ValueError, httpx.HTTPError) as exc:
        catalog = None
        report = report or {"sources": {}}
        report["sources"]["feed"] = {"status": "failed", "error": f"Published feed unavailable: {exc}"}
    found = problems(report, catalog, datetime.now(timezone.utc), args.job_status)
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_url = f"{os.environ['GITHUB_SERVER_URL']}/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}" if repo and os.environ.get("GITHUB_RUN_ID") else None
    summary = body(found, run_url) if found else "All benchmark sources checked clean."
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write(f"## Benchmark sources\n\n{summary}\n")
    print(summary)
    if repo and os.environ.get("GH_TOKEN"):
        print("issue:", sync_issue(repo, found, run_url, os.environ.get("ALERT_ASSIGNEE") or repo.split("/")[0], not args.no_close))


if __name__ == "__main__":
    main()
