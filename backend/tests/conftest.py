from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# Isolated test database, created fresh per session.
_TEST_DB = BACKEND / "test_designarena.db"
os.environ["ARENA_DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["ARENA_GENERATION_MODE"] = "sample"
os.environ["ARENA_LEGACY_API"] = "1"
# Tests vote instantly; disable the behavioral timing floor.
os.environ["ARENA_MIN_DECISION_MS"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    if _TEST_DB.exists():
        _TEST_DB.unlink()
    from app.db import SessionLocal, init_db
    from app.main import app
    from pipeline.seed import seed_models

    init_db()
    db = SessionLocal()
    try:
        seed_models(db)
    finally:
        db.close()

    with TestClient(app) as c:
        yield c

    if _TEST_DB.exists():
        _TEST_DB.unlink()


@pytest.fixture()
def auth_client(client):
    resp = client.post("/api/auth/request-code", json={"email": "tester@example.com"})
    code = resp.json()["dev_code"]
    resp = client.post("/api/auth/verify", json={"email": "tester@example.com", "code": code})
    token = resp.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)
    client.cookies.clear()
