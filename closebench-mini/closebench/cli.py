"""Thin wrapper over the `claude` CLI (subscription auth; no API keys).

All contestant and judge calls go through claude_call(). Built-in tools are disabled; the
only tools a contestant sees are the CloseBench MCP tools.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time

CLAUDE = os.environ.get("CLOSEBENCH_CLAUDE_BIN") or shutil.which("claude") or "claude"
# Neutral working dir so no project CLAUDE.md / settings are discovered.
NEUTRAL_CWD = os.path.join(tempfile.gettempdir(), "closebench-neutral")
os.makedirs(NEUTRAL_CWD, exist_ok=True)


def cli_version() -> str:
    try:
        return subprocess.run([CLAUDE, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return f"unknown ({e})"


def claude_call(prompt: str, model: str, system: str, effort: str | None = None,
                timeout: int = 1200, mcp_config: dict | None = None,
                allowed_tools: list[str] | None = None, safe_mode: bool = True) -> dict:
    args = [CLAUDE, "-p", "--no-session-persistence", "--output-format", "json",
            "--tools", "", "--strict-mcp-config",
            "--mcp-config", json.dumps(mcp_config or {"mcpServers": {}}),
            "--disable-slash-commands", "--permission-mode", "dontAsk",
            "--setting-sources", "", "--model", model, "--system-prompt", system]
    if safe_mode:
        args.insert(2, "--safe-mode")
    if effort:
        args += ["--effort", effort]
    if allowed_tools:
        args += ["--allowedTools", ",".join(allowed_tools)]
    t0 = time.time()
    try:
        p = subprocess.run(args, input=prompt, capture_output=True, text=True, timeout=timeout,
                           cwd=NEUTRAL_CWD)
    except subprocess.TimeoutExpired as e:
        return {"is_error": True, "error_kind": "timeout", "wall_s": time.time() - t0,
                "stderr": (e.stderr or "")[-2000:] if isinstance(e.stderr, str) else ""}
    wall = time.time() - t0
    out = (p.stdout or "").strip()
    try:
        d = json.loads(out.splitlines()[-1]) if out else {}
    except Exception:
        d = {}
    if not d:
        return {"is_error": True, "error_kind": "no_json", "wall_s": wall, "returncode": p.returncode,
                "stdout": out[-2000:], "stderr": (p.stderr or "")[-2000:]}
    d["wall_s"] = wall
    d["returncode"] = p.returncode
    if d.get("is_error"):
        txt = json.dumps(d).lower()
        d["error_kind"] = ("rate_limit" if ("rate" in txt and "limit" in txt) or "429" in txt or "usage limit" in txt
                           else "overloaded" if "overload" in txt or "529" in txt
                           else "api_error")
    return d
