"""Launch spend safety: explicit configurable limits, per-request budget
reservations, bounded concurrent generations and a generation pause switch.

A reservation is written before any provider call so in-flight spend counts
toward budgets immediately. When a provider reports usage it reconciles to
zero (the usage rows carry the truth); when usage is missing the full
reservation keeps counting — unknown cost is never recorded as zero.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, String, func, select
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .pilot_accounts import PilotAccount, PilotUsage
from .pilot_usage import usage_tokens


class PilotReservation(Base):
    __tablename__ = "pilot_reservations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    participant_id: Mapped[str] = mapped_column(String, index=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    reserved_tokens: Mapped[int] = mapped_column(Integer)
    counted_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String)  # active | reconciled | expired
    created_at: Mapped[str] = mapped_column(String)
    reconciled_at: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)


class PilotFlag(Base):
    __tablename__ = "pilot_flags"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(String, nullable=True)


def _now():
    return datetime.now(timezone.utc)


def _iso():
    return _now().isoformat()


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def participant_budget(account):
    if account and account.token_budget is not None:
        return account.token_budget
    if account:
        return _env_int("PILOT_TOKEN_BUDGET", 2000000)
    return _env_int("PILOT_GUEST_TOKEN_BUDGET", 30000)


def global_daily_tokens():
    return _env_int("PILOT_GLOBAL_DAILY_TOKENS", 3000000)


def daily_run_limit():
    return _env_int("PILOT_DAILY_RUN_LIMIT", 100)


def max_concurrent_generations():
    return _env_int("PILOT_MAX_CONCURRENT_GENERATIONS", 4)


def max_concurrent_per_participant():
    return _env_int("PILOT_MAX_CONCURRENT_PER_PARTICIPANT", 1)


def generation_timeout_seconds():
    return _env_int("PILOT_GENERATION_TIMEOUT_SECONDS", 150)


def reservation_ttl_seconds():
    return _env_int("PILOT_RESERVATION_TTL_SECONDS", generation_timeout_seconds() + 300)


def estimate_tokens(chars):
    return max(1, chars // 4)


def reservation_tokens(prompt, histories=None):
    """Conservative spend held while a generation is in flight: both model
    calls' estimated input plus the configured output ceiling for each."""
    total_chars = len(prompt)
    if isinstance(histories, dict):
        total_chars += max((sum(len(m.get("content", "")) for m in h) for h in histories.values()), default=0)
    elif isinstance(histories, list):
        total_chars += sum(len(m.get("content", "")) for m in histories)
    return 2 * (estimate_tokens(total_chars) + _env_int("PILOT_MAX_OUTPUT_TOKENS", 2000))


class LimitRejected(Exception):
    def __init__(self, detail, status_code):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def env_paused():
    return os.getenv("PILOT_GENERATION_PAUSED") == "1"


def flag_paused(db):
    row = db.get(PilotFlag, "generation_paused")
    return bool(row and row.value == "1")


def paused(db):
    return env_paused() or flag_paused(db)


def set_paused(db, value, note=None):
    row = db.get(PilotFlag, "generation_paused")
    if row is None:
        row = PilotFlag(key="generation_paused", value="1" if value else "0",
                        updated_at=_iso(), note=note)
        db.add(row)
    else:
        row.value = "1" if value else "0"
        row.updated_at = _iso()
        row.note = note
    return paused(db)


def sweep_expired(db):
    """Reservations that outlived a generation plus grace stop counting;
    a crashed process must not hold spend forever."""
    cutoff = (_now() - timedelta(seconds=reservation_ttl_seconds())).isoformat()
    stale = db.scalars(
        select(PilotReservation).where(
            PilotReservation.status == "active",
            PilotReservation.created_at < cutoff,
        )
    ).all()
    for row in stale:
        row.status = "expired"
        row.reconciled_at = _iso()
        row.note = "stale reservation expired"
    return stale


def recorded_tokens(db, participant_id=None, since=None):
    q = select(func.coalesce(func.sum(PilotUsage.input_tokens + PilotUsage.output_tokens), 0))
    if participant_id:
        q = q.where(PilotUsage.participant_id == participant_id)
    if since:
        q = q.where(PilotUsage.at >= since)
    return db.scalar(q) or 0


def committed_tokens(db, participant_id=None, since=None):
    """In-flight reservations plus reconciled amounts whose usage stayed unknown."""
    sweep_expired(db)
    q = select(PilotReservation)
    if participant_id:
        q = q.where(PilotReservation.participant_id == participant_id)
    if since:
        q = q.where(PilotReservation.created_at >= since)
    pending = 0
    for row in db.scalars(q):
        if row.status == "active":
            pending += row.reserved_tokens
        elif row.status == "reconciled":
            pending += row.counted_tokens or 0
    return pending


def assert_allowed(db, p):
    """Pause → global daily ceiling → participant budget. Raises LimitRejected;
    callers turn it into a failed run so the prompt is preserved."""
    if paused(db):
        raise LimitRejected(
            "Live comparisons are paused right now. Your prompt is saved; practice examples and your notebook still work.",
            503,
        )
    today = _now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    if recorded_tokens(db, since=today) + committed_tokens(db, since=today) >= global_daily_tokens():
        raise LimitRejected("Live comparisons are paused for today. Practice examples are still available.", 503)
    account = db.get(PilotAccount, p.id)
    used = recorded_tokens(db, p.id) + committed_tokens(db, p.id)
    if used >= participant_budget(account):
        suffix = (
            "Contact the Calibrated team to extend it."
            if account
            else "Create an account or contact the Calibrated team to extend it."
        )
        raise LimitRejected(f"You've used this account's included model tokens. {suffix}", 402)


def reserve(db, p, run_id, tokens):
    """Hold budget and a concurrency slot before any provider call. The row is
    written first so a crash cannot silently spend; on rejection the row is
    marked expired so it keeps no hold on the budget."""
    reservation = PilotReservation(
        id=secrets.token_hex(16), participant_id=p.id, run_id=run_id,
        reserved_tokens=tokens, counted_tokens=None, status="active",
        created_at=_iso(), reconciled_at=None, note=None,
    )
    db.add(reservation)
    db.commit()  # the hold must be durable before any provider call
    try:
        assert_allowed(db, p)
        active = db.scalar(
            select(func.count()).select_from(PilotReservation).where(PilotReservation.status == "active")
        ) or 0
        if active > max_concurrent_generations():
            raise LimitRejected("The service is at capacity right now. Your prompt is saved; try again shortly.", 429)
        mine = db.scalar(
            select(func.count()).select_from(PilotReservation).where(
                PilotReservation.status == "active",
                PilotReservation.participant_id == p.id,
            )
        ) or 0
        if mine > max_concurrent_per_participant():
            raise LimitRejected("Another comparison is already generating for this account. Your prompt is saved.", 429)
    except LimitRejected as exc:
        reservation.status = "expired"
        reservation.reconciled_at = _iso()
        reservation.note = exc.detail
        raise
    return reservation


def reconcile(db, reservation, attempts):
    """Close a reservation once generation settles (completion, timeout,
    partial failure or an explicit retry's own reservation). Supplied usage is
    recorded in pilot_usage; only the unrecorded remainder keeps counting."""
    recorded = 0
    unreported = 0
    for attempt in attempts or []:
        if attempt.get("usage"):
            input_tokens, output_tokens = usage_tokens(attempt)
            recorded += input_tokens + output_tokens
        else:
            unreported += 1
    reservation.status = "reconciled"
    reservation.reconciled_at = _iso()
    if attempts and not unreported:
        # Every call reported real usage; pilot_usage carries the truth.
        reservation.counted_tokens = 0
        reservation.note = "usage reported"
    else:
        # Partial or missing usage: the unknown share keeps counting at the
        # reserved estimate minus what was actually recorded — never zero.
        reservation.counted_tokens = max(0, reservation.reserved_tokens - recorded)
        reservation.note = "partial usage — remainder counted" if recorded else "usage unknown — full reservation counted"


def generation_state(db):
    today = _now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    flag = db.get(PilotFlag, "generation_paused")
    return {
        "paused": paused(db),
        "env_paused": env_paused(),
        "flag_paused": flag_paused(db),
        "flag_note": flag.note if flag else None,
        "active_reservations": db.scalar(
            select(func.count()).select_from(PilotReservation).where(PilotReservation.status == "active")
        ) or 0,
        "daily_tokens_used": recorded_tokens(db, since=today) + committed_tokens(db, since=today),
        "daily_tokens_limit": global_daily_tokens(),
        "limits": {
            "participant_tokens": _env_int("PILOT_TOKEN_BUDGET", 2000000),
            "guest_tokens": _env_int("PILOT_GUEST_TOKEN_BUDGET", 30000),
            "daily_runs_per_participant": daily_run_limit(),
            "max_concurrent_generations": max_concurrent_generations(),
            "max_concurrent_per_participant": max_concurrent_per_participant(),
            "generation_timeout_seconds": generation_timeout_seconds(),
            "reservation_ttl_seconds": reservation_ttl_seconds(),
        },
    }
