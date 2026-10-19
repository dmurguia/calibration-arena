"""Application configuration.

Every value can be overridden via environment variables (see .env.pilot.example).
Pilot-specific settings are read directly from the environment by the pilot_*
modules; inference credentials live in pilot_inference / pilot_direct.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def normalize_database_url(url: str) -> str:
    """Map the URLs Railway/Heroku hand out (postgres://, postgresql://) to the
    psycopg 3 driver SQLAlchemy should use. Other URLs pass through untouched."""
    url = url.strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def is_production_like() -> bool:
    return any(os.getenv(k) for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_PROJECT_ID"))


class Settings:
    def __init__(self) -> None:
        self.app_name = "Calibration Arena"
        # SQLite by default so the app runs with zero infra; swap for Postgres
        # by setting ARENA_DATABASE_URL=postgresql+psycopg://...
        self.database_url = normalize_database_url(
            os.getenv("ARENA_DATABASE_URL") or f"sqlite:///{BACKEND_DIR / 'arena.db'}"
        )
        # Session token signing secret. PLACEHOLDER — set a real secret in prod.
        self.secret_key = os.getenv("ARENA_SECRET_KEY", "dev-secret-change-me")
        self.session_ttl_seconds = int(os.getenv("ARENA_SESSION_TTL", str(60 * 60 * 24 * 30)))


@lru_cache
def get_settings() -> Settings:
    return Settings()
