import base64
import hashlib
import hmac
import os
import time
from collections import defaultdict

from fastapi import HTTPException, Request
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class PilotAccount(Base):
    __tablename__ = "pilot_accounts"

    participant_id: Mapped[str] = mapped_column(ForeignKey("pilot_participants.id"), primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    token_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reset_hash: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    reset_expires_at: Mapped[str | None] = mapped_column(String, nullable=True)


class PilotSession(Base):
    __tablename__ = "pilot_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("pilot_participants.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String)
    revoked_at: Mapped[str | None] = mapped_column(String, nullable=True)
    last_seen_at: Mapped[str] = mapped_column(String)


class PilotUsage(Base):
    __tablename__ = "pilot_usage"
    __table_args__ = (Index("ix_pilot_usage_at", "at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("pilot_participants.id"), index=True)
    run_id: Mapped[str] = mapped_column(String)
    model_id: Mapped[str] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    at: Mapped[str] = mapped_column(String)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = encoded.split("$")
        if scheme != "scrypt":
            raise ValueError
        digest = hashlib.scrypt(
            password.encode(),
            salt=base64.b64decode(salt, validate=True),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=32,
        )
        return hmac.compare_digest(digest, base64.b64decode(expected, validate=True))
    except (ValueError, TypeError):
        return False


_DUMMY_HASH = "scrypt$16384$8$1$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


class SlidingWindowLimiter:
    def __init__(self):
        self.events: dict[str, list[float]] = defaultdict(list)

    def reset(self):
        self.events.clear()

    def allowed(self, key: str, limit: int, seconds: int) -> bool:
        now = time.monotonic()
        recent = [stamp for stamp in self.events[key] if stamp > now - seconds]
        self.events[key] = recent
        return len(recent) < limit

    def record(self, key: str, limit: int, seconds: int) -> bool:
        now = time.monotonic()
        recent = [stamp for stamp in self.events[key] if stamp > now - seconds]
        self.events[key] = recent
        if len(recent) >= limit:
            return False
        recent.append(now)
        return True


_limiter = SlidingWindowLimiter()
_RATE_LIMIT_MESSAGE = "Too many attempts. Try again in a few minutes."


def reset_limits():
    _limiter.reset()


def client_ip(request: Request) -> str:
    if os.getenv("ARENA_TRUST_PROXY") == "1":
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded.strip():
            return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request, key: str, limit: int, seconds: int):
    if not _limiter.record(f"{client_ip(request)}:{key}", limit, seconds):
        raise HTTPException(429, _RATE_LIMIT_MESSAGE)


def login_is_limited(request: Request, email: str) -> bool:
    ip = client_ip(request)
    return not _limiter.allowed(f"{ip}:login-ip", 10, 15 * 60) or not _limiter.allowed(f"login-email:{email}", 10, 15 * 60)


def record_login_failure(request: Request, email: str):
    ip = client_ip(request)
    _limiter.record(f"{ip}:login-ip", 10, 15 * 60)
    _limiter.record(f"login-email:{email}", 10, 15 * 60)


def admin_check_allowed(request: Request) -> bool:
    return _limiter.allowed(f"{client_ip(request)}:admin", 10, 15 * 60)


def record_admin_failure(request: Request):
    _limiter.record(f"{client_ip(request)}:admin", 10, 15 * 60)


def require_login_limit(request: Request, email: str):
    if login_is_limited(request, email):
        raise HTTPException(429, _RATE_LIMIT_MESSAGE)


def require_dummy_password_work(password: str):
    verify_password(password, _DUMMY_HASH)
