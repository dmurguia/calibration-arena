"""Isolated pilot ledger. No dependency on synthetic legacy votes or credential tiers."""
from datetime import datetime, timezone, timedelta
import hashlib
import os
import secrets
from copy import deepcopy
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator
from sqlalchemy import JSON, String, select, func, update
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..db import Base, get_db
from ..pilot_cases import CASES, snapshot
from ..pilot_inference import generate, live_ready, inference_backend
from ..pilot_tasks import TASKS, case_task
from ..pilot_examples import STARTERS
from ..pilot_audit import GenerationFailure, text_hash
from ..pilot_study import Assignment, ClosePack, assign_cases, assigned_case

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
    independent_first: bool = True  # Legacy callers retain the independent-answer protocol.
    source_run_id: str | None = Field(default=None, max_length=100)
    source_position: Literal['a', 'b'] | None = None
    continuation_mode: Literal['revision', 'followup', 'compare'] = 'revision'
    retry_of_run_id: str | None = Field(default=None, max_length=100)
    source_example_id: str | None = Field(default=None, max_length=100)
    privacy_ack: bool = False  # Historical acknowledgement only; never inferred from submission.
    task_type: Literal["accounting-question", "journal-entry", "treatment-memo", "workpaper-review"] = "accounting-question"

    @model_validator(mode='after')
    def context_fields(self):
        if self.continuation_mode == 'followup' and (not self.source_run_id or not self.source_position):
            raise ValueError('Choose a revealed response to continue.')
        if self.continuation_mode == 'compare' and not self.source_run_id:
            raise ValueError('Choose a conversation to continue.')
        if self.source_position and self.continuation_mode != 'followup':
            raise ValueError('A selected response requires follow-up mode.')
        if self.retry_of_run_id and (self.source_run_id or self.case_id):
            raise ValueError('Retry a failed question without selecting another source.')
        return self


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


class Preference(Strict):
    preference: Literal["a", "b"]
    rationale: str = Field(default="", max_length=3000)


class Issue(Strict):
    position: Literal["a", "b"]
    category: Literal["calculation", "timing", "account-treatment", "policy", "missing-facts", "unsupported-claim", "other"]
    note: str = Field(default="", max_length=3000)

    @model_validator(mode="after")
    def explain_other(self):
        if self.category == "other" and len(self.note) < 5:
            raise ValueError("Describe the issue in a few words.")
        return self


class Improvement(Strict):
    position: Literal["a", "b", "both"] = "both"
    category: Literal["calculation", "timing", "account-treatment", "policy", "missing-facts", "unsupported-claim", "clarity", "other"] | None = None
    note: str = Field(min_length=1, max_length=3000)


class Feedback(Strict):
    usefulness: Literal["useful", "somewhat", "not-useful"]
    note: str = Field(default="", max_length=1000)


class Activity(Strict):
    name: Literal["visit", "share_intent", "left_session", "response_copied", "response_downloaded", "close_examples_opened"]
    run_id: str | None = None
    position: Literal['a', 'b'] | None = None


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
              **{k: data.get(k) for k in ("kind", "case_id", "title", "brief", "conclusion", "mode", "version", "drafts_shown_at", "task_type", "source_run_id", "evaluation_scope", "history", "turn_number", "source_position", "retry_of_run_id", "source_example_id")}}
    if data.get('pair_histories'):
        result['conversation'] = [{'position': 'ab'[i], 'messages': data['pair_histories'].get(model, [])} for i, model in enumerate(data['pair_order'])]
    result['identity_exposed'] = bool(data.get('identity_exposed'))
    result["drafts"] = [{"position": "ab"[i], "text": d["text"], **({k: d.get(k) for k in ("author", "model_id", "origin", "checks", "review_note", "artifact_id")} if revealed else {})} for i, d in enumerate(data.get("drafts", []))] if visible else []
    if revealed:
        result.update({k: data.get(k) for k in ("expected", "takeaway", "validation", "judgment", "feedback")})
    return result


@router.get("/config")
def config():
    return {"ask_mode": "live" if live_ready() else "fixture", "invite_required": False, "inference_backend": inference_backend(), "consent_version": "pilot-research-v1", "prompt_starters": STARTERS, "task_types": [{"id": key, **{k: value[k] for k in ("label", "placeholder")}} for key, value in TASKS.items()]}


@router.get("/cases")
def cases():
    return [{**{k: c[k] for k in ("id", "title", "topic", "minutes", "brief")}, "task_type": case_task(c["id"])} for c in CASES]


def public_assignment(db, assignment):
    pack, case = assigned_case(db, assignment)
    run = db.get(Run, assignment.run_id) if assignment.run_id else None
    return {'id': assignment.id, 'pack_id': pack.id, 'case_id': case['id'], 'version': case['version'],
            'title': case['title'], 'brief': case['brief'], 'framework': case['framework'],
            'evidence': case['evidence'], 'ordinal': assignment.ordinal,
            'run_id': assignment.run_id, 'status': run.status if run else 'not-started',
            'exposure': assignment.exposure}


@router.post('/assignments')
def assignments(p=Depends(participant), db: Session = Depends(get_db)):
    rows = assign_cases(db, p.id)
    return [public_assignment(db, row) for row in rows]


@router.post('/assignments/{assignment_id}/start')
def start_assignment(assignment_id: str, p=Depends(participant), db: Session = Depends(get_db)):
    assignment = db.get(Assignment, assignment_id)
    if not assignment or assignment.participant_id != p.id:
        raise HTTPException(404, 'Case assignment not found.')
    if assignment.run_id:
        emit(db, p, 'case_resumed', db.get(Run, assignment.run_id), {'assignment_id': assignment.id})
        db.commit()
        return public_run(owned(db, p, assignment.run_id))
    try:
        pack, case = assigned_case(db, assignment)
    except ValueError:
        raise HTTPException(409, 'This case pack needs operator review.')
    data = deepcopy(case)
    data.pop('id')
    prior = db.scalar(select(func.count()).select_from(Assignment).where(
        Assignment.participant_id == p.id, Assignment.case_id == case['id'], Assignment.run_id.is_not(None)))
    secrets.SystemRandom().shuffle(data['drafts'])
    data.update(kind='close-case', case_id=case['id'], pack_id=pack.id, pack_sha256=pack.sha256,
                assignment_id=assignment.id, mode='frozen-model-pair', task_type='accounting-question',
                evaluation_scope='shared-close-case', history=[], turn_number=1,
                prior_case_exposure=bool(prior), reviewer_exposure=assignment.exposure,
                drafts_shown_at=now(), independent_first=False)
    run = Run(id=secrets.token_hex(16), participant_id=p.id, created_at=now(), status='review', data=data)
    db.add(run)
    db.flush()
    changed = db.execute(update(Assignment).where(Assignment.id == assignment.id, Assignment.run_id.is_(None)).values(run_id=run.id))
    if changed.rowcount != 1:
        db.rollback()
        db.expire_all()
        return public_run(owned(db, p, db.get(Assignment, assignment_id).run_id))
    emit(db, p, 'session_started', run, {'entry': 'close-case', 'assignment_id': assignment.id, 'pack_id': pack.id})
    emit(db, p, 'drafts_shown', run, {'mechanism': 'preference-v2'})
    db.commit()
    return public_run(run)


@router.post("/participants")
def enroll(body: Profile, db: Session = Depends(get_db)):
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
    evidence = {}
    if body.name in ('response_copied', 'response_downloaded'):
        if not run or run.status != 'completed' or not body.position:
            raise HTTPException(422, 'Select a revealed response for this action.')
        draft = run.data['drafts']['ab'.index(body.position)]
        evidence = {'position': body.position, 'artifact_id': draft.get('artifact_id'),
                    'text_sha256': text_hash(draft['text']), 'after_reveal': True}
    if body.name == "visit":
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        recent = db.scalar(select(Event).where(Event.participant_id == p.id, Event.name == "visit", Event.at > cutoff))
        if recent:
            return {"ok": True}
    emit(db, p, body.name, run, evidence)
    db.commit()
    return {"ok": True}


def conversation_revealed(db, run):
    root = run.data.get('root_run_id') or run.id
    return any(r.status == 'completed' for r in db.scalars(select(Run).where(Run.participant_id == run.participant_id))
               if (r.data.get('root_run_id') or r.id) == root)


@router.post("/runs")
async def start(body: Start, p=Depends(participant), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(Run).where(Run.participant_id == p.id, Run.created_at >= now()[:10]))
    if count >= 20:
        raise HTTPException(429, "You've reached today's 20-session limit. Come back tomorrow.")
    source = owned(db, p, body.source_run_id) if body.source_run_id else None
    retry = owned(db, p, body.retry_of_run_id) if body.retry_of_run_id else None
    if retry and retry.status != 'failed':
        raise HTTPException(409, 'Only a failed request can be retried.')
    if source and (source.status not in (("review", "completed") if body.continuation_mode == "compare" else ("completed",)) or body.case_id):
        raise HTTPException(409, "Vote on the original pair before starting a revised prompt.")
    example = next((e for e in STARTERS if e['id'] == body.source_example_id), None)
    if body.source_example_id and not example:
        raise HTTPException(422, 'Unknown prompt starter.')
    history = []
    pair_histories = {}
    pair_order = []
    identity_exposed = False
    turn_number = 1
    source_artifact = None
    if source and body.continuation_mode == 'compare':
        if source.data['mode'] not in ('direct', 'local-cli', 'openrouter'):
            raise HTTPException(422, 'Start an open question to compare model conversations.')
        turn_number = source.data.get('turn_number', 1) + 1
        pair_order = [d['model_id'] for d in source.data['drafts']]
        if len(set(pair_order)) != 2:
            raise HTTPException(422, 'A conversation requires two distinct model IDs.')
        for d in source.data['drafts']:
            pair_histories[d['model_id']] = [*source.data.get('pair_histories', {}).get(d['model_id'], source.data.get('history', [])),
                {'role': 'user', 'content': source.data['brief']}, {'role': 'assistant', 'content': d['text']}]
        identity_exposed = conversation_revealed(db, source)
    elif source and body.continuation_mode == 'followup':
        selected = source.data['drafts']['ab'.index(body.source_position)]
        history = [*source.data.get('history', []), {'role': 'user', 'content': source.data['brief']},
                   {'role': 'assistant', 'content': selected['text']}]
        turn_number = source.data.get('turn_number', 1) + 1
        source_artifact = {'artifact_id': selected.get('artifact_id'), 'text_sha256': text_hash(selected['text'])}
    elif retry:
        history = retry.data.get('history', [])
        turn_number = retry.data.get('turn_number', 1)
        source_artifact = retry.data.get('source_artifact')
        pair_histories = retry.data.get('pair_histories', {})
        pair_order = retry.data.get('pair_order', [])
        identity_exposed = retry.data.get('identity_exposed', False)
    if pair_histories and (turn_number > 5 or any(sum(len(m['content']) for m in h) + len(body.question) > 40000 for h in pair_histories.values())):
        raise HTTPException(422, 'This comparison reached its limit (5 turns or 40,000 characters). Finish and reveal, or start a new question.')
    if turn_number > 20 or sum(len(m['content']) for m in history) + len(body.question) > 40000:
        raise HTTPException(422, 'This conversation reached its context limit (20 turns or 40,000 characters). Start a new question; the notebook keeps this conversation.')
    if body.case_id:
        case = next((c for c in CASES if c["id"] == body.case_id), None)
        if case is None:
            raise HTTPException(404, "Practice case not found.")
        if body.question and body.question != case["brief"]:
            raise HTTPException(422, "This edited prompt is no longer the fixed sample. Submit it as a new model comparison.")
        data = snapshot(case)
        data.update(kind="challenge", case_id=case["id"], mode="authored-fixture", task_type=case_task(case["id"]))
        secrets.SystemRandom().shuffle(data["drafts"])
        status = "conclusion" if body.independent_first else "review"
        data["independent_first"] = body.independent_first
        if status == "review":
            data["drafts_shown_at"] = now()
    else:
        if len(body.question) < (1 if history or pair_histories else 15):
            raise HTTPException(422, "Describe a new question in at least 15 characters, or enter a follow-up.")
        if not live_ready():
            raise HTTPException(503, "Live models are not connected yet. You can review a sample case from the sidebar; your prompt has not been replaced with a sample.")
        data = {"kind": "ask", "case_id": None, "title": TASKS[body.task_type]["label"], "brief": body.question,
                "mode": inference_backend(), "version": "ask-local-v3" if inference_backend() == "local-cli" else "ask-v4", "drafts": [], "privacy_ack": body.privacy_ack,
                "task_type": body.task_type, "routing": "explicit-user-selection",
                "source_run_id": source.id if source else retry.data.get('source_run_id') if retry else None,
                "source_position": body.source_position if source else retry.data.get('source_position') if retry else None,
                "pair_histories": pair_histories, "pair_order": pair_order, "identity_exposed": identity_exposed,
                "source_artifact": source_artifact, "history": history, "turn_number": turn_number,
                "retry_of_run_id": retry.id if retry else None,
                "source_example_id": body.source_example_id, "source_example_version": example['version'] if example else None,
                "source_example_edited": body.question != example['brief'] if example else None,
                "root_run_id": (source.data.get("root_run_id") or source.id) if source else (retry.data.get('root_run_id') or retry.id) if retry else None,
                "evaluation_scope": ("unblinded-conversation" if identity_exposed else "blind-conversation") if pair_histories else 'exploratory-followup' if history else "exploratory-prompt-revision" if source else 'exploratory-retry' if retry else 'exploratory-prompt-starter' if example else "exploratory-first-pair"}
        status = "generating"
    run = Run(id=secrets.token_hex(16), participant_id=p.id, created_at=now(), status=status, data=data)
    db.add(run)
    emit(db, p, "session_started", run, {"entry": data["kind"], "mode": data["mode"], "case_id": data["case_id"], "task_type": data["task_type"]})
    if status == "review":
        emit(db, p, "drafts_shown", run, {"mechanism": "preference-v2"})
    db.commit()
    if not body.case_id:
        try:
            drafts = await generate(body.question, body.task_type, history=pair_histories or history) if history or pair_histories else await generate(body.question, body.task_type)
            attempts = [d.pop('attempt') for d in drafts if 'attempt' in d]
            if pair_order:
                if set(pair_order) != {d['model_id'] for d in drafts}:
                    raise GenerationFailure('The model pair changed. Start a new comparison.', attempts)
                drafts.sort(key=lambda d: pair_order.index(d['model_id']))
            else:
                secrets.SystemRandom().shuffle(drafts)
            run.data = {**data, "drafts": drafts, "generation_attempts": attempts, "drafts_shown_at": now()}
            run.status = "review"
            emit(db, p, "drafts_shown", run, {"mechanism": "preference-v2"})
        except ValueError as exc:
            run.data = {**data, 'generation_attempts': exc.attempts if isinstance(exc, GenerationFailure) else [],
                        'generation_error_type': type(exc).__name__}
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


@router.post("/runs/{run_id}/skip-conclusion")
def skip_conclusion(run_id: str, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    changed = db.execute(update(Run).where(Run.id == run_id, Run.status == "conclusion").values(
        data={**run.data, "conclusion_skipped_at": now(), "drafts_shown_at": now()}, status="review"))
    if changed.rowcount != 1:
        raise HTTPException(409, "The drafts have already been opened.")
    emit(db, p, "conclusion_skipped", run)
    emit(db, p, "drafts_shown", run, {"mechanism": "preference-v2"})
    db.commit()
    db.refresh(run)
    return public_run(run)


@router.post("/runs/{run_id}/preference")
def prefer(run_id: str, body: Preference, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    if run.status != "review":
        if run.status == 'completed' and run.data.get('judgment', {}).get('mechanism') == 'preference-v2' and run.data['judgment']['preference'] == body.preference:
            return public_run(run)
        raise HTTPException(409, "This pair is not awaiting a vote.")
    elapsed = int((datetime.now(timezone.utc) - datetime.fromisoformat(run.data["drafts_shown_at"])).total_seconds() * 1000)
    # Missing approval/confidence is deliberately NOT inferred from a preference.
    exposed = bool(run.data.get('identity_exposed')) or conversation_revealed(db, run)
    judgment = {**body.model_dump(), "identity_exposed": exposed, "turn_number": run.data.get('turn_number', 1),
                "artifacts": [{"artifact_id": d.get('artifact_id'), "text_sha256": text_hash(d['text'])} for d in run.data['drafts']], "a": None, "b": None, "confidence": None, "reasons": [],
                "rationale": body.rationale.strip(), "correction": "", "submitted_at": now(), "decision_ms": elapsed,
                "mechanism": "preference-v2", "question": "Which conversation would you prefer to use?"}
    changed = db.execute(update(Run).where(Run.id == run_id, Run.status == "review").values(
        data={**run.data, "judgment": judgment}, status="completed"))
    if changed.rowcount != 1:
        db.refresh(run)
        if run.status == 'completed' and run.data.get('judgment', {}).get('mechanism') == 'preference-v2' and run.data['judgment']['preference'] == body.preference:
            return public_run(run)
        raise HTTPException(409, "This pair already has a vote.")
    emit(db, p, "judgment_completed", run, {"mechanism": "preference-v2"})
    db.commit()
    db.refresh(run)
    return public_run(run)


@router.get("/runs/{run_id}/issues")
def issues(run_id: str, p=Depends(participant), db: Session = Depends(get_db)):
    owned(db, p, run_id)
    records = db.scalars(select(Event).where(Event.run_id == run_id, Event.name == "issue_reported").order_by(Event.at)).all()
    return [{"id": e.id, "at": e.at, **{k: e.data[k] for k in ("position", "category", "note", "after_reveal")}} for e in records]


@router.post("/runs/{run_id}/issues")
def report_issue(run_id: str, body: Issue, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    if run.status not in ("review", "completed"):
        raise HTTPException(409, "Open the drafts before reporting an issue.")
    count = db.scalar(select(func.count()).select_from(Event).where(Event.run_id == run_id, Event.name == "issue_reported"))
    if count >= 20:
        raise HTTPException(429, "This pair already has 20 issue reports.")
    draft = run.data["drafts"]["ab".index(body.position)]
    emit(db, p, "issue_reported", run, {**body.model_dump(), "artifact_id": draft.get("artifact_id"),
         "text_sha256": hashlib.sha256(draft["text"].encode()).hexdigest(),
         "after_reveal": run.status == "completed", "taxonomy_version": "accounting-issues-v1",
         "assessment": "reviewer-reported-unverified"})
    db.commit()
    return issues(run_id, p, db)


@router.post("/runs/{run_id}/improvements")
def improve(run_id: str, body: Improvement, p=Depends(participant), db: Session = Depends(get_db)):
    run = owned(db, p, run_id)
    if run.status not in ("review", "completed"):
        raise HTTPException(409, "Open the responses before leaving feedback.")
    count = db.scalar(select(func.count()).select_from(Event).where(Event.run_id == run_id, Event.name == "issue_reported"))
    if count >= 20:
        raise HTTPException(429, "This comparison already has 20 feedback notes.")
    targets = [i for i in range(2) if body.position == "both" or "ab"[i] == body.position]
    artifacts = [{"position": "ab"[i], "artifact_id": run.data["drafts"][i].get("artifact_id"),
                  "text_sha256": hashlib.sha256(run.data["drafts"][i]["text"].encode()).hexdigest()} for i in targets]
    emit(db, p, "issue_reported", run, {**body.model_dump(), "artifacts": artifacts,
         "after_reveal": run.status == "completed", "taxonomy_version": "response-improvement-v2",
         "assessment": "reviewer-reported-unverified"})
    db.commit()
    return issues(run_id, p, db)


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
    return {"schema_version": "pilot-export-v2", "exported_at": now(), "notice": "PRIVATE pilot records. Check each participant research_consent before research reuse. No publication or training rights granted. Identity is self-reported. Authored fixtures are not model runs.",
            "close_packs": [{'id': pack.id, 'sha256': pack.sha256, 'created_at': pack.created_at, 'active': pack.active, 'data': pack.data} for pack in db.scalars(select(ClosePack))],
            "assignments": [{k: getattr(a, k) for k in ('id', 'participant_id', 'pack_id', 'case_id', 'ordinal', 'created_at', 'run_id', 'exposure')} for a in db.scalars(select(Assignment))],
            "participants": [{"id": p.id, "created_at": p.created_at, **p.profile} for p in db.scalars(select(Participant)).all()],
            "runs": [{**r.data, "id": r.id, "participant_id": r.participant_id, "created_at": r.created_at, "status": r.status} for r in db.scalars(select(Run)).all()],
            "events": [{"id": e.id, "participant_id": e.participant_id, "run_id": e.run_id, "name": e.name, "at": e.at, "data": e.data} for e in db.scalars(select(Event)).all()]}


@router.get("/founder/export")
def founder_export(x_pilot_admin: str = Header(default=""), db: Session = Depends(get_db)):
    expected = os.getenv("PILOT_ADMIN_TOKEN", "")
    if len(expected) < 24 or expected.startswith("PLACEHOLDER") or not secrets.compare_digest(x_pilot_admin, expected):
        raise HTTPException(403, "Founder review requires the configured private admin token.")
    return export_data(db)
