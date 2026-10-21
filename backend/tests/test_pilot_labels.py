"""Project labels: takeaway titles and categories for new questions, with a keyword fallback."""
import asyncio
import json

from app import pilot_labels as labels
from test_pilot import enroll


def test_keyword_category_picks_a_workflow_or_open():
    assert labels.keyword_category('Reconcile the bank statement to the cash ledger') == 'bank-reconciliation'
    assert labels.keyword_category('Build the Q3 AR aging by customer') == 'ar-reporting'
    assert labels.keyword_category('Prepare the October invoice under SOW #3') == 'invoicing'
    assert labels.keyword_category('How are employee wellness stipends taxed?') == 'open'


def test_model_reply_is_validated():
    good = labels.clean('Sure: {"title": "Wellness stipend tax treatment.", "category": "open", "topic": "Fringe benefits"}')
    assert good == {'title': 'Wellness stipend tax treatment', 'category': 'open', 'topic': 'Fringe benefits'}
    assert labels.clean('{"title": "Fine", "category": "payroll"}') is None
    assert labels.clean('{"title": "' + 'x' * 80 + '", "category": "open"}') is None
    assert labels.clean('no json here') is None


def test_label_question_uses_the_model_and_falls_back(monkeypatch):
    monkeypatch.setenv('ARENA_RUN_LABELS', 'model')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')

    async def reply(question):
        return json.dumps({'title': 'Three-year SaaS contract revenue', 'category': 'open', 'topic': 'Revenue recognition'})
    monkeypatch.setattr(labels, 'ask_anthropic', reply)
    result = asyncio.run(labels.label_question('We signed a three-year SaaS contract.', 'direct'))
    assert result == {'title': 'Three-year SaaS contract revenue', 'category': 'open', 'topic': 'Revenue recognition', 'label_source': 'model'}

    async def broken(question):
        raise RuntimeError('provider down')
    monkeypatch.setattr(labels, 'ask_anthropic', broken)
    result = asyncio.run(labels.label_question('Reconcile the bank statement.', 'direct'))
    assert result == {'category': 'bank-reconciliation', 'topic': None, 'label_source': 'keyword'}


def test_new_question_is_labeled_and_follow_ups_keep_the_thread_label(client, monkeypatch):
    from app.routers import pilot

    async def generate(question, task_type, history=None):
        return [{'text': 'A response', 'author': f'model-{i}', 'model_id': f'model-{i}', 'origin': 'openrouter'} for i in range(2)]

    async def label(question, backend):
        return {'title': 'Wellness stipend tax treatment', 'category': 'open', 'topic': 'Fringe benefits', 'label_source': 'model'}
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    monkeypatch.setattr(pilot.pilot_labels, 'label_question', label)
    h = enroll(client)
    first = client.post('/api/pilot/runs', headers=h, json={'question': 'Every month I factor in employee gym and wellness stipends. How are they taxed?'}).json()
    assert (first['title'], first['category'], first['topic']) == ('Wellness stipend tax treatment', 'open', 'Fringe benefits')

    async def unused(question, backend):
        raise AssertionError('follow-ups keep the thread label')
    monkeypatch.setattr(pilot.pilot_labels, 'label_question', unused)
    follow = client.post('/api/pilot/runs', headers=h, json={'question': 'And medical expenses?', 'source_run_id': first['id'], 'continuation_mode': 'compare'}).json()
    assert (follow['title'], follow['category'], follow['topic']) == ('Wellness stipend tax treatment', 'open', 'Fringe benefits')


def test_a_chosen_workflow_wins_the_category():
    from app.routers.pilot import apply_labels
    update = apply_labels({'title': 'October Sunset Hotel invoice', 'category': 'open', 'topic': 'Billing', 'label_source': 'model'}, 'invoicing')
    assert update['category'] == 'invoicing' and update['title'] == 'October Sunset Hotel invoice'
    assert apply_labels({'category': 'open', 'topic': None, 'label_source': 'keyword'}, None) == {'category': 'open', 'topic': None, 'label_source': 'keyword'}
