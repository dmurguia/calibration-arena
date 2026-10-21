from app import pilot_artifacts
from app.pilot_audit import finish_artifact, new_attempt

RESPONSE = """Framework: US GAAP (ASC 340).

**Proposed entry**

```artifact kind="journal-entry" title="March 15 payment"
| Account | Debit | Credit |
|---|---|---|
| Prepaid insurance | 14,400 | |
| Cash | | 14,400 |
```

Coverage begins in April, so no March amortization.

### Amortization schedule

| Month | Expense | Remaining |
|---|---|---|
| Apr | 1,200 | 13,200 |

Open questions:
- Confirm the policy dates.

```
Dr Utilities expense    2,400
Cr Accrued liabilities  2,400
```
"""


def test_split_lifts_fenced_tables_and_entries_out_of_the_narrative():
    narrative, artifacts = pilot_artifacts.split(RESPONSE)
    assert [a['kind'] for a in artifacts] == ['journal-entry', 'schedule', 'journal-entry']
    assert artifacts[0]['title'] == 'March 15 payment' and artifacts[0]['source'] == 'fenced'
    assert artifacts[1]['title'] == 'Amortization schedule' and artifacts[1]['source'] == 'table'
    assert artifacts[2]['source'] == 'code-block' and 'Dr Utilities' in artifacts[2]['content']
    assert '| Prepaid insurance' not in narrative and '| Apr |' not in narrative
    assert '*↓ Journal entry: March 15 payment*' in narrative and '*↓ Schedule: Amortization schedule*' in narrative
    assert '### Amortization schedule' not in narrative, 'a heading that names the artifact moves with it'
    assert narrative.startswith('Framework: US GAAP') and 'Confirm the policy dates.' in narrative
    assert all(set(a) == {'id', 'kind', 'title', 'format', 'content', 'source'} for a in artifacts)


def test_split_leaves_plain_prose_alone():
    assert pilot_artifacts.split('Ask the preparer for the policy dates first.') == ('Ask the preparer for the policy dates first.', [])
    assert pilot_artifacts.split('') == ('', [])


def test_finish_artifact_keeps_text_verbatim_and_adds_the_split():
    attempt = new_attempt('openrouter', 'model-x', {'messages': []})
    attempt['resolved_model'] = 'model-x'
    draft = finish_artifact(attempt, RESPONSE, 'journal-entry', {}, 'ask-v4')
    assert draft['text'] == RESPONSE and len(draft['artifacts']) == 3
    assert pilot_artifacts.public(draft) == {'narrative': draft['narrative'], 'artifacts': draft['artifacts']}


def test_public_view_derives_from_text_for_older_drafts():
    view = pilot_artifacts.public({'text': RESPONSE, 'author': 'secret'})
    assert set(view) == {'narrative', 'artifacts'} and len(view['artifacts']) == 3


def test_unrevealed_live_drafts_carry_artifacts_but_no_identity(client, monkeypatch):
    from app.routers import pilot
    from tests.test_pilot import enroll

    async def generate(question, task_type):
        return [{'text': RESPONSE, 'author': 'model-one', 'origin': 'openrouter'}, {'text': 'Plain answer.', 'author': 'model-two', 'origin': 'openrouter'}]
    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    h = enroll(client)
    run = client.post('/api/pilot/runs', headers=h, json={'question': 'Record the March insurance payment and tell me the entries.', 'task_type': 'journal-entry'}).json()
    assert run['status'] == 'review'
    by_artifacts = sorted(run['drafts'], key=lambda d: len(d['artifacts']))
    assert len(by_artifacts[0]['artifacts']) == 0 and by_artifacts[0]['narrative'] == 'Plain answer.'
    assert len(by_artifacts[1]['artifacts']) == 3
    assert all(set(d) == {'position', 'text', 'narrative', 'artifacts'} for d in run['drafts'])
