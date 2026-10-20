from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import httpx
import pytest

from pipeline import boards, benchmarks
from pipeline import refresh_benchmarks as refresh
from pipeline.verify_benchmarks import health_errors
from pipeline import publish_benchmarks

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 20, 13, 17, tzinfo=timezone.utc)


def board(bid="apex-accounting"):
    return json.loads((ROOT / "benchmarks/boards" / f"{bid}.json").read_text())


def parsed(bid, page, retrieved):
    value = board(bid)
    value["retrieved"] = retrieved
    raw = [{"label": r["label"], "org": None} for r in value["entries"]]
    return value, raw


def test_failed_source_preserves_snapshot_and_healthy_source_updates(tmp_path, monkeypatch):
    monkeypatch.setattr(boards, "build_board", parsed)
    ids = ["apex-accounting", "dualentry-accounting-ai-benchmark"]
    attempts = []
    def respond(request):
        attempts.append(str(request.url))
        return httpx.Response(503 if "dualentry" in str(request.url) else 200, text='<h2>Methodology</h2><p>Rubric</p>')
    before = (ROOT / "benchmarks/registry.json").read_bytes()
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        report = refresh.refresh(ROOT, tmp_path / "output", tmp_path / "evidence", client, ids=ids, now=NOW, sleep=lambda _: None)
    assert len(attempts) == 4
    assert report["sources"][ids[0]]["status"] == "ok"
    assert report["sources"][ids[1]]["status"] == "failed"
    feed = refresh.read(tmp_path / "output/benchmarks.json")
    fresh = next(b for b in feed["boards"] if b["benchmark_id"] == ids[0])
    stale = next(b for b in feed["boards"] if b["benchmark_id"] == ids[1])
    assert fresh["last_successful_check"] == NOW.isoformat()
    assert stale == board(ids[1])
    assert (ROOT / "benchmarks/registry.json").read_bytes() == before
    assert (tmp_path / "evidence" / ids[1] / "attempt-3.html").exists()
    assert "error" not in feed["refresh"]["sources"][ids[1]]


def test_total_failure_keeps_previous_good_data(tmp_path, monkeypatch):
    monkeypatch.setattr(boards, "build_board", parsed)
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, text="hello"))) as client:
        refresh.refresh(ROOT, tmp_path / "first", tmp_path / "evidence1", client, ids=["apex-accounting"], now=NOW)
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403))) as client:
        refresh.refresh(ROOT, tmp_path / "second", tmp_path / "evidence2", client, previous=tmp_path / "first", ids=["apex-accounting"], now=NOW)
    first = refresh.read(tmp_path / "first/benchmarks.json")
    second = refresh.read(tmp_path / "second/benchmarks.json")
    assert first["boards"] == second["boards"]
    assert second["refresh"]["sources"]["apex-accounting"]["status"] == "failed"


def test_aggregate_failure_never_exposes_output(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmarks, "build_outputs", lambda *a, **k: (_ for _ in ()).throw(ValueError("build failed")))
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403))) as client:
        with pytest.raises(ValueError, match="build failed"):
            refresh.refresh(ROOT, tmp_path / "output", tmp_path / "evidence", client, ids=["apex-accounting"], now=NOW)
    assert not (tmp_path / "output").exists()
    assert not list(tmp_path.glob('.benchmark-stage-*'))


@pytest.mark.parametrize('problem', ['range', 'nan', 'duplicate', 'metric', 'row_loss', 'methodology'])
def test_rejects_suspicious_candidates(problem):
    old = board()
    candidate = deepcopy(old)
    candidate["methodology_sha256"] = "same"
    if problem == 'range': candidate["entries"][0]["scores"]["mean-score"] = 101
    if problem == 'nan': candidate["entries"][0]["scores"]["mean-score"] = float('nan')
    if problem == 'duplicate': candidate["entries"].append(candidate["entries"][0])
    if problem == 'metric': candidate["entries"][0]["scores"].pop("pass-1")
    if problem == 'row_loss': candidate["entries"] = candidate["entries"][:2]
    if problem == 'methodology': old["methodology_sha256"] = "old"
    with pytest.raises(ValueError): refresh.check_candidate(candidate, old)


def test_methodology_detector_ignores_scores_but_detects_protocol_changes():
    a = '<h2>Leaderboard</h2>50%<h2>Methodology</h2><p>Two judges.</p><h2>Contact</h2>'
    assert refresh.methodology_hash(a) == refresh.methodology_hash(a.replace('50%', '60%'))
    assert refresh.methodology_hash(a) != refresh.methodology_hash(a.replace('Two judges', 'One judge'))
    assert refresh.methodology_hash('<p>No protocol section</p>') is None


def test_dates_and_lifecycle_are_independent():
    registry = refresh.read(ROOT / "benchmarks/registry.json")
    value = board('vals-taxeval-v2')
    value.update(as_of=None, archived=True, retrieved='2026-10-20')
    boards.sync_registry(registry, value)
    entry = next(b for b in registry["benchmarks"] if b["id"] == value["benchmark_id"])
    assert entry["results"]["as_of"] is None
    assert entry["results_status"] == 'archived'
    value["archived"] = False
    boards.sync_registry(registry, value)
    assert entry["results_status"] == 'leaderboard'


def test_vals_explicit_retirement_notice_overrides_embedded_false(monkeypatch):
    monkeypatch.setattr(boards, '_astro', lambda _: {'benchmarkView': {
        'metadata': {'archived': False}, 'tasks': {'overall': {}}
    }})
    page = '<p>Archived Benchmark</p><astro-island props="{&quot;benchmarkView&quot;: {}, &quot;tasks&quot;: {}}"></astro-island>'
    assert boards.adapt_vals(page)['archived'] is True
    assert boards.adapt_vals(page.replace('Archived Benchmark', 'Current Benchmark'))['archived'] is False


def test_apex_new_results_payload_preserves_costs(monkeypatch):
    monkeypatch.setattr(boards, '_next_data', lambda _: {'props': {'pageProps': {'results': [{
        'model': {'modelName': 'Example', 'provider': {'name': 'Example'}, 'effort': 'high'},
        'passScores': [{'pass': 'mean-score', 'score': 60, 'error': 2}, {'pass': 'pass-1', 'score': 20}],
        'costPerRun': 2.04
    }]}}})
    result = boards.adapt_apex_accounting('')
    assert result['entries'][0]['cost'] == 2.04
    assert result['entries'][0]['ci']['mean-score'] == [58, 62]
    boards.attach_apex_costs(result, [])
    assert result['cost_label'] == 'USD per run (publisher-reported)'


def test_review_approval_is_exact_and_never_skips_invalid_scores():
    previous = board()
    candidate = deepcopy(previous)
    candidate['entries'] = candidate['entries'][:2]
    candidate['methodology_sha256'] = None
    digest = refresh.candidate_digest(candidate)
    refresh.check_candidate(candidate, previous, digest)
    candidate['entries'][0]['scores']['mean-score'] = 99
    with pytest.raises(ValueError): refresh.check_candidate(candidate, previous, digest)
    candidate['entries'][0]['scores']['mean-score'] = 101
    with pytest.raises(ValueError): refresh.check_candidate(candidate, previous, refresh.candidate_digest(candidate))


def test_watchdog_detects_stopped_scheduler_and_failed_sources():
    feed = {"refresh": {"checked_at": NOW.isoformat(), "snapshot_id": "good", "sources": {"a": {"status": "ok"}}},
            "boards": [{"benchmark_id": "a", "last_successful_check": NOW.isoformat()}]}
    assert health_errors(feed, NOW, 'good') == []
    assert health_errors(feed, NOW, 'wrong')
    assert health_errors(feed, datetime(2026, 10, 23, tzinfo=timezone.utc))
    feed["refresh"]["sources"]["a"]["status"] = 'failed'
    assert health_errors(feed, NOW)


def test_publication_updates_only_data_ref_after_complete_tree(tmp_path, monkeypatch):
    refresh.dump(tmp_path / 'benchmarks.json', {'refresh': {'snapshot_id': 'example'}})
    requests = []
    def respond(request):
        requests.append((request.method, request.url.path, json.loads(request.content) if request.content else None))
        if request.method == 'GET': return httpx.Response(200, json={'object': {'sha': 'parent'}})
        if request.url.path.endswith('/trees'): return httpx.Response(201, json={'sha': 'tree'})
        if request.url.path.endswith('/commits'): return httpx.Response(201, json={'sha': 'commit'})
        return httpx.Response(200, json={})
    client = httpx.Client(base_url='https://api.github.com/repos/example/repo/', transport=httpx.MockTransport(respond))
    monkeypatch.setattr(publish_benchmarks.httpx, 'Client', lambda **_: client)
    assert publish_benchmarks.publish(tmp_path, 'example/repo', 'test-token') == 'commit'
    assert requests[-1] == ('PATCH', '/repos/example/repo/git/refs/heads/benchmark-data', {'sha': 'commit', 'force': False})
    assert requests[-2][2]['parents'] == ['parent']
    paths = {entry['path'] for entry in requests[1][2]['tree']}
    assert paths == {'benchmarks.json', 'vercel.json', 'frontend/vercel.json', 'marketing/vercel.json'}
    assert all('/heads/main' not in path for _, path, _ in requests)
