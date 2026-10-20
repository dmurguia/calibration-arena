from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# Isolated test database, created fresh per session.
_TEST_DB = BACKEND / "test_designarena.db"
# Set ARENA_TEST_DATABASE_URL to run the suite against a real Postgres
# (its tables are dropped at the start of the session).
_PG_URL = os.getenv("ARENA_TEST_DATABASE_URL", "")
os.environ["ARENA_DATABASE_URL"] = _PG_URL or f"sqlite:///{_TEST_DB}"

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    if _TEST_DB.exists():
        _TEST_DB.unlink()
    from app.db import Base, engine, init_db
    from app.main import app

    if _PG_URL:
        Base.metadata.drop_all(bind=engine)

    init_db()

    with TestClient(app) as c:
        yield c

    if _TEST_DB.exists():
        _TEST_DB.unlink()
