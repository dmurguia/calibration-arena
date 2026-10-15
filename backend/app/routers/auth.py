from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..categories import VERTICALS
from ..config import get_settings
from ..db import get_db
from ..deps import SESSION_COOKIE, get_current_user
from ..models import AuthCode, User, utcnow
from ..schemas import (
    ProfileIn,
    RequestCodeIn,
    RequestCodeOut,
    ReviewerStatsOut,
    SessionOut,
    UserOut,
    VerifyCodeIn,
)
from ..security import generate_login_code, sign_session
from ..services.reviewer import reviewer_stats, tier_for_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

CODE_TTL = timedelta(minutes=15)


@router.post("/request-code", response_model=RequestCodeOut)
def request_code(payload: RequestCodeIn, db: Session = Depends(get_db)) -> RequestCodeOut:
    settings = get_settings()
    code = generate_login_code()
    db.add(AuthCode(email=payload.email.lower(), code=code, expires_at=utcnow() + CODE_TTL))
    db.commit()

    # PLACEHOLDER: wire a transactional email provider (Resend/SendGrid) here
    # using settings.email_provider_api_key. Until then, dev mode returns the
    # code in the response so the flow is fully usable locally.
    dev_code = code if settings.dev_return_login_code else None
    return RequestCodeOut(ok=True, dev_code=dev_code)


@router.post("/verify", response_model=SessionOut)
def verify(payload: VerifyCodeIn, response: Response, db: Session = Depends(get_db)) -> SessionOut:
    email = payload.email.lower()
    record = db.scalars(
        select(AuthCode)
        .where(AuthCode.email == email, AuthCode.code == payload.code, AuthCode.used.is_(False))
        .order_by(AuthCode.id.desc())
        .limit(1)
    ).first()
    if record is None or _as_utc(record.expires_at) < utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired code.")
    record.used = True

    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None:
        # Credential tier from the email domain: work domains verify cheaply.
        user = User(email=email, display_name=email.split("@")[0], tier=tier_for_email(email))
        db.add(user)
        db.flush()
    db.commit()

    token = sign_session(user.id)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=get_settings().session_ttl_seconds,
    )
    return SessionOut(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/profile", response_model=UserOut)
def set_profile(
    payload: ProfileIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    if payload.vertical not in VERTICALS:
        raise HTTPException(status_code=400, detail=f"Unknown vertical '{payload.vertical}'.")
    user.vertical = payload.vertical
    user.role = payload.role.strip()
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/reviewer", response_model=ReviewerStatsOut)
def reviewer(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ReviewerStatsOut:
    return ReviewerStatsOut(**reviewer_stats(db, user))


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


def _as_utc(value):
    """SQLite hands back naive datetimes (stored as UTC); Postgres hands back
    aware ones in the session time zone. Compare both as aware UTC."""
    from datetime import timezone
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
