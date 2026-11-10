from datetime import datetime, timezone

from pipeline import alert_benchmarks as alerts

NOW = datetime(2026, 11, 11, 13, 17, tzinfo=timezone.utc)
FEED = {"refresh": {"checked_at": NOW.isoformat(), "sources": {"a": {"status": "ok"}, "b": {"status": "failed"}}},
        "boards": [{"benchmark_id": "a", "last_successful_check": NOW.isoformat()},
                   {"benchmark_id": "b", "last_successful_check": "2026-10-27T00:00:00+00:00"}]}


def test_report_failures_are_listed_once_per_board_with_fix():
    report = {"sources": {"a": {"status": "ok"}, "b": {"status": "failed", "error": "Methodology section changed", "last_successful_check": "2026-10-27"}}}
    found = alerts.problems(report, FEED, NOW, "failure")
    assert [p["board"] for p in found] == ["b"]
    text = alerts.body(found, "https://example.test/run")
    assert "Methodology section changed" in text and "benchmarks/sources.json" in text and "https://example.test/run" in text


def test_workflow_failure_without_source_problems_still_alerts():
    clean = {"refresh": {"checked_at": NOW.isoformat(), "sources": {"a": {"status": "ok"}}},
             "boards": [{"benchmark_id": "a", "last_successful_check": NOW.isoformat()}]}
    assert alerts.problems({"sources": {"a": {"status": "ok"}}}, clean, NOW, "success") == []
    assert alerts.problems({"sources": {"a": {"status": "ok"}}}, clean, NOW, "failure")[0]["kind"] == "workflow"


def test_issue_plan_creates_updates_only_on_change_and_closes():
    found = alerts.problems(None, FEED, NOW, None)
    assert alerts.plan(None, found) == "create"
    open_issue = {"number": 1, "body": alerts.body(found, None)}
    assert alerts.plan(open_issue, found) == "none"
    assert alerts.plan(open_issue, found + [{"board": "c", "kind": "failed", "detail": "x"}]) == "update"
    assert alerts.plan(open_issue, []) == "close"
    assert alerts.plan(open_issue, [], close=False) == "none"
    assert alerts.plan(None, []) == "none"
