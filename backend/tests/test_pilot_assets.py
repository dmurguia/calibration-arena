"""Document routing and evidence preservation, with synthetic files and mocked models."""
import base64
import io

import pytest
from openpyxl import Workbook
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.pilot_assets import AssetUpload, MAX_BYTES, extract_asset, prepare_assets


def asset(name='statement.csv', role='bank-statement', raw=b'date,amount\n2026-09-01,125.00\n'):
    return AssetUpload(name=name, role=role, content_base64=base64.b64encode(raw).decode())


def pdf_bytes(text=None):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                                 NameObject('/Subtype'): NameObject('/Type1'),
                                 NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 20 200 Td ({text}) Tj ET'.encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_extracts_csv_txt_xlsx_and_text_pdf():
    assert '125.00' in extract_asset(asset())['text']
    assert extract_asset(asset('terms.txt', raw=b'QA billing terms: net 30'))['text'] == 'QA billing terms: net 30'
    book = Workbook()
    book.active.append(['Customer', 'Balance'])
    book.active.append(['QA Company', 125])
    book.active.append(['Formula', '=SUM(B2)'])
    output = io.BytesIO()
    book.save(output)
    text = extract_asset(asset('aging.xlsx', raw=output.getvalue()))['text']
    assert 'QA Company\t125' in text and '=SUM(B2)' in text
    assert 'QA invoice total 125' in extract_asset(asset('invoice.pdf', raw=pdf_bytes('QA invoice total 125')))['text']


@pytest.mark.parametrize('name,raw,match', [
    ('statement.exe', b'bad', 'choose a CSV'),
    ('statement.csv', b'date,amount\n', 'at least one data row'),
    ('statement.csv', b'', 'at least 1 character'),
    ('statement.csv', b'x' * (MAX_BYTES + 1), '2 MB'),
    ('statement.txt', b'\xff\xfe', 'UTF-8'),
    ('statement.txt', b'\x00binary', 'UTF-8'),
    ('statement.txt', b'x' * 15001, 'smaller document'),
    ('statement.xlsx', b'not a workbook', 'readable text'),
    ('statement.pdf', pdf_bytes(), 'no readable text'),
], ids=['unsupported', 'header-only', 'empty', 'too-large', 'encoding', 'binary', 'text-limit', 'invalid-workbook', 'scanned-pdf'])
def test_rejects_unsupported_empty_unreadable_and_large_files(name, raw, match):
    # The request schema bounds encoded bytes before extraction as well.
    with pytest.raises(ValueError, match=match):
        extract_asset(asset(name, raw=raw))


def test_required_roles_and_total_text_are_enforced():
    with pytest.raises(ValueError, match='each required'):
        prepare_assets('bank-reconciliation', [asset()])
    with pytest.raises(ValueError, match='each required'):
        prepare_assets('bank-reconciliation', [asset(), asset()])
    with pytest.raises(ValueError, match='Choose a finance task'):
        prepare_assets(None, [asset()])
    with pytest.raises(ValueError, match='Unknown finance task'):
        prepare_assets('invented', [])
    with pytest.raises(ValueError, match='combined files'):
        prepare_assets('bank-reconciliation', [asset('a.txt', raw=b'x' * 14000), asset('b.txt', 'cash-ledger', b'y' * 14000)])


def test_backend_gates_files_before_generation_and_preserves_evidence(client, monkeypatch):
    from app.routers import pilot
    from app.db import SessionLocal
    calls = []

    async def generate(question, task_type, *, history=None):
        calls.append((question, history))
        return [{'text': 'Synthetic QA response A'}, {'text': 'Synthetic QA response B'}]

    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    token = client.post('/api/pilot/guests', json={'source': 'qa-assets'}).json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    question = 'QA edited prompt: reconcile September transactions and show differences.'
    uploads = [asset(), asset('ledger.csv', 'cash-ledger', b'reference,amount\nQA-ledger,125.00\n')]
    body = {'question': question, 'workflow_id': 'bank-reconciliation', 'assets': [a.model_dump() for a in uploads]}
    assert client.post('/api/pilot/runs', json=body).status_code == 401
    for invalid in [[], [uploads[0].model_dump()], [a.model_dump() for a in [uploads[0], uploads[0]]]]:
        assert client.post('/api/pilot/runs', headers=headers, json={**body, 'assets': invalid}).status_code == 422
    assert calls == []
    response = client.post('/api/pilot/runs', headers=headers, json=body)
    assert response.status_code == 200
    run = response.json()
    assert run['brief'] == question and run['workflow_id'] == 'bank-reconciliation'
    assert len(run['attachments']) == 2 and all('text' not in d for d in run['attachments'])
    prompt = calls[0][0]
    assert prompt.startswith(question) and 'QA-ledger' in prompt and '125.00' in prompt
    with SessionLocal() as db:
        saved = db.get(pilot.Run, run['id']).data
        assert saved['model_prompt'] == prompt
        assert saved['input_documents'][1]['text'].startswith('reference,amount')
    client.post(f'/api/pilot/runs/{run["id"]}/preference', headers=headers, json={'preference': 'a'})
    response = client.post('/api/pilot/runs', headers=headers, json={'question': 'Explain the unmatched amounts.', 'source_run_id': run['id'], 'source_position': 'a', 'continuation_mode': 'followup'})
    assert response.status_code == 200
    assert calls[1][1][0]['content'] == prompt


def test_failed_comparison_retry_retains_documents(client, monkeypatch):
    from app.routers import pilot
    calls = []

    async def generate(question, task_type):
        calls.append(question)
        if len(calls) == 1:
            raise ValueError('Synthetic QA failure')
        return [{'text': 'Synthetic QA response A'}, {'text': 'Synthetic QA response B'}]

    monkeypatch.setattr(pilot, 'live_ready', lambda: True)
    monkeypatch.setattr(pilot, 'generate', generate)
    token = client.post('/api/pilot/guests', json={'source': 'qa-assets-retry'}).json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    run = client.post('/api/pilot/runs', headers=headers, json={'question': 'Review the synthetic aging export.', 'workflow_id': 'ar-reporting', 'assets': [asset('aging.csv', 'ar-ledger').model_dump()]}).json()
    assert run['status'] == 'failed'
    retried = client.post('/api/pilot/runs', headers=headers, json={'question': 'Review the synthetic aging export with a shorter summary.', 'retry_of_run_id': run['id']}).json()
    assert retried['status'] == 'review' and retried['attachments'] == run['attachments']
    assert calls[1].startswith('Review the synthetic aging export with a shorter summary.')
    assert '125.00' in calls[1]
