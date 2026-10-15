from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path

import httpx

from pipeline import benchmarks as pipeline


ROOT = Path(__file__).resolve().parents[2]


def load_registry():
    return json.loads((ROOT / "benchmarks" / "registry.json").read_text(encoding="utf-8"))


def load_board_inputs():
    boards, board_errors = pipeline._load_board_files(pipeline.BOARDS_DIR)
    models, model_errors = pipeline._load_models_file(pipeline.MODELS)
    assert not board_errors + model_errors
    return boards, models


def test_committed_registry_validates():
    registry = load_registry()
    assert pipeline.validate(registry) == []
    boards, models = load_board_inputs()
    assert pipeline.validate_boards(registry, boards, models) == []


def test_metric_definitions_are_optional():
    registry = deepcopy(load_registry())
    for benchmark in registry["benchmarks"]:
        benchmark.pop("metric_definitions", None)
    assert pipeline.validate(registry) == []


def test_validator_rejects_invalid_metric_definitions():
    registry = deepcopy(load_registry())
    registry["benchmarks"][0]["metric_definitions"] = ["not", "an object"]
    assert any("metric_definitions must be a non-empty object" in error for error in pipeline.validate(registry))

    registry = deepcopy(load_registry())
    registry["benchmarks"][0]["metric_definitions"]["mean-score"] = " "
    assert any("metric_definitions.mean-score must be a non-empty string" in error for error in pipeline.validate(registry))


def test_board_validator_rejects_metric_definition_for_unknown_board_metric():
    registry = deepcopy(load_registry())
    benchmark = next(item for item in registry["benchmarks"] if item["id"] == "apex-accounting")
    benchmark["metric_definitions"]["not-a-board-metric"] = "Not a real board metric."
    boards, models = load_board_inputs()
    assert any(
        "metric_definitions keys are not board metrics" in error
        for error in pipeline.validate_boards(registry, boards, models)
    )


def test_board_validator_rejects_board_metric_without_definition():
    registry = deepcopy(load_registry())
    benchmark = next(item for item in registry["benchmarks"] if item["id"] == "apex-accounting")
    del benchmark["metric_definitions"]["pass-1"]
    boards, models = load_board_inputs()
    assert any(
        "board metrics missing definitions" in error
        for error in pipeline.validate_boards(registry, boards, models)
    )


def test_board_validator_rejects_definitions_without_board():
    registry = deepcopy(load_registry())
    boards, models = load_board_inputs()
    board_ids = {board["benchmark_id"] for board in boards}
    benchmark = next(item for item in registry["benchmarks"] if item["id"] not in board_ids)
    benchmark["metric_definitions"] = {"accuracy": "A definition without a board."}
    assert any(
        "metric_definitions require a model board" in error
        for error in pipeline.validate_boards(registry, boards, models)
    )


def test_build_matches_committed_outputs(tmp_path):
    registry = load_registry()
    built = tmp_path / "benchmarks.json"
    doc = tmp_path / "public-finance-accounting-benchmarks.md"
    pipeline.build_outputs(registry, built, doc)
    assert built.read_bytes() == (ROOT / "frontend/public/benchmarks.json").read_bytes()
    assert doc.read_bytes() == (ROOT / "docs/research/public-finance-accounting-benchmarks.md").read_bytes()
    built_registry = json.loads(built.read_text(encoding="utf-8"))
    apex = next(item for item in built_registry["benchmarks"] if item["id"] == "apex-accounting")
    assert apex["metric_definitions"] == registry["benchmarks"][0]["metric_definitions"]


def test_validator_rejects_duplicate_id():
    registry = deepcopy(load_registry())
    registry["benchmarks"][1]["id"] = registry["benchmarks"][0]["id"]
    assert any("id is duplicated" in error for error in pipeline.validate(registry))


def test_validator_rejects_unknown_enum():
    registry = deepcopy(load_registry())
    registry["benchmarks"][0]["grader"] = "machine_magic"
    assert any("grader has unknown value" in error for error in pipeline.validate(registry))


def test_validator_rejects_unpublished_results():
    registry = deepcopy(load_registry())
    entry = next(item for item in registry["benchmarks"] if item["results_status"] == "unpublished")
    entry["results"] = {}
    assert any("results must be null for unpublished" in error for error in pipeline.validate(registry))


def test_validator_rejects_leaderboard_without_results_url():
    registry = deepcopy(load_registry())
    entry = next(
        item for item in registry["benchmarks"]
        if item["results_status"] == "leaderboard" and not item["links"].get("leaderboard")
    )
    entry["results"]["source_url"] = None
    assert any("leaderboard requires" in error for error in pipeline.validate(registry))


def test_validator_rejects_claim_only_without_source():
    registry = deepcopy(load_registry())
    product = next(item for item in registry["products"] if item["status"] == "claim_only")
    product["claim_source"] = None
    assert any("claim_only requires" in error for error in pipeline.validate(registry))


def test_validator_rejects_published_missing_benchmark():
    registry = deepcopy(load_registry())
    product = next(item for item in registry["products"] if item["status"] == "published")
    product["benchmark_ids"] = ["not-a-benchmark"]
    assert any("references missing benchmark" in error for error in pipeline.validate(registry))


def test_validator_rejects_non_https_link():
    registry = deepcopy(load_registry())
    registry["benchmarks"][0]["links"]["home"] = "http://example.com"
    assert any("must start with https://" in error for error in pipeline.validate(registry))


def test_flags_for_stale_review_and_undated_results():
    registry = load_registry()
    catalog_date = date.fromisoformat(registry["catalog_updated"])
    stale = deepcopy(registry["benchmarks"][0])
    stale["results_status"] = "leaderboard"
    stale["results"]["as_of"] = (catalog_date - timedelta(days=200)).isoformat()
    assert "results_stale" in pipeline._flags(stale, catalog_date)

    stale["last_verified"] = (catalog_date - timedelta(days=60)).isoformat()
    assert "review_due" in pipeline._flags(stale, catalog_date)

    stale["results"]["as_of"] = None
    assert "undated_results" in pipeline._flags(stale, catalog_date)


def test_check_sources_classifies_responses_and_hashes_visible_text():
    registry = {
        "benchmarks": [
            {"links": {"home": f"https://example.com/{name}"}, "results": None}
            for name in ("same", "changed", "missing", "redirect")
        ],
        "products": [],
    }
    bodies = {
        "https://example.com/same": "<p>Same <b>text</b></p><script>old secret</script><style>old css</style>",
        "https://example.com/changed": "<p>New text</p>",
        "https://example.com/missing": "<h1>Not found</h1>",
        "https://example.com/redirect": "<p>Moved</p>",
    }
    status_codes = {
        "https://example.com/same": 200,
        "https://example.com/changed": 200,
        "https://example.com/missing": 404,
        "https://example.com/redirect": 200,
    }

    def handler(request):
        if str(request.url) == "https://example.com/redirect":
            return httpx.Response(
                302,
                request=request,
                headers={"Location": "https://example.com/redirected"},
            )
        if str(request.url) == "https://example.com/redirected":
            return httpx.Response(200, text=bodies["https://example.com/redirect"], request=request)
        return httpx.Response(status_codes[str(request.url)], text=bodies[str(request.url)], request=request)

    previous_state = {}
    for key, body in bodies.items():
        if key != "https://example.com/redirect":
            previous_state[key] = {
                "text_sha256": pipeline.sha256(pipeline._visible_text(body).encode("utf-8")).hexdigest()
                if key in ("https://example.com/same", "https://example.com/missing")
                else pipeline.sha256(b"old text").hexdigest()
            }
    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    try:
        report = pipeline.check_sources(registry, client, previous_state, checked="2026-09-29")
    finally:
        client.close()

    assert report["unchanged_count"] == 1
    assert report["changed"] == ["https://example.com/changed"]
    assert [url for url, _ in report["unreachable"]] == ["https://example.com/missing"]
    assert [url for url, _ in report["redirected"]] == ["https://example.com/redirect"]
    assert report["state"]["https://example.com/same"]["text_sha256"] == previous_state["https://example.com/same"]["text_sha256"]


def test_script_and_style_changes_do_not_change_visible_hash():
    before = pipeline._visible_text("<p>Visible words</p><script>one()</script><style>.x{}</style>")
    after = pipeline._visible_text("<p>Visible words</p><script>two()</script><style>.y{}</style>")
    assert pipeline.sha256(before.encode("utf-8")).hexdigest() == pipeline.sha256(after.encode("utf-8")).hexdigest()
