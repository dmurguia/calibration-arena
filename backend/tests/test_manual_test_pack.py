"""The manual test pack in docs/pilot/manual-test stays uploadable and matches its answer key."""
import base64
import importlib.util
from pathlib import Path

import pytest

from app.pilot_assets import AssetUpload, prepare_assets

PACK = Path(__file__).resolve().parents[2] / 'docs' / 'pilot' / 'manual-test'
TASKS = {
    'bank-reconciliation': [('bank-statement.pdf', 'bank-statement'), ('cash-ledger.csv', 'cash-ledger')],
    'ar-reporting': [('ar-ledger.xlsx', 'ar-ledger')],
    'invoicing': [('billing-terms.txt', 'billing-terms'), ('billable-items.csv', 'billable-items')],
}


def upload(name, role, directory=PACK):
    return AssetUpload(name=name, role=role, content_base64=base64.b64encode((directory / name).read_bytes()).decode())


@pytest.mark.parametrize('workflow', TASKS)
def test_committed_files_pass_the_upload_extractor(workflow):
    documents = prepare_assets(workflow, [upload(*f) for f in TASKS[workflow]])
    assert all(d['text'] for d in documents)
    assert prepare_assets('bank-reconciliation', [upload('bank-statement.csv', 'bank-statement'), upload('cash-ledger.csv', 'cash-ledger')])


def test_generator_still_matches_the_readme_answer_key(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('manual_test_generate', PACK / 'generate.py')
    generate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate)
    monkeypatch.setattr(generate, 'OUT', tmp_path)
    key = {'bank': generate.bank_reconciliation(), 'ar': generate.ar_reporting(), 'invoicing': generate.invoicing()}
    readme = (PACK / 'README.md').read_text()
    for figure in (key['bank']['adjusted_balance'], key['bank']['bank_close'], key['bank']['book_close'],
                   key['ar']['total_open'], key['ar']['gl_balance'], *key['ar']['bucket_totals'].values(),
                   key['invoicing']['total'], key['invoicing']['time_and_materials']):
        assert f'{figure:,.2f}' in readme, f'{figure:,.2f} is missing from README.md; update the answer key'
    for workflow, files in TASKS.items():
        assert prepare_assets(workflow, [upload(name, role, tmp_path) for name, role in files])
