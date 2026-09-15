"""Collection invariants, not claims about accounting correctness or model quality."""
import asyncio
from copy import deepcopy
import json
import secrets
import pytest
from sqlalchemy import select
from app.pilot_audit import new_attempt, finish_artifact, text_hash, object_hash, GenerationFailure
from app.pilot_study import ClosePack, Assignment, import_pack, validate_pack


def guest(client):
    r = client.post('/api/pilot/guests', json={'source': 'qa-sprint', 'research_consent': False})
    assert r.status_code == 200
    return {'Authorization': 'Bearer ' + r.json()['token']}


def frozen_pack():
    """Explicit synthetic unit-test approvals. Never load into participant data."""
    case = {'id': 'QA-CLOSE-01', 'version': '1', 'title': 'QA test case',
            'brief': 'Fictional test company pays 4800 for twelve months of service. Review the entry.',
            'framework': 'QA supplied policy', 'period': 'September', 'materiality': 'QA test only',
            'evidence': ['QA fixture evidence'],
            'rubric': [{'id': 'R1', 'requirement': 'QA criterion', 'acceptable_alternatives': ['QA alternative'],
                        'source': 'QA source', 'material_error': 'QA definition'}]}
    scope = {k: case[k] for k in ('id', 'version', 'brief', 'framework', 'period', 'materiality', 'evidence')}
    case['validation'] = {'status': 'approved', 'brief_sha256': text_hash(case['brief']),
        'rubric_sha256': object_hash(case['rubric']), 'evidence_sha256': object_hash(case['evidence']),
        'case_sha256': object_hash(scope), 'reconciliation_ref': 'QA-only-not-human-validation',
        'reviewers': [{'id': f'QA-reviewer-{i}', 'independent_review_ref': f'QA-review-{i}',
                       'approved_at': '2020-01-01T00:00:00+00:00', 'qualification': 'Synthetic fixture only'} for i in (1, 2)]}
    drafts = []
    for i in (1, 2):
        model = f'qa/model-{i}'
        request = {'model': model, 'messages': [{'role': 'system', 'content': 'QA instructions'}, {'role': 'user', 'content': case['brief']}]}
        a = new_attempt('openrouter', model, request)
        a['resolved_model'] = model
        drafts.append(finish_artifact(a, f'QA synthetic response {i}: monthly amount 400.', 'accounting-question', {}, 'ask-v3'))
    case['generation_attempts'] = [d.pop('attempt') for d in drafts]
    case['drafts'] = drafts
    return {'schema_version': 'close-pack-v1', 'id': 'qa-pack-' + secrets.token_hex(6), 'cases': [case]}


def test_neutral_prompt_and_editable_starters(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    seen = []
    async def generate(question, task_type):
        seen.append((question, task_type))
        return [{'text': 'QA one'}, {'text': 'QA two'}]
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    cfg = client.get('/api/pilot/config').json()
    starter = cfg['prompt_starters'][0]
    question = starter['brief'].replace('86,400', '90,000')
    h = guest(client)
    r = client.post('/api/pilot/runs', headers=h, json={'question': question, 'source_example_id': starter['id']}).json()
    assert seen == [(question, 'accounting-question')]
    assert r['evaluation_scope'] == 'exploratory-prompt-starter'
    with SessionLocal() as db:
        assert db.get(pilot.Run, r['id']).data['source_example_edited'] is True
    assert client.post('/api/pilot/runs', headers=h, json={'question': question, 'source_example_id': 'invented'}).status_code == 422


def test_followup_uses_owned_selected_response_and_entire_history(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    h, other = guest(client), guest(client)
    source = client.post('/api/pilot/runs', headers=h, json={'case_id': 'insurance-cutoff', 'independent_first': False}).json()
    body = {'question': 'Why?', 'source_run_id': source['id'], 'source_position': 'b', 'continuation_mode': 'followup'}
    assert client.post('/api/pilot/runs', headers=other, json=body).status_code == 404
    assert client.post('/api/pilot/runs', headers=h, json=body).status_code == 409
    client.post(f'/api/pilot/runs/{source["id"]}/preference', headers=h, json={'preference': 'a'})
    calls = []
    async def generate(question, task_type, *, history=None):
        calls.append((question, deepcopy(history)))
        return [{'text': 'QA follow-up one', 'artifact_id': 'qa1'}, {'text': 'QA follow-up two', 'artifact_id': 'qa2'}]
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    child = client.post('/api/pilot/runs', headers=h, json=body).json()
    assert child['evaluation_scope'] == 'exploratory-followup' and child['turn_number'] == 2
    assert calls[0][1] == [{'role': 'user', 'content': source['brief']}, {'role': 'assistant', 'content': source['drafts'][1]['text']}]
    assert all(set(d) == {'position', 'text'} for d in child['drafts'])
    client.post(f'/api/pilot/runs/{child["id"]}/preference', headers=h, json={'preference': 'b'})
    grandchild = client.post('/api/pilot/runs', headers=h, json={**body, 'source_run_id': child['id'], 'question': 'Shorter.'}).json()
    assert grandchild['turn_number'] == 3 and len(calls[1][1]) == 4
    assert calls[1][1][-1]['content'] == child['drafts'][1]['text']
    with SessionLocal() as db:
        assert db.get(pilot.Run, child['id']).data['source_artifact']['text_sha256'] == text_hash(source['drafts'][1]['text'])
        assert db.get(pilot.Run, grandchild['id']).data['root_run_id'] == source['id']
    assert client.post('/api/pilot/runs', headers=h, json={'question': 'Why?', 'continuation_mode': 'followup'}).status_code == 422


def test_context_limit_does_not_silently_drop_messages(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    h = guest(client)
    source = client.post('/api/pilot/runs', headers=h, json={'case_id': 'insurance-cutoff', 'independent_first': False}).json()
    client.post(f'/api/pilot/runs/{source["id"]}/preference', headers=h, json={'preference': 'a'})
    with SessionLocal() as db:
        run = db.get(pilot.Run, source['id'])
        run.data = {**run.data, 'history': [{'role': 'user', 'content': 'x' * 40000}]}
        db.commit()
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'Why?', 'source_run_id': source['id'], 'source_position': 'a', 'continuation_mode': 'followup'})
    assert r.status_code == 422 and 'context limit' in r.json()['detail']


def test_partial_generation_is_saved_privately_and_retry_links(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    h = guest(client)
    attempts = [{'id': 'attempt-one', 'status': 'complete', 'output_text': 'QA response'}, {'id': 'attempt-two', 'status': 'failed', 'error_type': 'TimeoutError'}]
    async def generate(question, task_type):
        raise GenerationFailure('Internal failure detail', attempts)
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    r = client.post('/api/pilot/runs', headers=h, json={'question': 'A fictional question that should be preserved.'}).json()
    assert r['status'] == 'failed' and not r['drafts'] and 'generation_attempts' not in r
    with SessionLocal() as db:
        assert db.get(pilot.Run, r['id']).data['generation_attempts'] == attempts
    retry = client.post('/api/pilot/runs', headers=h, json={'question': r['brief'], 'retry_of_run_id': r['id']}).json()
    assert retry['retry_of_run_id'] == r['id'] and retry['evaluation_scope'] == 'exploratory-retry'


def test_pack_rejects_unapproved_changed_or_unrelated_outputs():
    pack = frozen_pack()
    validate_pack(pack)
    mutations = [
        lambda c: c['validation'].update(status='draft'),
        lambda c: c.update(brief='Changed approved question'),
        lambda c: c.update(framework='Changed framework'),
        lambda c: c['drafts'][0].update(text='Edited output'),
        lambda c: c['drafts'][0].update(origin='authored-fixture'),
        lambda c: c['generation_attempts'][0].update(started_at='2019-01-01T00:00:00+00:00'),
    ]
    for mutate in mutations:
        bad = deepcopy(pack); mutate(bad['cases'][0])
        with pytest.raises(ValueError): validate_pack(bad)
    bad = deepcopy(pack); a = bad['cases'][0]['generation_attempts'][0]
    a['request']['messages'][-1]['content'] = 'Different question'
    a['request_sha256'] = object_hash(a['request'])
    bad['cases'][0]['drafts'][0]['request_sha256'] = a['request_sha256']
    with pytest.raises(ValueError, match='approved brief'): validate_pack(bad)


def test_assignments_are_stable_owned_and_share_exact_outputs(client):
    from app.db import SessionLocal
    from app.routers.pilot import export_data
    pack = frozen_pack()
    with SessionLocal() as db:
        import_pack(db, pack)
        assert import_pack(db, pack).id == pack['id']
        changed = deepcopy(pack); changed['id'] = pack['id']; changed['cases'][0]['title'] = 'Changed'
        with pytest.raises(ValueError, match='cannot be overwritten'): import_pack(db, changed)
    h1, h2 = guest(client), guest(client)
    assignments1 = client.post('/api/pilot/assignments', headers=h1, json={}).json()
    a1 = next(a for a in assignments1 if a['pack_id'] == pack['id'])
    a2 = next(a for a in client.post('/api/pilot/assignments', headers=h2, json={}).json() if a['pack_id'] == pack['id'])
    assert assignments1 == client.post('/api/pilot/assignments', headers=h1, json={}).json()
    assert 'rubric' not in a1 and 'drafts' not in a1
    assert client.post(f'/api/pilot/assignments/{a1["id"]}/start', headers=h2, json={}).status_code == 404
    run1 = client.post(f'/api/pilot/assignments/{a1["id"]}/start', headers=h1, json={}).json()
    run2 = client.post(f'/api/pilot/assignments/{a2["id"]}/start', headers=h2, json={}).json()
    assert {d['text'] for d in run1['drafts']} == {d['text'] for d in run2['drafts']}
    assert all(set(d) == {'position', 'text'} for d in run1['drafts'])
    client.post(f'/api/pilot/runs/{run1["id"]}/preference', headers=h1, json={'preference': 'a'})
    resumed = client.post(f'/api/pilot/assignments/{a1["id"]}/start', headers=h1, json={}).json()
    assert resumed['id'] == run1['id'] and resumed['status'] == 'completed'
    assert [d['text'] for d in resumed['drafts']] == [d['text'] for d in run1['drafts']]
    with SessionLocal() as db:
        exported = export_data(db)
        assert any(a['run_id'] == run1['id'] for a in exported['assignments'])
        assert any(p['id'] == pack['id'] for p in exported['close_packs'])
        db.get(ClosePack, pack['id']).active = False
        db.commit()


def test_openrouter_audit_keeps_exact_context_usage_and_failed_partner(monkeypatch):
    from app import pilot_inference as inference
    for k, v in {'OPENROUTER_API_KEY': 'DO-NOT-RECORD', 'OPENROUTER_MODEL_A': 'qa/a', 'OPENROUTER_MODEL_B': 'qa/b', 'PILOT_INVITE_CODE': 'qa'}.items(): monkeypatch.setenv(k, v)
    monkeypatch.setenv('ARENA_INFERENCE_BACKEND', 'openrouter')
    requests = []
    class Response:
        headers = {'x-request-id': 'qa-request'}
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {'id': 'qa-response', 'model': 'qa/resolved', 'usage': {'prompt_tokens': 12, 'completion_tokens': 5}, 'choices': [{'finish_reason': 'stop', 'message': {'content': '  QA original text\n'}}]}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, headers, json):
            requests.append(json)
            if json['model'] == 'qa/b': raise TimeoutError('DO-NOT-RECORD')
            return Response()
    monkeypatch.setattr(inference.httpx, 'AsyncClient', Client)
    history = [{'role': 'user', 'content': 'Earlier question'}, {'role': 'assistant', 'content': 'Selected answer'}]
    with pytest.raises(GenerationFailure) as error: asyncio.run(inference.generate('Why?', history=history))
    attempts = error.value.attempts
    assert [a['status'] for a in attempts] == ['complete', 'failed']
    assert attempts[0]['output_text'] == '  QA original text\n'
    assert attempts[0]['provider_request_id'] == 'qa-request' and attempts[0]['usage']['prompt_tokens'] == 12
    assert attempts[0]['request']['messages'][1:-1] == history
    assert requests[0]['messages'] == requests[1]['messages']
    assert 'DO-NOT-RECORD' not in json.dumps(attempts)


def test_hygiene_and_export_actions_do_not_create_correctness(client, monkeypatch):
    from app.pilot_audit import hygiene
    monkeypatch.setenv('PILOT_HOST_IDENTIFIERS', 'QA Host Person')
    assert 'host-identifier' in hygiene('Written by QA Host Person')
    assert not hygiene('Contact client@example.test', 'Contact client@example.test')
    assert 'unexpected-email' in hygiene('Prepared by personal@example.test')
    h = guest(client)
    run = client.post('/api/pilot/runs', headers=h, json={'case_id': 'insurance-cutoff', 'independent_first': False}).json()
    payload = {'name': 'response_copied', 'run_id': run['id'], 'position': 'a'}
    assert client.post('/api/pilot/events', headers=h, json=payload).status_code == 422
    client.post(f'/api/pilot/runs/{run["id"]}/preference', headers=h, json={'preference': 'neither'})
    assert client.post('/api/pilot/events', headers=h, json=payload).status_code == 200


def test_direct_adapters_use_common_context_and_do_not_fallback(monkeypatch):
    from app import pilot_direct, pilot_inference
    for k, v in {'ARENA_INFERENCE_BACKEND': 'direct', 'OPENAI_API_KEY': 'SECRET-O', 'ANTHROPIC_API_KEY': 'SECRET-A',
                 'OPENAI_MODEL': 'qa/gpt', 'ANTHROPIC_MODEL': 'qa/claude', 'PILOT_INVITE_CODE': 'qa'}.items():
        monkeypatch.setenv(k, v)
    assert pilot_inference.live_ready()
    seen = []
    class Response:
        status_code = 200
        headers = {'request-id': 'qa-id'}
        def __init__(self, provider): self.provider = provider
        def raise_for_status(self): pass
        def json(self):
            if self.provider == 'openai':
                return {'id': 'qa-response-o', 'model': 'qa/gpt', 'status': 'completed', 'usage': {'input_tokens': 8},
                        'output': [{'type': 'reasoning', 'summary': []}, {'type': 'message', 'role': 'assistant',
                                    'content': [{'type': 'output_text', 'text': 'QA OpenAI answer'}]}]}
            return {'id': 'qa-response-a', 'model': 'qa/claude', 'stop_reason': 'end_turn', 'usage': {'input_tokens': 8},
                    'content': [{'type': 'text', 'text': 'QA Claude answer'}]}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, headers, json):
            seen.append((url, json))
            return Response('openai' if 'api.openai.com' in url else 'anthropic')
    monkeypatch.setattr(pilot_direct.httpx, 'AsyncClient', Client)
    history = [{'role': 'user', 'content': 'Prior question'}, {'role': 'assistant', 'content': 'Chosen response'}]
    drafts = asyncio.run(pilot_inference.generate('Why?', history=history))
    assert len(seen) == 2 and {d['origin'] for d in drafts} == {'openai', 'anthropic'}
    assert seen[0][1]['instructions'] == seen[1][1]['system']
    assert seen[0][1]['input'] == seen[1][1]['messages'] == [*history, {'role': 'user', 'content': 'Why?'}]
    assert seen[0][1]['store'] is False
    assert 'SECRET' not in json.dumps(drafts)
    assert [d['attempt']['provider_response_id'] for d in drafts] == ['qa-response-o', 'qa-response-a']
    monkeypatch.delenv('ANTHROPIC_API_KEY')
    assert not pilot_inference.live_ready()


def test_audit_detects_tampering_and_consent_boundaries():
    from pipeline.audit_pilot import audit
    d = finish_artifact(new_attempt('openrouter', 'qa/a', {'messages': []}), 'QA output', 'accounting-question', {}, 'ask-v3')
    attempt = d.pop('attempt')
    second = finish_artifact(new_attempt('openrouter', 'qa/b', {'messages': []}), 'QA other output', 'accounting-question', {}, 'ask-v3')
    second_attempt = second.pop('attempt')
    data = {'participants': [{'id': 'qa-person', 'source': 'qa-sprint', 'research_consent': False}],
            'runs': [{'id': 'qa-run', 'participant_id': 'qa-person', 'status': 'review', 'version': 'ask-v3',
                      'drafts': [d, second], 'generation_attempts': [attempt, second_attempt]}], 'events': []}
    assert audit(data)['ok']
    assert audit(data)['research_eligible_runs'] == 0
    duplicate = deepcopy(data)
    duplicate['runs'][0]['drafts'][1] = deepcopy(d)
    assert not audit(duplicate)['ok']
    data['runs'][0]['drafts'][0]['text'] = 'Tampered output'
    assert not audit(data)['ok']
