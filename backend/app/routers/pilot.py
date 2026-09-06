"""Isolated pilot ledger. No dependency on synthetic legacy votes or credential tiers."""
from datetime import datetime, timezone, timedelta
import hashlib
import os
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator
from sqlalchemy import JSON, String, select, func, update
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..db import Base, get_db
from ..pilot_cases import CASES, snapshot
from ..pilot_inference import generate, live_ready, inference_backend
from ..pilot_tasks import TASKS, case_task

router = APIRouter(prefix="/api/pilot", tags=["pilot"])


def now():
    return datetime.now(timezone.utc).isoformat()


class Participant(Base):
    __tablename__ = "pilot_participants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[str] = mapped_column(String)
    profile: Mapped[dict] = mapped_column(JSON)


class Run(Base):
    __tablename__ = "pilot_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    participant_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON)


class Event(Base):
    __tablename__ = "pilot_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    participant_id: Mapped[str] = mapped_column(String, index=True)
    run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String)
    at: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Profile(Strict):
    name: str = Field(min_length=1, max_length=60)
    role: Literal["Public accountant", "Industry accountant", "Bookkeeper", "Controller / finance leader", "Other accounting professional"]
    experience: Literal["0–2 years", "3–7 years", "8–15 years", "16+ years"]
    framework: Literal["US GAAP", "IFRS", "Local GAAP / other", "Multiple / not applicable"]
    email: EmailStr | None = None
    followup: bool = False
    research_consent: bool = False
    source: str = Field(default="direct", max_length=100)
    invite_code: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def contact(self):
        if self.email and not self.followup:
            raise ValueError("Choose follow-up permission to save an email address.")
        if self.followup and not self.email:
            raise ValueError("Add an email address for follow-up.")
        return self


class Guest(Strict):
    research_consent: bool = False
    source: str = Field(default="direct", max_length=100)
    invite_code: str = Field(default="", max_length=200)


class Start(Strict):
    case_id: str | None = Field(default=None, max_length=100)
    question: str = Field(default="", max_length=5000)
    privacy_ack: bool = False  # Historical acknowledgement only; never inferred from submission.
    task_type: Literal["journal-entry", "treatment-memo", "workpaper-review"] = "journal-entry"


class Conclusion(Strict):
    conclusion: str = Field(min_length=10, max_length=3000)


Approval = Literal["ready", "revise", "unsure"]
Reason = Literal["Amounts", "Timing", "Account treatment", "Policy", "Evidence", "Clarity", "Missing facts", "Other"]


class Judgment(Strict):
    a: Approval
    b: Approval
    preference: Literal["a", "b", "tie", "neither", "unsure"]
    reasons: list[Reason] = Field(min_length=1, max_length=8)
    confidence: Literal["low", "medium", "high"]
    rationale: str = Field(default="", max_length=3000)
    correction: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def consistent(self):
        if self.preference == "neither" and "ready" in (self.a, self.b):
            raise ValueError("Neither is ready conflicts with a ready-to-approve draft.")
        if "Other" in self.reasons and len(self.rationale) < 5:
            raise ValueError("Explain your Other reason in a few words.")
        return self


class Feedback(Strict):
    usefulness: Literal["useful", "somewhat", "not-useful"]
    note: str = Field(default="", max_length=1000)


class Activity(Strict):
    name: Literal["visit", "share_intent", "left_session"]
    run_id: str | None = None


def emit(db, p, name, run=None, data=None):
    db.add(Event(id=secrets.token_hex(16), participant_id=p.id, run_id=run.id if run else None, name=name, at=now(), data=data or {}))


def participant(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Start a comparison to save your work.")
    digest = hashlib.sha256(authorization[7:].encode()).hexdigest()
    p = db.scalar(select(Participant).where(Participant.token_hash == digest))
    if p is None:
        raise HTTPException(401, "This browser session is no longer available. Begin again or contact the Calibrated team.")
    return p


def owned(db, p, run_id):
    run = db.get(Run, run_id)
    if run is None or run.participant_id != p.id:
        raise HTTPException(404, "Session not found.")
    return run


def public_run(run):
    data = run.data
    revealed = run.status == "completed"
    visible = run.status in ("review", "completed")
    result = {"id": run.id, "status": run.status, "created_at": run.created_at,
              **{k: data.get(k) for k in ("kind", "case_id", "title", "brief", "conclusion", "mode", "version", "drafts_shown_at", "task_type")}}
    result["drafts"] = [{"position": "ab"[i], "text": d["text"], **({k: d.get(k) for k in ("author", "model_id", "origin", "checks", "review_note", "artifact_id")} if revealed else {})} for i, d in enumerate(data.get("drafts", []))] if visible else []
    if revealed:
        result.update({k: data.get(k) for k in ("expected", "takeaway", "validation", "judgment", "feedback")})
    return result


@router.get("/config")
def config():
    return {"ask_mode": "live" if live_ready() else "fixture", "invite_required": bool(os.getenv("PILOT_INVITE_CODE")), "inference_backend": inference_backend(), "consent_version": "pilot-research-v1", "task_types": [{"id": key, **{k: value[k] for k in ("label", "placeholder")}} for key, value in TASKS.items()]}


@router.get("/cases")
def cases():
    return [{**{k: c[k] for k in ("id", "title", "topic", "minutes", "brief")}, "task_type": case_task(c["id"])} for c in CASES]


@router.post("/participants")
def enroll(body: Profile, db: Session = Depends(get_db)):
    required = os.getenv("PILOT_INVITE_CODE", "")
    if required and not secrets.compare_digest(body.invite_code, required):
        raise HTTPException(403, "The invitation code is not valid.")
    token = secrets.token_urlsafe(32)
    profile = body.model_dump(exclude={"invite_code"})
    profile.update(consent_version="pilot-research-v1" if body.research_consent else None, consent_at=now() if body.research_consent else None, publication_consent=False, training_consent=False, identity="self-reported", dataset=os.getenv("PILOT_DATASET", "preview"))
    p = Participant(id=secrets.token_hex(16), token_hash=hashlib.sha256(token.encode()).hexdigest(), created_at=now(), profile=profile)
    db.add(p)
    emit(db, p, "enrolled", data={"source": body.source})
    emit(db, p, "visit")
    db.commit()
    return {"token": token, "participant": {"id": p.id, **p.profile}}


@router.post("/guests")
def guest(body: Guest, db: Session = Depends(get_db)):
    required = os.getenv("PILOT_INVITE_CODE", "")
    if required and not secrets.compare_digest(body.invite_code, required):
        raise HTTPException(403, "The invitation code is not valid.")
    raw = secrets.token_urlsafe(32)
    profile = dict(name="Guest", role="Not supplied", experience="Not supplied", framework="Not supplied", followup=False,
                   research_consent=body.research_consent, source=body.source, consent_version="pilot-research-v1" if body.research_consent else None, consent_at=now() if body.research_consent else None,
                   publication_consent=False, training_consent=False, identity="guest", dataset=os.getenv("PILOT_DATASET", "preview"))
    p = Participant(id=secrets.token_hex(16), token_hash=hashlib.sha256(raw.encode()).hexdigest(), created_at=now(), profile=profile)
    db.add(p)
    emit(db, p, "enrolled", data={"source": body.source, "identity": "guest"})
    emit(db, p, "visit")
    db.commit()
    return {"token": raw, "participant": {"id": p.id, **p.profile}}


@router.post("/profile")
def enrich_profile(body: Profile, p=Depends(participant), db: Session = Depends(get_db)):
    # Enrich the existing guest record; never create a second identity or drop its runs.
    fields = body.model_dump(exclude={"invite_code", "source"})
    p.profile = {**p.profile, **fields, "identity": "self-reported", "profile_updated_at": now(), "consent_version": "pilot-research-v1" if body.research_consent else None, "consent_at": now() if body.research_consent else None}
    emit(db, p, "profile_completed")
    db.commit()
    return {"participant": {"id": p.id, **p.profile}}


@router.get("/me")
def me(p=Depends(participant), db: Session = Depends(get_db)):
    runs = db.scalars(select(Run).where(Run.participant_id == p.id).order_by(Run.created_at.desc())).all()
    return {"participant": {"id": p.id, **p.profile}, "runs": [public_run(r) for r in runs]}


@router.post("/events")
def activity(body: Activity, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, body.run_id) if body.run_id else None
    if body.name == "visit":
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        recent = db.scalar(select(Event).where(Event.participant_id == p.id, Event.name == "visit", Event.at > cutoff))
        if recent:
            return {"ok": True}
    emit(db, p, body.name, run)
    db.commit()
    return {"ok": True}


@router.post("/runs")
async def start(body: Start, p=Depends(participant), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(Run).where(Run.participant_id == p.id, Run.created_at >= now()[:10]))
    if count >= 20:
        raise HTTPException(429, "You've reached today's 20-session limit. Come back tomorrow.")
    if body.case_id:
        case = next((c for c in CASES if c["id"] == body.case_id), None)
        if case is None:
            raise HTTPException(404, "Practice case not found.")
        if body.question and body.question != case["brief"]:
            raise HTTPException(422, "This edited prompt is no longer the fixed sample. Submit it as a new model comparison.")
        data = snapshot(case)
        data.update(kind="challenge", case_id=case["id"], mode="authored-fixture", task_type=case_task(case["id"]))
        secrets.SystemRandom().shuffle(data["drafts"])
        status = "conclusion"
    else:
        if len(body.question) < 15:
            raise HTTPException(422, "Describe the work in at least 15 characters.")
        if not live_ready():
            raise HTTPException(503, "Live models are not connected yet. You can review a sample case from the sidebar; your prompt has not been replaced with a sample.")
        data = {"kind": "ask", "case_id": None, "title": TASKS[body.task_type]["label"], "brief": body.question,
                "mode": inference_backend(), "version": "ask-local-v1" if inference_backend() == "local-cli" else "ask-v2", "drafts": [], "privacy_ack": body.privacy_ack,
                "task_type": body.task_type, "routing": "explicit-user-selection"}
        status = "generating"
    run = Run(id=secrets.token_hex(16), participant_id=p.id, created_at=now(), status=status, data=data)
    db.add(run)
    emit(db, p, "session_started", run, {"entry": data["kind"], "mode": data["mode"], "case_id": data["case_id"], "task_type": data["task_type"]})
    db.commit()
    if not body.case_id:
        try:
            drafts = await generate(body.question, body.task_type)
            secrets.SystemRandom().shuffle(drafts)
            run.data = {**data, "drafts": drafts, "drafts_shown_at": now()}
            run.status = "review"
            emit(db, p, "drafts_shown", run, {"mechanism": "approval-and-pair-v1"})
        except ValueError:
            run.status = "failed"
            emit(db, p, "generation_failed", run)
        db.commit()
    return public_run(run)


@router.get("/runs/{run_id}")
def get_run(run_id: str, p=Depends(participant), db: Session = Depends(get_db)):
    return public_run(owned(db, p, run_id))


@router.post("/runs/{run_id}/conclusion")
def conclude(run_id: str, body: Conclusion, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    if run.status != "conclusion":
        raise HTTPException(409, "The independent conclusion has already been saved.")
    data = {**run.data, "conclusion": body.conclusion, "drafts_shown_at": now()}
    changed = db.execute(update(Run).where(Run.id == run_id, Run.status == "conclusion").values(data=data, status="review"))
    if changed.rowcount != 1:
        raise HTTPException(409, "The independent conclusion has already been saved.")
    emit(db, p, "conclusion_saved", run)
    emit(db, p, "drafts_shown", run, {"mechanism": "approval-and-pair-v1"})
    db.commit()
    db.refresh(run)
    return public_run(run)


@router.post("/runs/{run_id}/judgment")
def judge(run_id: str, body: Judgment, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    if run.status != "review":
        raise HTTPException(409, "This session is not awaiting a judgment.")
    elapsed = int((datetime.now(timezone.utc) - datetime.fromisoformat(run.data["drafts_shown_at"])).total_seconds() * 1000)
    judgment = {**body.model_dump(), "submitted_at": now(), "decision_ms": elapsed, "mechanism": "approval-and-pair-v1", "reason_version": "reasons-v1"}
    changed = db.execute(update(Run).where(Run.id == run_id, Run.status == "review").values(data={**run.data, "judgment": judgment}, status="completed"))
    if changed.rowcount != 1:
        raise HTTPException(409, "This session was already judged.")
    emit(db, p, "judgment_completed", run)
    db.commit()
    db.refresh(run)
    return public_run(run)


@router.post("/runs/{run_id}/feedback")
def feedback(run_id: str, body: Feedback, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    if run.status != "completed":
        raise HTTPException(409, "Complete the judgment first.")
    run.data = {**run.data, "feedback": {**body.model_dump(), "at": now()}}
    emit(db, p, "usefulness_submitted", run)
    db.commit()
    return public_run(run)


def export_data(db):
    return {"schema_version": "pilot-export-v1", "exported_at": now(), "notice": "PRIVATE pilot records. Check each participant research_consent before research reuse. No publication or training rights granted. Identity is self-reported. Authored fixtures are not model runs.",
            "participants": [{"id": p.id, "created_at": p.created_at, **p.profile} for p in db.scalars(select(Participant)).all()],
            "runs": [{**r.data, "id": r.id, "participant_id": r.participant_id, "created_at": r.created_at, "status": r.status} for r in db.scalars(select(Run)).all()],
            "events": [{"id": e.id, "participant_id": e.participant_id, "run_id": e.run_id, "name": e.name, "at": e.at, "data": e.data} for e in db.scalars(select(Event)).all()]}


@router.get("/founder/export")
def founder_export(x_pilot_admin: str = Header(default=""), db: Session = Depends(get_db)):
    expected = os.getenv("PILOT_ADMIN_TOKEN", "")
    if len(expected) < 24 or expected.startswith("PLACEHOLDER") or not secrets.compare_digest(x_pilot_admin, expected):
        raise HTTPException(403, "Founder review requires the configured private admin token.")
    return export_data(db)
