"""Immutable close-case packs and resumable participant assignments.

Human approvals are operator-supplied records, not automated certification.
Unapproved prompts and authored practice drafts never enter this collection.
"""
from copy import deepcopy
from datetime import datetime
from sqlalchemy import JSON, String, Boolean, Integer, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .pilot_audit import object_hash, text_hash, timestamp, hygiene
from .pilot_direct import normalized_messages


class ClosePack(Base):
    __tablename__ = 'pilot_close_packs'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    sha256: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    data: Mapped[dict] = mapped_column(JSON)


class Assignment(Base):
    __tablename__ = 'pilot_case_assignments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    participant_id: Mapped[str] = mapped_column(String, index=True)
    pack_id: Mapped[str] = mapped_column(String, index=True)
    case_id: Mapped[str] = mapped_column(String)
    ordinal: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String)
    run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    exposure: Mapped[str] = mapped_column(String, default='not-reported')


def validate_pack(document):
    if document.get('schema_version') != 'close-pack-v1' or not document.get('id'):
        raise ValueError('Expected close-pack-v1 with a stable pack ID.')
    cases = document.get('cases', [])
    if not 1 <= len(cases) <= 6 or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('A pack requires 1–6 distinct cases.')
    artifact_ids = set()
    for case in cases:
        for field in ('id', 'version', 'title', 'brief', 'framework', 'period', 'materiality', 'evidence', 'rubric'):
            if not case.get(field):
                raise ValueError(f'Missing case field: {field}')
        rubric = case['rubric']
        if not isinstance(rubric, list) or len({r['id'] for r in rubric}) != len(rubric):
            raise ValueError('Rubric criterion IDs must be unique.')
        for criterion in rubric:
            if any(not criterion.get(k) for k in ('id', 'requirement', 'acceptable_alternatives', 'source', 'material_error')):
                raise ValueError('Every criterion needs requirements, alternatives, source and material-error definition.')
        validation = case.get('validation', {})
        reviewers = validation.get('reviewers', [])
        if validation.get('status') != 'approved' or len(reviewers) < 2 or len({r['id'] for r in reviewers}) != len(reviewers):
            raise ValueError('Two distinct independent reviewer approvals are required.')
        if any(not all(r.get(k) for k in ('id', 'independent_review_ref', 'approved_at', 'qualification')) for r in reviewers):
            raise ValueError('Reviewer evidence, qualification and approval date are required.')
        if validation.get('brief_sha256') != text_hash(case['brief']) or validation.get('rubric_sha256') != object_hash(rubric):
            raise ValueError('Approved brief/rubric hashes do not match.')
        if validation.get('evidence_sha256') != object_hash(case['evidence']):
            raise ValueError('Approved evidence hash does not match.')
        scope = {k: case[k] for k in ('id', 'version', 'brief', 'framework', 'period', 'materiality', 'evidence')}
        if validation.get('case_sha256') != object_hash(scope):
            raise ValueError('Approved case scope hash does not match.')
        if not validation.get('reconciliation_ref'):
            raise ValueError('Preserve the independent reviews and reconciliation record.')
        drafts = case.get('drafts', [])
        if len(drafts) != 2 or len({d.get('model_id') for d in drafts}) != 2:
            raise ValueError('Each case requires two different model responses.')
        attempts = {a['id']: a for a in case.get('generation_attempts', [])}
        common_inputs = []
        for draft in drafts:
            aid = draft.get('artifact_id')
            attempt = attempts.get(aid, {})
            if not aid or aid in artifact_ids:
                raise ValueError('Output artifact IDs must be unique within a pack.')
            artifact_ids.add(aid)
            if draft.get('origin') not in ('openrouter', 'local-cli', 'openai', 'anthropic'):
                raise ValueError('Authored fixtures cannot be imported as model outputs.')
            if not draft.get('model_id') or not draft.get('text', '').strip():
                raise ValueError('Model identity and original output are required.')
            if draft.get('text_sha256') != text_hash(draft['text']):
                raise ValueError('Output hash mismatch.')
            if attempt.get('status') != 'complete' or attempt.get('output_text') != draft['text']:
                raise ValueError('A complete generation record is required for every output.')
            if attempt.get('requested_model') != draft['model_id'] or attempt.get('provider') != draft['origin']:
                raise ValueError('Generation identity does not match the artifact.')
            if not attempt.get('request') or attempt.get('request_sha256') != object_hash(attempt['request']):
                raise ValueError('Generation request hash mismatch.')
            if attempt.get('output_sha256') != draft['text_sha256'] or draft.get('request_sha256') != attempt['request_sha256']:
                raise ValueError('Generation/artifact hash mismatch.')
            request = attempt['request']
            messages = normalized_messages(draft['origin'], request)
            if messages is None and draft['origin'] == 'local-cli':
                messages = [{'role': 'system', 'content': request.get('instructions')},
                            {'role': 'user', 'content': request.get('stdin')}]
            if not messages or len(messages) != 2 or messages[-1] != {'role': 'user', 'content': case['brief']}:
                raise ValueError('Each model must answer the exact approved brief without earlier conversation.')
            common_inputs.append(messages)
            try:
                started = datetime.fromisoformat(attempt['started_at'])
                approved = [datetime.fromisoformat(r['approved_at']) for r in reviewers]
                if not started.tzinfo or any(not dt.tzinfo for dt in approved) or started < max(approved):
                    raise ValueError('Generate only after independent case approval.')
            except (KeyError, TypeError) as exc:
                raise ValueError('Timezone-aware approval and generation timestamps are required.') from exc
            if draft.get('hygiene_flags') or attempt.get('hygiene_flags') or hygiene(draft['text'], case['brief']):
                raise ValueError('Resolve output identity flags before distribution; preserve the rejected attempt.')
        if common_inputs[0] != common_inputs[1]:
            raise ValueError('Both models must receive identical instructions and case facts.')
    return document


def import_pack(db, document):
    validate_pack(document)
    digest = object_hash(document)
    previous = db.get(ClosePack, document['id'])
    if previous:
        if previous.sha256 != digest:
            raise ValueError('A frozen pack cannot be overwritten. Use a new version and ID.')
        return previous
    pack = ClosePack(id=document['id'], sha256=digest, created_at=timestamp(), active=True, data=deepcopy(document))
    db.add(pack)
    db.commit()
    return pack


def assign_cases(db, participant_id):
    existing = list(db.scalars(select(Assignment).where(Assignment.participant_id == participant_id).order_by(Assignment.ordinal)))
    known = {a.id for a in existing}
    candidates = []
    for pack in db.scalars(select(ClosePack).where(ClosePack.active.is_(True)).order_by(ClosePack.created_at)):
        for case in pack.data['cases']:
            aid = text_hash(f'{participant_id}:{pack.id}:{case["id"]}')
            if aid not in known:
                candidates.append((aid, pack.id, case['id']))
    # Stable randomized order for this participant; original assignments never move.
    candidates.sort()
    for offset, (aid, pack_id, case_id) in enumerate(candidates):
        db.add(Assignment(id=aid, participant_id=participant_id, pack_id=pack_id, case_id=case_id,
                          ordinal=len(existing) + offset, created_at=timestamp(), exposure='not-reported'))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Concurrent tabs may allocate the same deterministic assignment IDs.
        # They refer to the same participant and pack; return the committed rows.
    return list(db.scalars(select(Assignment).where(Assignment.participant_id == participant_id).order_by(Assignment.ordinal)))


def assigned_case(db, assignment):
    pack = db.get(ClosePack, assignment.pack_id)
    if not pack or pack.sha256 != object_hash(pack.data):
        raise ValueError('The frozen case pack could not be verified.')
    return pack, next(c for c in pack.data['cases'] if c['id'] == assignment.case_id)
