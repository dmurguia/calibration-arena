"""Application configuration.

Every value can be overridden via environment variables. Placeholder values are
clearly marked so real credentials can be swapped in later (see .env.example).
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

        # Generation mode:
        #   sample — offline, deterministic-but-varied designs (default; no keys needed)
        #   live   — route each arena model to its provider adapter (requires API keys)
        self.generation_mode = os.getenv("ARENA_GENERATION_MODE", "sample")

        # PLACEHOLDER credentials for live providers. The adapters read these and
        # fail with a clear message until real keys are supplied.
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "PLACEHOLDER_ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "PLACEHOLDER_OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "PLACEHOLDER_GOOGLE_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "PLACEHOLDER_OPENROUTER_API_KEY")

        # PLACEHOLDER for a transactional email provider (magic-link/code emails).
        # In dev mode the login code is returned directly in the API response.
        self.email_provider_api_key = os.getenv("EMAIL_PROVIDER_API_KEY", "PLACEHOLDER_RESEND_OR_SENDGRID_KEY")
        self.dev_return_login_code = os.getenv("ARENA_DEV_LOGIN_CODE", "1") == "1"

        # How many models compete per battle (the tournament bracket assumes 4).
        self.models_per_battle = 4

        # Bootstrap resamples for leaderboard confidence intervals.
        self.ci_bootstrap_rounds = int(os.getenv("ARENA_CI_ROUNDS", "40"))

        # Behavioral floor: votes decided faster than this many ms are recorded
        # but excluded from published boards.
        self.min_decision_ms = int(os.getenv("ARENA_MIN_DECISION_MS", "4000"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
