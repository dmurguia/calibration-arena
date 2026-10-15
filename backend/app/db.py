from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings, is_production_like

log = logging.getLogger("arena.db")
settings = get_settings()
_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # Managed Postgres drops idle connections; check before handing one out.
    pool_pre_ping=not _is_sqlite,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  (register mappings)

    if _is_sqlite and is_production_like():
        log.warning(
            "!!! ARENA_DATABASE_URL is not set: using a SQLite file inside the container. "
            "Every account and run is WIPED on each redeploy. Set "
            "ARENA_DATABASE_URL=${{Postgres.DATABASE_URL}} on this Railway service. !!!"
        )
    log.info("Database backend: %s", engine.dialect.name)
    # create_all only issues CREATE for missing tables, so it is idempotent on
    # SQLite and Postgres alike.
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    _retire_models()


# Arena models cut from the roster after databases were already seeded.
# Deactivated rather than deleted: votes, generations and rating rows reference
# them by foreign key, so the history stays intact while match selection
# (active only) and leaderboard snapshots skip them. Idempotent.
RETIRED_MODEL_SLUGS: tuple[str, ...] = ("deepseek-v4", "grok-4-1", "qwen3-max", "mistral-large-3")


def _retire_models() -> None:
    from sqlalchemy import update

    from .models import ArenaModel

    with engine.begin() as conn:
        result = conn.execute(
            update(ArenaModel)
            .where(ArenaModel.slug.in_(RETIRED_MODEL_SLUGS), ArenaModel.active.is_(True))
            .values(active=False)
        )
        if result.rowcount:
            log.info("Deactivated %d retired arena models", result.rowcount)


# Columns added after a table already exists locally, which create_all cannot
# backfill. Prototype-grade migration — replace with Alembic when the schema
# starts moving for real.
_COLUMN_BACKFILL: dict[str, dict[str, str]] = {
    "arena_models": {
        "kind": "VARCHAR(20) NOT NULL DEFAULT 'foundation'",
        "vertical": "VARCHAR(40) NOT NULL DEFAULT ''",
        "provenance": "VARCHAR(40) NOT NULL DEFAULT ''",
        "submitted_version": "VARCHAR(60) NOT NULL DEFAULT ''",
    },
    "pilot_accounts": {
        "clerk_user_id": "VARCHAR",
    },
}


def _ensure_columns() -> None:
    with engine.begin() as conn:
        insp = inspect(conn)
        tables = set(insp.get_table_names())
        for table, cols in _COLUMN_BACKFILL.items():
            if table not in tables:
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for col, ddl in cols.items():
                if col not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
        if "pilot_accounts" in tables:
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_accounts_clerk_user_id "
                "ON pilot_accounts (clerk_user_id)"
            )
