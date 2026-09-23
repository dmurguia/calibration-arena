"""Minimal MCP (JSON-RPC over stdio) server exposing the CloseBench tools.

Usage: python -m closebench.mcp_server --state RUN/state.json --trace RUN/trace.jsonl [--max-calls 60]
State is persisted after every mutating call; every call is appended to the trace.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from .tools import Ledger, ToolError, call, tool_schemas

MUTATING = {"post_journal_entry", "reverse_entry", "attach_support", "flag_exception",
            "request_approval", "match_bank_transaction", "mark_checklist_item", "submit_memo"}


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--trace", required=True)
    ap.add_argument("--max-calls", type=int, default=60)
    a = ap.parse_args()
    with open(a.state) as f:
        state = json.load(f)
    ledger = Ledger(state)
    n_calls = 0
    if os.path.exists(a.trace):
        with open(a.trace) as f:
            n_calls = sum(1 for line in f if '"type": "tool_call"' in line)

    def log(rec):
        with open(a.trace, "a") as f:
            f.write(json.dumps(rec) + "\n")

    out = sys.stdout
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue
        mid = msg.get("id")
        method = msg.get("method")
        if method == "initialize":
            res = {"protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
                   "capabilities": {"tools": {}},
                   "serverInfo": {"name": "closebench", "version": "0.1.0"}}
        elif method == "tools/list":
            res = {"tools": tool_schemas()}
        elif method == "ping":
            res = {}
        elif method == "tools/call":
            p = msg.get("params", {})
            name, args = p.get("name"), p.get("arguments") or {}
            n_calls += 1
            t0 = time.time()
            is_err = False
            if n_calls > a.max_calls and name != "submit_memo":
                payload = {"error": f"Tool-call budget of {a.max_calls} exhausted. Call submit_memo now."}
                is_err = True
            else:
                try:
                    payload = call(ledger, name, args)
                except ToolError as e:
                    payload = {"error": str(e)}
                    is_err = True
                except Exception as e:  # harness bug: surface, log, keep going
                    payload = {"error": f"internal error: {type(e).__name__}: {e}"}
                    is_err = True
                if name in MUTATING and not is_err:
                    write_json_atomic(a.state, state)
            log({"type": "tool_call", "n": n_calls, "ts": time.time(), "tool": name, "args": args,
                 "is_error": is_err, "result": payload, "ms": int((time.time() - t0) * 1000)})
            res = {"content": [{"type": "text", "text": json.dumps(payload, default=str)}],
                   "isError": is_err}
        elif mid is None:
            continue  # notification
        else:
            out.write(json.dumps({"jsonrpc": "2.0", "id": mid,
                                  "error": {"code": -32601, "message": f"unknown method {method}"}}) + "\n")
            out.flush()
            continue
        out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
