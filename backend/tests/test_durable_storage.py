"""An account must survive the process (engine + app) being torn down and
rebuilt against the same database, which is what a Railway redeploy does."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.config import normalize_database_url

BACKEND = Path(__file__).resolve().parent.parent

_SCRIPT = r"""
import os, sys
from fastapi.testclient import TestClient
from app.main import app
from app.pilot_accounts import reset_limits
reset_limits()
email, step = "durable@example.com", sys.argv[1]
with TestClient(app) as c:
    if step == "signup":
        r = c.post("/api/pilot/auth/signup", json={"name": "Dura", "email": email, "password": "long-enough-password"})
    else:
        r = c.post("/api/pilot/auth/login", json={"email": email, "password": "long-enough-password"})
    assert r.status_code == 200, (step, r.status_code, r.text)
    assert c.get("/api/pilot/me", headers={"Authorization": "Bearer " + r.json()["token"]}).status_code == 200
print("ok", step)
"""


def _run(step: str, url: str) -> None:
    env = {**os.environ, "ARENA_DATABASE_URL": url}
    out = subprocess.run([sys.executable, "-c", _SCRIPT, step], cwd=BACKEND, env=env,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stdout + out.stderr


def test_account_survives_restart(tmp_path):
    url = os.getenv("ARENA_TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'durable.db'}"
    if os.getenv("ARENA_TEST_DATABASE_URL"):
        from sqlalchemy import create_engine, text
        eng = create_engine(normalize_database_url(url))
        with eng.begin() as conn:
            conn.execute(text("DELETE FROM pilot_accounts WHERE email = 'durable@example.com'"))
        eng.dispose()
    _run("signup", url)   # process 1: fresh engine, create schema, create account
    _run("login", url)    # process 2: brand-new engine/app, same DB, sign in


def test_normalize_database_url():
    assert normalize_database_url("postgres://u:p@h:5432/d") == "postgresql+psycopg://u:p@h:5432/d"
    assert normalize_database_url("postgresql://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    assert normalize_database_url("postgresql+psycopg://u@h/d") == "postgresql+psycopg://u@h/d"
    assert normalize_database_url("sqlite:///x.db") == "sqlite:///x.db"
