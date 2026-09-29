from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
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

    Base.metadata.create_all(bind=engine)
    _ensure_columns()


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
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        for table, cols in _COLUMN_BACKFILL.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            if not existing:
                continue
            for col, ddl in cols.items():
                if col not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
        account_tables = {
            row[0] for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "pilot_accounts" in account_tables:
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_accounts_clerk_user_id "
                "ON pilot_accounts (clerk_user_id)"
            )
