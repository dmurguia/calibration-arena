"""COR-357: explicit configurable limits, reservations, bounded concurrency,
generation pause. All providers mocked — no live credentials."""
import asyncio
import threading
import time
from datetime import datetime, timezone

from sqlalchemy import select

PROFILE = dict(name="Limit test", role="Public accountant", experience="3–7 years", framework="US GAAP")


def guest(client):
    r = client.post('/api/pilot/guests', json={'source': 'qa-limits'})
    assert r.status_code == 200, r.text
    return {'Authorization': 'Bearer ' + r.json()['token']}


def live_generate(texts=('QA one', 'QA two'), attempt=None):
    async def generate(*args, **kwargs):
        drafts = [{'text': t} for t in texts]
        if attempt:
            for d in drafts:
                d['attempt'] = dict(attempt)
        return drafts
    return generate


def reservations_for(db, participant_id):
    from app.pilot_limits import PilotReservation
    return db.scalars(select(PilotReservation).where(PilotReservation.participant_id == participant_id)).all()


def test_pause_blocks_generation_but_preserves_prompt_and_reads(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', live_generate())
    monkeypatch.setenv('PILOT_ADMIN_TOKEN', 'a-long-private-test-admin-token')
    admin = {'X-Pilot-Admin': 'a-long-private-test-admin-token'}
    assert client.post('/api/pilot/founder/generation', headers=admin, json={'paused': True, 'note': 'launch freeze'}).json()['paused'] is True
    assert client.get('/api/pilot/config').json()['generation_paused'] is True

    h = guest(client)
    question = 'A question asked while generation is paused.'
    r = client.post('/api/pilot/runs', headers=h, json={'question': question})
    assert r.status_code == 503 and 'paused' in r.json()['detail']
    me = client.get('/api/pilot/me', headers=h).json()
    failed = next(r for r in me['runs'] if r['brief'] == question)
    assert failed['status'] == 'failed' and 'paused' in failed['limit_rejection']
    # Notebooks and authored fixtures stay readable while paused.
    assert client.post('/api/pilot/runs', headers=h, json={'case_id': 'insurance-cutoff'}).status_code == 200

    state = client.get('/api/pilot/founder/generation', headers=admin).json()
    assert state['flag_paused'] is True and state['flag_note'] == 'launch freeze'
    assert client.post('/api/pilot/founder/generation', headers=admin, json={'paused': False}).json()['paused'] is False
    assert client.post('/api/pilot/runs', headers=h, json={'question': question + ' again'}).json()['status'] == 'review'
    with SessionLocal() as db:
        pid = me['participant']['id']
        assert sorted(r.status for r in reservations_for(db, pid)) == ['expired', 'reconciled']


def test_env_pause_overrides_flag(client, monkeypatch):
    from app.routers import pilot
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setenv('PILOT_GENERATION_PAUSED', '1')
    h = guest(client)
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'Blocked by the env kill switch.'})
    assert r.status_code == 503


def test_participant_budget_rejects_and_preserves_prompt(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', live_generate())
    monkeypatch.setenv('PILOT_GUEST_TOKEN_BUDGET', '1')
    h = guest(client)
    question = 'My budget question should survive the rejection.'
    r = client.post('/api/pilot/runs', headers=h, json={'question': question})
    assert r.status_code == 402 and 'included model tokens' in r.json()['detail']
    me = client.get('/api/pilot/me', headers=h).json()
    run = next(r for r in me['runs'] if r['brief'] == question)
    assert run['status'] == 'failed' and 'included model tokens' in run['limit_rejection']
    with SessionLocal() as db:
        assert reservations_for(db, me['participant']['id'])[0].status == 'expired'


def test_concurrency_bounds_per_participant_and_global(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    from app.pilot_limits import PilotReservation
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', live_generate())
    h = guest(client)
    me = client.get('/api/pilot/me', headers=h).json()
    pid = me['participant']['id']
    iso = datetime.now(timezone.utc).isoformat()
    with SessionLocal() as db:
        db.add(PilotReservation(id='held-by-me', participant_id=pid, run_id='x1',
                                reserved_tokens=10, status='active', created_at=iso))
        db.commit()
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'A second concurrent request from me.'})
    assert r.status_code == 429 and 'already generating' in r.json()['detail']
    with SessionLocal() as db:
        held = db.get(PilotReservation, 'held-by-me')
        held.status = 'reconciled'
        held.counted_tokens = 0
        for i in range(4):
            db.add(PilotReservation(id=f'other-{i}', participant_id=f'other-{i}', run_id=f'o{i}',
                                    reserved_tokens=10, status='active', created_at=iso))
        db.commit()
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'A request while the service is saturated.'})
    assert r.status_code == 429 and 'at capacity' in r.json()['detail']
    with SessionLocal() as db:
        assert db.get(PilotReservation, 'held-by-me').status == 'reconciled'
        for i in range(4):
            other = db.get(PilotReservation, f'other-{i}')
            other.status = 'reconciled'
            other.counted_tokens = 0
        db.commit()


def test_missing_usage_counts_reservation_not_zero(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', live_generate())  # drafts carry no attempt usage
    h = guest(client)
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'Providers that do not report usage.'})
    assert r.json()['status'] == 'review'
    me = client.get('/api/pilot/me', headers=h).json()
    with SessionLocal() as db:
        reservation = reservations_for(db, me['participant']['id'])[0]
        assert reservation.status == 'reconciled'
        assert reservation.counted_tokens == reservation.reserved_tokens
        assert me['usage']['used'] == reservation.reserved_tokens > 0


def test_partial_failure_reconciles_and_retry_gets_own_reservation(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    from app.pilot_audit import GenerationFailure
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    attempts = [{'status': 'complete', 'usage': {'input_tokens': 5, 'output_tokens': 5}},
                {'status': 'failed', 'error_type': 'TimeoutError'}]

    async def fail(*args, **kwargs):
        raise GenerationFailure('one side timed out', attempts)

    monkeypatch.setattr(pilot, 'generate', fail)
    h = guest(client)
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'A partially failing generation.'})
    assert r.json()['status'] == 'failed'
    me = client.get('/api/pilot/me', headers=h).json()
    with SessionLocal() as db:
        reservation = reservations_for(db, me['participant']['id'])[0]
        assert reservation.status == 'reconciled'
        # One side reported 10 tokens; the failed side counts at the remainder.
        assert reservation.counted_tokens == reservation.reserved_tokens - 10
        assert me['usage']['used'] == 10 + reservation.reserved_tokens - 10

    monkeypatch.setattr(pilot, 'generate', live_generate(attempt={'status': 'complete', 'usage': {'input_tokens': 3, 'output_tokens': 3}}))
    retry = client.post('/api/pilot/runs', headers=h, json={'question': r.json()['brief'], 'retry_of_run_id': r.json()['id']})
    assert retry.json()['status'] == 'review'
    with SessionLocal() as db:
        rows = reservations_for(db, me['participant']['id'])
        assert len(rows) == 2 and all(row.status == 'reconciled' for row in rows)
        assert rows[1].run_id == retry.json()['id'] and rows[1].counted_tokens == 0
    # 10 recorded + 6 per draft-attempt on the retry (12) + the failed run's
    # unreported remainder (reserved - 10).
    assert client.get('/api/pilot/me', headers=h).json()['usage']['used'] == rows[0].reserved_tokens + 12


def test_generation_timeout_fails_and_reconciles(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setenv('PILOT_GENERATION_TIMEOUT_SECONDS', '1')

    async def slow(*args, **kwargs):
        await asyncio.sleep(30)
        return [{'text': 'late'}]

    monkeypatch.setattr(pilot, 'generate', slow)
    h = guest(client)
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'A generation that overruns.'})
    assert r.json()['status'] == 'failed'
    with SessionLocal() as db:
        run = db.get(pilot.Run, r.json()['id'])
        assert run.data['generation_error_type'] == 'TimeoutError'
        reservation = reservations_for(db, run.participant_id)[0]
        assert reservation.status == 'reconciled'


def test_overlapping_requests_only_one_generates(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    from app.pilot_limits import PilotReservation
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    gate = threading.Event()

    async def gated(*args, **kwargs):
        deadline = time.monotonic() + 10
        while not gate.is_set() and time.monotonic() < deadline:
            await asyncio.sleep(0.02)
        return [{'text': 'gated one'}, {'text': 'gated two'}]

    monkeypatch.setattr(pilot, 'generate', gated)
    h = guest(client)
    pid = client.get('/api/pilot/me', headers=h).json()['participant']['id']
    results = []

    def ask(tag):
        r = client.post('/api/pilot/runs', headers=h, json={'question': f'Concurrent question {tag}.'})
        results.append(r.status_code)

    first = threading.Thread(target=ask, args=('a',))
    first.start()
    for _ in range(500):  # wait until request a holds its slot
        with SessionLocal() as db:
            if db.scalars(select(PilotReservation).where(
                    PilotReservation.participant_id == pid, PilotReservation.status == 'active')).first():
                break
        time.sleep(0.02)
    ask('b')
    gate.set()
    first.join(timeout=15)
    assert sorted(results) == [200, 429]


def test_founder_generation_requires_admin(client, monkeypatch):
    monkeypatch.setenv('PILOT_ADMIN_TOKEN', 'a-long-private-test-admin-token')
    assert client.get('/api/pilot/founder/generation').status_code == 403
    assert client.post('/api/pilot/founder/generation', json={'paused': True}).status_code == 403


def test_daily_run_limit_is_configurable(client, monkeypatch):
    from app.routers import pilot
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', live_generate())
    monkeypatch.setenv('PILOT_DAILY_RUN_LIMIT', '2')
    h = guest(client)
    for i in range(2):
        assert client.post('/api/pilot/runs', headers=h, json={'question': f'Question number {i} today.'}).status_code == 200
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'One question too many today.'})
    assert r.status_code == 429 and '2-session limit' in r.json()['detail']
