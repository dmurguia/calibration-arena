"""Pilot contract tests: privacy boundaries, atomic transitions and research provenance."""
import asyncio
import json
import pytest

PROFILE = dict(name="Pilot test", role="Public accountant", experience="3–7 years", framework="US GAAP", research_consent=True)
JUDGMENT = dict(a="revise", b="revise", preference="neither", reasons=["Timing"], confidence="medium", rationale="Check the actual service period", correction="")


def enroll(client):
    r = client.post('/api/pilot/participants', json=PROFILE)
    assert r.status_code == 200, r.text
    return {"Authorization": 'Bearer ' + r.json()['token']}


def start(client, h):
    r = client.post('/api/pilot/runs', headers=h, json={"case_id": "insurance-cutoff"})
    assert r.status_code == 200, r.text
    return r.json()


def test_challenge_blinding_and_immutable_judgment(client):
    h = enroll(client)
    run = start(client, h)
    path = '/api/pilot/runs/' + run['id']
    assert run['status'] == 'conclusion' and run['drafts'] == []
    assert 'expected' not in run
    assert client.post(path + '/judgment', headers=h, json=JUDGMENT).status_code == 409
    assert client.post(path + '/conclusion', headers=h, json={"conclusion": " "}).status_code == 422
    r = client.post(path + '/conclusion', headers=h, json={"conclusion": "Expense starts in April, not March."})
    assert r.status_code == 200, r.text
    assert len(r.json()['drafts']) == 2
    assert all(set(d) == {'position', 'text'} for d in r.json()['drafts'])
    assert client.post(path + '/conclusion', headers=h, json={"conclusion": "Change the independent call."}).status_code == 409
    r = client.post(path + '/judgment', headers=h, json=JUDGMENT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['status'] == 'completed'
    assert 'March insurance expense is $0' in data['expected']
    assert data['judgment']['decision_ms'] >= 0
    assert all(d['author'] == 'Authored practice draft' for d in data['drafts'])
    assert sorted(d['checks'][1]['passed'] for d in data['drafts']) == [False, True]
    assert client.post(path + '/judgment', headers=h, json=JUDGMENT).status_code == 409
    assert client.post(path + '/feedback', headers=h, json={"usefulness": "useful", "note": "The timing check helped."}).status_code == 200
    assert client.get('/api/pilot/me', headers=h).json()['runs'][0]['feedback']['usefulness'] == 'useful'


def test_cross_participant_access_denied(client):
    a, b = enroll(client), enroll(client)
    run = start(client, a)
    path = '/api/pilot/runs/' + run['id']
    assert client.get(path, headers=b).status_code == 404
    assert client.get(path).status_code == 401
    assert client.post(path + '/conclusion', headers=b, json={"conclusion": "A different person's answer"}).status_code == 404
    assert client.post('/api/pilot/events', headers=b, json={"name": "left_session", "run_id": run['id']}).status_code == 404


def test_optional_research_and_no_implicit_contact(client):
    result = client.post('/api/pilot/participants', json={**PROFILE, 'research_consent': False})
    assert result.status_code == 200
    assert result.json()['participant']['consent_at'] is None
    assert client.post('/api/pilot/participants', json={**PROFILE, 'email': 'test@example.com'}).status_code == 422
    assert client.post('/api/pilot/participants', json={**PROFILE, 'followup': True}).status_code == 422


def test_invite_and_founder_boundaries(client, monkeypatch):
    monkeypatch.setenv('PILOT_INVITE_CODE', 'test-cohort')
    assert client.post('/api/pilot/participants', json=PROFILE).status_code == 403
    response = client.post('/api/pilot/participants', json={**PROFILE, 'invite_code': 'test-cohort'})
    assert response.status_code == 200
    assert 'invite_code' not in response.json()['participant']
    assert client.get('/api/pilot/founder/export').status_code == 403
    monkeypatch.setenv('PILOT_ADMIN_TOKEN', 'a-long-private-test-admin-token')
    data = client.get('/api/pilot/founder/export', headers={'X-Pilot-Admin': 'a-long-private-test-admin-token'}).json()
    assert data['schema_version'] == 'pilot-export-v1'
    assert all('token_hash' not in p and 'token' not in p for p in data['participants'])
    assert all(p['publication_consent'] is False and p['training_consent'] is False for p in data['participants'])
    assert not any('synthetic' in e['name'] for e in data['events'])


def test_unconnected_ask_never_substitutes_static_answers(client, monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    h = enroll(client)
    question = 'How should an annual software fee be recognized under my stated accrual policy?'
    response = client.post('/api/pilot/runs', headers=h, json={'question': question})
    assert response.status_code == 503
    assert 'not been replaced' in response.json()['detail']
    assert client.get('/api/pilot/me', headers=h).json()['runs'] == []


def test_generation_failure_is_recorded_not_replaced(client, monkeypatch):
    from app.routers import pilot
    async def failed(question, task_type):
        raise ValueError('Provider unavailable')
    monkeypatch.setattr(pilot, 'generate', failed)
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    h = enroll(client)
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'A hypothetical question about annual insurance expense.', 'privacy_ack': True})
    assert r.status_code == 200
    assert r.json()['status'] == 'failed'
    assert r.json()['drafts'] == []
    assert client.post('/api/pilot/runs/' + r.json()['id'] + '/judgment', headers=h, json=JUDGMENT).status_code == 409


def test_judgment_validation(client):
    h = enroll(client); run = start(client, h); path = '/api/pilot/runs/' + run['id']
    client.post(path + '/conclusion', headers=h, json={'conclusion': 'The dates should drive the recognition.'})
    for change in [dict(reasons=[]), dict(confidence='certain'), dict(a='ready'), dict(reasons=['Other'], rationale='')]:
        assert client.post(path + '/judgment', headers=h, json={**JUDGMENT, **change}).status_code == 422


def test_cases_checks_derive_from_postings():
    from app.pilot_cases import CASES, checks, snapshot
    frozen = [snapshot(c) for c in CASES]
    assert len(frozen) == 5
    assert sum(all(d['checks'][1]['passed'] for d in c['drafts']) for c in frozen) == 2
    d = frozen[0]['drafts'][0]
    assert all(c['passed'] for c in checks(d))
    d['postings'][0][2] += 1
    assert not any(c['passed'] for c in checks(d))
    assert all(c['passed'] for c in snapshot(CASES[0])['drafts'][0]['checks'])


def test_matched_live_payload_and_provider_error(monkeypatch):
    from app import pilot_inference as inference
    for k, v in dict(OPENROUTER_API_KEY='test-key', OPENROUTER_MODEL_A='provider/a', OPENROUTER_MODEL_B='provider/b', PILOT_INVITE_CODE='test').items():
        monkeypatch.setenv(k, v)
    sent = []
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'choices': [{'message': {'content': 'A useful response'}}], 'model': 'actual-version'}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, headers, json): sent.append(json); return Response()
    monkeypatch.setattr(inference.httpx, 'AsyncClient', Client)
    data = asyncio.run(inference.generate('Preserve this exact accounting question.', 'treatment-memo'))
    assert len(sent) == 2
    assert sent[0]['messages'] == sent[1]['messages']
    assert 'treatment memo' in sent[0]['messages'][0]['content']
    assert sent[0]['messages'][1]['content'] == 'Preserve this exact accounting question.'
    assert sent[0]['model'] != sent[1]['model']
    assert sent[0]['temperature'] == sent[1]['temperature']
    assert sent[0]['provider'] == {'data_collection': 'deny', 'zdr': True, 'allow_fallbacks': False}
    assert data[0]['actual_model_id'] == 'actual-version'
    monkeypatch.setenv('OPENROUTER_MODEL_B', 'provider/a')
    assert not inference.live_ready()


def test_daily_limit(client):
    from app.db import SessionLocal
    from app.routers.pilot import Run, Participant, now
    from sqlalchemy import select
    h = enroll(client)
    pid = client.get('/api/pilot/me', headers=h).json()['participant']['id']
    with SessionLocal() as db:
        for i in range(20): db.add(Run(id=f'{pid}-{i}', participant_id=pid, created_at=now(), status='failed', data={}))
        db.commit()
    assert client.post('/api/pilot/runs', headers=h, json={'case_id': 'insurance-cutoff'}).status_code == 429


def test_guest_sees_value_before_background_and_keeps_ownership(client):
    guest = client.post('/api/pilot/guests', json={'research_consent': True, 'source': 'peer-share'}).json()
    h = {'Authorization': 'Bearer ' + guest['token']}
    assert guest['participant']['identity'] == 'guest'
    assert guest['participant']['role'] == 'Not supplied'
    run = start(client, h)
    result = client.post('/api/pilot/profile', headers=h, json=PROFILE)
    assert result.status_code == 200, result.text
    data = client.get('/api/pilot/me', headers=h).json()
    assert data['participant']['identity'] == 'self-reported'
    assert data['participant']['id'] == guest['participant']['id']
    assert data['participant']['source'] == 'peer-share'
    assert data['runs'][0]['id'] == run['id']


def test_guest_does_not_infer_consent_but_still_checks_invite(client, monkeypatch):
    guest = client.post('/api/pilot/guests', json={}).json()['participant']
    assert guest['research_consent'] is False
    assert guest['consent_at'] is None and guest['consent_version'] is None
    monkeypatch.setenv('PILOT_INVITE_CODE', 'pilot-test')
    assert client.post('/api/pilot/guests', json={'research_consent': True}).status_code == 403
    assert client.post('/api/pilot/guests', json={'research_consent': True, 'invite_code': 'pilot-test'}).status_code == 200



def test_export_retains_session_ids_not_case_ids(client):
    from app.db import SessionLocal
    from app.routers.pilot import export_data
    h = enroll(client)
    run = start(client, h)
    with SessionLocal() as db:
        data = export_data(db)
    exported = next(r for r in data['runs'] if r['id'] == run['id'])
    assert exported['case_id'] == 'insurance-cutoff'
    assert any(e['run_id'] == exported['id'] and e['name'] == 'session_started' for e in data['events'])
    ids = {r['id'] for r in data['runs']}
    assert all(e['run_id'] in ids for e in data['events'] if e['run_id'])



def test_live_task_type_preserves_prompt_and_does_not_invent_ack(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    sent = []
    async def generate(question, task_type):
        sent.append((question, task_type))
        return [{'text': 'A response', 'author': 'test-model', 'origin': 'openrouter'} for _ in range(2)]
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    h = enroll(client)
    question = 'Draft a treatment memo on this hypothetical reporting issue.'
    response = client.post('/api/pilot/runs', headers=h, json={'question': question, 'task_type': 'treatment-memo'})
    assert response.status_code == 200
    data = response.json()
    assert data['brief'] == question and data['task_type'] == 'treatment-memo'
    assert data['mode'] == 'openrouter' and data['status'] == 'review'
    assert sent == [(question, 'treatment-memo')]
    with SessionLocal() as db:
        run = db.get(pilot.Run, data['id'])
        assert run.data['privacy_ack'] is False
        assert run.data['routing'] == 'explicit-user-selection'


def test_samples_are_explicit_not_prompt_routing(client):
    h = enroll(client)
    sample = next(c for c in client.get('/api/pilot/cases').json() if c['id'] == 'utilities-accrual')
    assert sample['task_type'] == 'workpaper-review'
    response = client.post('/api/pilot/runs', headers=h, json={'case_id': sample['id'], 'question': sample['brief'], 'task_type': 'workpaper-review'})
    assert response.status_code == 200
    assert response.json()['mode'] == 'authored-fixture'
    assert response.json()['drafts'] == []
    assert response.json()['task_type'] == 'workpaper-review'
    assert client.post('/api/pilot/runs', headers=h, json={'case_id': sample['id'], 'question': 'This is a changed prompt with different numbers.'}).status_code == 422
    assert client.post('/api/pilot/runs', headers=h, json={'question': sample['brief'], 'task_type': 'imaginary-category'}).status_code == 422
