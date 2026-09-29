from __future__ import annotations

from copy import deepcopy
import html
import json
from pathlib import Path

from pipeline import boards
from pipeline import benchmarks as catalog


ROOT = Path(__file__).resolve().parents[2]


def load_registry():
    return json.loads((ROOT / "benchmarks" / "registry.json").read_text(encoding="utf-8"))


def load_boards_and_models():
    board_data, board_errors = catalog._load_board_files(boards.BOARDS_DIR)
    models, model_errors = catalog._load_models_file(boards.MODELS)
    assert not board_errors + model_errors
    return board_data, models


def test_model_keys_merge_aliases():
    label, _, _ = boards.vals_label("anthropic/claude-opus-5")
    assert boards.model_key("Claude Opus 5") == boards.model_key("Opus 5") == boards.model_key(label)
    assert boards.model_key("Gemini Pro 3.1") == boards.model_key("Gemini 3.1 Pro (Preview)")


def test_vals_label():
    assert boards.vals_label("grok/grok-4-0709") == ("Grok 4 0709", None, "xAI")
    assert boards.vals_label("anthropic/claude-opus-4-5-20251101-thinking") == (
        "Claude Opus 4.5", "Thinking", "Anthropic"
    )


def test_resolve_weights_handles_conflict_and_open_family():
    assert boards.resolve_weights({
        "name": "GPT-OSS-20B",
        "weights_reported": {"benchmark-a": "open", "benchmark-b": "closed"},
    }) == ("unknown", "conflict")
    assert boards.resolve_weights({"name": "GPT-OSS-20B", "weights_reported": {}}) == ("open", "family")


def test_attach_apex_costs_requires_equal_mean_score():
    board = {
        "entries": [
            {"label": "Opus 5", "scores": {"mean-score": 61.0}, "cost": None},
            {"label": "Claude Opus 5", "scores": {"mean-score": 59.0}, "cost": None},
        ]
    }
    boards.attach_apex_costs(board, [("Opus 5", 59.0, 12.5)])
    assert [entry["cost"] for entry in board["entries"]] == [None, 12.5]
    assert board["cost_label"] == "USD per run (publisher cost study, subset of models)"


def test_adapt_dualentry_reads_two_rows():
    page = """
    <table>
      <tr><th>Model Provider</th><th>License Type</th></tr>
      <tr><td>Claude Opus 5</td><td>84.5%</td><td>Overall</td><td>Anthropic</td><td>Closed</td></tr>
      <tr><td>Grok 4.5</td><td>81%</td><td>Overall</td><td>xAI</td><td>Open</td></tr>
    </table>
    """
    result = boards.adapt_dualentry(page)
    assert [(row["label"], row["scores"]["accuracy"], row["org"], row["weights"]) for row in result["entries"]] == [
        ("Claude Opus 5", 84.5, "Anthropic", "closed"),
        ("Grok 4.5", 81.0, "xAI", "open"),
    ]


def test_adapt_entendre_reads_open_and_non_open_rows():
    page = """
    <table>
      <tr><th>Model</th><th>Mean score</th><th>Sort</th></tr>
      <tr><td>GPT-OSS-20B</td><td>OS</td><td>Open weights</td><td>88.2%</td></tr>
      <tr><td>Claude Opus 5</td><td>—</td><td>81.4%</td></tr>
    </table>
    """
    result = boards.adapt_entendre(page)
    assert [(row["label"], row["scores"]["mean"], row["weights"]) for row in result["entries"]] == [
        ("GPT-OSS-20B", 88.2, "open"),
        ("Claude Opus 5", 81.4, None),
    ]


def test_adapt_vals_reads_html_escaped_astro_payload():
    payload = {
        "benchmarkView": [0, {
            "metadata": [0, {
                "updated": [0, "2026-09-26"],
                "use_cost_per_test": [0, True],
                "archived": [0, False],
                "tags": [1, ["finance"]],
            }],
            "tasks": [0, {
                "overall": [0, {
                    "anthropic/claude-opus-5": [0, {
                        "accuracy": [0, 72.5],
                        "cost_per_test": [0, 1.25],
                    }],
                }],
            }],
        }],
    }
    page = f'<div props="{html.escape(json.dumps(payload), quote=True)}"></div>'
    result = boards.adapt_vals(page)
    assert result["as_of"] == "2026-09-26"
    assert result["entries"] == [{
        "label": "Claude Opus 5",
        "config": None,
        "org": "Anthropic",
        "source_model_id": "anthropic/claude-opus-5",
        "scores": {"accuracy": 72.5},
        "cost": 1.25,
    }]


def test_committed_boards_validate():
    board_data, models = load_boards_and_models()
    assert catalog.validate_boards(load_registry(), board_data, models) == []


def test_board_validator_rejects_unknown_model():
    board_data, models = load_boards_and_models()
    board_data[0]["entries"][0]["model"] = "not-in-models"
    assert any("not present in models.json" in error for error in catalog.validate_boards(load_registry(), board_data, models))


def test_board_validator_rejects_unknown_score_key():
    board_data, models = load_boards_and_models()
    board_data[0]["entries"][0]["scores"]["not-a-metric"] = 1
    assert any("unknown metric keys" in error for error in catalog.validate_boards(load_registry(), board_data, models))


def test_board_validator_rejects_cost_label_for_null_costs():
    board_data, models = load_boards_and_models()
    board = next(item for item in board_data if item["benchmark_id"] == "apex-agents-ib")
    board["cost_label"] = "USD per run"
    assert any("cost_label must be null iff" in error for error in catalog.validate_boards(load_registry(), board_data, models))


def test_board_validator_rejects_wrong_file_stem():
    board_data, models = load_boards_and_models()
    board_data[0]["_file_stem"] = "wrong-name"
    assert any("file stem does not match" in error for error in catalog.validate_boards(load_registry(), board_data, models))


def test_board_validator_rejects_registry_out_of_sync():
    board_data, models = load_boards_and_models()
    registry = deepcopy(load_registry())
    registry_board = next(item for item in registry["benchmarks"] if item["id"] == "apex-accounting")
    registry_board["results"]["leader"] = "Out of date"
    assert any(
        "registry results out of sync with board; run python -m pipeline.boards" in error
        for error in catalog.validate_boards(registry, board_data, models)
    )
