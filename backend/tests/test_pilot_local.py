"""Local CLI integration: process isolation, source provenance and loopback access."""
import asyncio
import json
import sys
import pytest
from fastapi.testclient import TestClient
from app import pilot_local as local


def codex_result(text='Codex draft'):
    return '\n'.join(json.dumps(e) for e in [
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': text}},
        {'type': 'turn.completed'},
    ])


def claude_result(text='Claude draft'):
    return json.dumps({'subtype': 'success', 'result': text, 'is_error': False,
                      'modelUsage': {'claude-test-model': {}}, 'permission_denials': []})


def configure(monkeypatch):
    monkeypatch.setenv('ARENA_INFERENCE_BACKEND', 'local-cli')
    monkeypatch.setenv('LOCAL_CODEX_MODEL', 'codex-test-model')
    monkeypatch.setenv('LOCAL_CLAUDE_MODEL', 'claude-test-model')
    monkeypatch.setattr(local, 'binaries', lambda: ('/test/codex', '/test/claude'))


def test_local_pair_preserves_input_and_provenance(monkeypatch):
    configure(monkeypatch)
    calls = []
    async def execute(args, prompt, directory):
        calls.append((args, prompt, directory))
        return codex_result() if args[0] == '/test/codex' else claude_result()
    monkeypatch.setattr(local, 'execute', execute)
    from app.pilot_inference import generate
    question = 'Review the entry literally: $(touch /tmp/never-execute); `whoami`'
    drafts = asyncio.run(generate(question, 'workpaper-review'))
    assert [c[1] for c in calls] == [question, question]
    assert all(question not in c[0] for c in calls)  # stdin, never command construction
    assert calls[0][2] == calls[1][2]
    assert all(d['origin'] == 'local-cli' and d['settings']['temperature'] is None for d in drafts)
    assert drafts[0]['actual_model_id'] is None
    assert drafts[1]['actual_model_id'] == 'claude-test-model'
    assert all(d['task_type'] == 'workpaper-review' for d in drafts)
    assert '--ignore-user-config' in calls[0][0] and '--ephemeral' in calls[0][0]
    assert '--safe-mode' in calls[1][0] and '--no-session-persistence' in calls[1][0]
    assert calls[1][0][calls[1][0].index('--tools') + 1] == ''
    codex_instructions = next(a for a in calls[0][0] if a.startswith('developer_instructions='))
    assert json.loads(codex_instructions.split('=', 1)[1]) == calls[1][0][-1]


def test_local_partial_failure_never_substitutes(monkeypatch):
    configure(monkeypatch)
    async def execute(args, prompt, directory):
        if args[0] == '/test/codex':
            raise ValueError('secret stderr must not appear')
        return claude_result()
    monkeypatch.setattr(local, 'execute', execute)
    with pytest.raises(ValueError, match='Both local answers') as error:
        asyncio.run(local.generate_local('question', 'instruction', 'journal-entry'))
    assert 'secret' not in str(error.value)


def test_local_parsers_reject_errors_tools_and_incomplete_results():
    diagnostic = {'type': 'item.completed', 'item': {'type': 'error', 'message': 'Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`.'}}
    assert local.parse_codex(json.dumps(diagnostic) + '\n' + codex_result())[0] == 'Codex draft'
    with pytest.raises(ValueError):
        local.parse_codex(codex_result() + '\n' + json.dumps({'type': 'turn.failed'}))
    with pytest.raises(ValueError):
        local.parse_codex(json.dumps({'type': 'item.completed', 'item': {'type': 'command_execution'}}))
    with pytest.raises(ValueError):
        local.parse_claude(json.dumps({'subtype': 'success', 'is_error': True}))
    with pytest.raises(ValueError):
        local.parse_claude(json.dumps({'subtype': 'error_max_turns', 'result': 'partial'}))


def test_child_environment_does_not_forward_app_secrets(monkeypatch):
    for key in ('OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY', 'PILOT_ADMIN_TOKEN', 'CODEX_THREAD_ID', 'CLAUDECODE'):
        monkeypatch.setenv(key, 'sensitive')
        assert key not in local.child_env()
    assert 'HOME' in local.child_env()


def test_process_timeout_is_bounded(monkeypatch, tmp_path):
    monkeypatch.setattr(local, '_TIMEOUT', 0.1)
    with pytest.raises(TimeoutError):
        asyncio.run(local.execute([sys.executable, '-c', 'import time;time.sleep(30)'], '', str(tmp_path)))


def test_local_server_rejects_remote_and_cross_origin(client, monkeypatch):
    configure(monkeypatch)
    from app.main import app
    with TestClient(app, base_url='http://127.0.0.1:8021', client=('127.0.0.1', 5555)) as c:
        assert c.get('/api/pilot/config').json()['ask_mode'] == 'live'
        for headers in ({'Origin': 'https://unrelated.example'}, {'Host': 'unrelated.example'},
                        {'X-Forwarded-For': '203.0.113.1'}, {'Sec-Fetch-Site': 'cross-site'}):
            assert c.get('/api/pilot/config', headers=headers).status_code == 403
        assert c.get('/api/pilot/config', headers={'Origin': 'http://127.0.0.1:8021'}).status_code == 200
    with TestClient(app, base_url='http://127.0.0.1:8021', client=('203.0.113.1', 5555)) as c:
        assert c.get('/api/pilot/config').status_code == 403


def test_local_run_remains_blind_and_records_correct_source(client, monkeypatch):
    configure(monkeypatch)
    from app.main import app
    from app.routers import pilot
    async def generate(question, task_type):
        return [dict(text='Draft ' + name, author=name, origin='local-cli', model_id=name, checks=[]) for name in ('Codex', 'Claude Code')]
    monkeypatch.setattr(pilot, 'generate', generate)
    with TestClient(app, base_url='http://127.0.0.1:8021', client=('127.0.0.1', 5555)) as c:
        auth = c.post('/api/pilot/guests', json={}).json()
        headers = {'Authorization': 'Bearer ' + auth['token']}
        run = c.post('/api/pilot/runs', headers=headers, json={'question': 'How should prepaid insurance be recorded?'}).json()
        assert run['mode'] == 'local-cli' and run['status'] == 'review'
        assert all(set(d) == {'position', 'text'} for d in run['drafts'])
        revealed = c.post('/api/pilot/runs/' + run['id'] + '/judgment', headers=headers,
                          json=dict(a='revise', b='revise', preference='tie', reasons=['Clarity'], confidence='low')).json()
        assert {d['author'] for d in revealed['drafts']} == {'Codex', 'Claude Code'}
