"""Build an immutable, validated publication; never mutate the input snapshots."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

import httpx

from pipeline import boards, benchmarks


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def read(path: Path):
    return json.loads(path.read_text())


class Methodology(HTMLParser):
    """Watch explicitly headed methodology sections, excluding scripts/navigation.

    This is a change detector, not proof the entire evaluation protocol is unchanged.
    Raw evidence is retained so changes elsewhere can be reviewed separately.
    """
    def __init__(self):
        super().__init__()
        self.heading = None
        self.heading_text = []
        self.active_level = None
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav"):
            self.hidden += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.heading = int(tag[1])
            self.heading_text = []
            if self.active_level is not None and self.heading <= self.active_level:
                self.active_level = None

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav"):
            self.hidden = max(0, self.hidden - 1)
        if re.fullmatch(r"h[1-6]", tag) and self.heading is not None:
            title = " ".join(self.heading_text).strip().lower()
            if not self.hidden and re.search(r"methodology|evaluation (setup|protocol)|scoring (method|criteria)|how we (evaluate|score)", title):
                self.active_level = self.heading
                self.parts.append(title)
            self.heading = None

    def handle_data(self, value):
        if self.hidden:
            return
        if self.heading is not None:
            self.heading_text.append(value)
        elif self.active_level is not None:
            self.parts.append(value)


def methodology_hash(page: str) -> str | None:
    parser = Methodology()
    parser.feed(page)
    value = " ".join(" ".join(parser.parts).split())
    return sha256(value.encode()).hexdigest() if value else None


def candidate_digest(board: dict) -> str:
    # Exact reviewed result content; independent of retrieval time and HTML chrome.
    return sha256(json.dumps({k: board.get(k) for k in ("benchmark_id", "metrics", "entries", "as_of", "archived", "methodology_sha256")}, sort_keys=True, allow_nan=False).encode()).hexdigest()


def check_candidate(board: dict, previous: dict | None, reviewed_digest: str | None = None) -> None:
    if not board["entries"]:
        raise ValueError("No model results extracted")
    keys = {m["key"] for m in board["metrics"]}
    identities = set()
    for row in board["entries"]:
        identity = (row.get("source_model_id", row["model"]), row["config"])
        if identity in identities:
            raise ValueError(f"Duplicate model/configuration: {identity}")
        identities.add(identity)
        if set(row["scores"]) != keys:
            raise ValueError("Missing or unexpected score metrics")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 100 for v in row["scores"].values()):
            raise ValueError("Scores must be finite percentages between 0 and 100")
        for key, interval in row.get("ci", {}).items():
            if len(interval) != 2 or any(not math.isfinite(v) for v in interval) or not interval[0] <= row["scores"][key] <= interval[1]:
                raise ValueError("Invalid confidence interval")
        if row["cost"] is not None and (not math.isfinite(row["cost"]) or row["cost"] < 0):
            raise ValueError("Invalid cost")
    if previous:
        if board["metrics"] != previous["metrics"]:
            raise ValueError("Metric definition changed; review required")
        reviewed = reviewed_digest is not None and candidate_digest(board) == reviewed_digest
        if not reviewed and len(board["entries"]) < len(previous["entries"]) * 0.8:
            raise ValueError("More than 20% of result rows disappeared; review required")
        if not reviewed and "methodology_sha256" in previous and board["methodology_sha256"] != previous["methodology_sha256"]:
            raise ValueError("Methodology section changed or disappeared; review required")
        if board["as_of"] and previous.get("as_of") and board["as_of"] < previous["as_of"]:
            raise ValueError("Publisher date moved backwards; review required")


def download(client: httpx.Client, url: str, evidence: Path, *, sleep=time.sleep) -> httpx.Response:
    for attempt in range(1, 4):
        try:
            response = client.get(url)
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / f"attempt-{attempt}.html").write_bytes(response.content)
            dump(evidence / f"attempt-{attempt}.json", {
                "url": url, "final_url": str(response.url), "status": response.status_code,
                "sha256": sha256(response.content).hexdigest(),
            })
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            dump(evidence / f"attempt-{attempt}-error.json", {"error": str(exc)})
            if attempt == 3 or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500 and exc.response.status_code not in (408, 429)):
                raise
            sleep(2 ** (attempt - 1))
    raise AssertionError("unreachable")


def refresh(root: Path, output: Path, evidence: Path, client: httpx.Client, *, previous: Path | None = None,
            now: datetime | None = None, ids: list[str] | None = None, sleep=time.sleep) -> dict:
    """Publish output by directory rename only after all aggregate checks pass.

    The scheduler publishes this directory in ONE git commit. Failed sources retain
    their previous boards/models, and a whole-run failure leaves output absent.
    """
    if output.exists():
        raise ValueError("Output must be a new directory (immutable run)")
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat()
    today = now.date().isoformat()
    registry = read(root / "benchmarks/registry.json")
    approvals_path = root / "benchmarks/refresh-approvals.json"
    approvals = read(approvals_path) if approvals_path.exists() else {}
    current = {p.stem: read(p) for p in (root / "benchmarks/boards").glob("*.json")}
    model_records = read(root / "benchmarks/models.json")["models"]
    # Editorial metadata always comes from reviewed application code. Only prior
    # board snapshots and model observations are taken from the publication branch.
    if previous is not None:
        prior = read(previous / "benchmarks.json")
        prior_models = {m["id"]: m for m in prior["models"]}
        prior_models.update({m["id"]: m for m in model_records if m["id"] not in prior_models})
        model_records = list(prior_models.values())
        for board in prior["boards"]:
            if board["benchmark_id"] in current:
                current[board["benchmark_id"]] = board
    models = {m["id"]: {k: m[k] for k in ("id", "name", "org", "weights_reported")} for m in model_records}
    for board in current.values():
        boards.sync_registry(registry, board)
    report = {"checked_at": stamp, "cadence": "daily", "sources": {}}
    for bid in ids if ids is not None else boards.SOURCES:
        source = boards.SOURCES[bid]
        old = current.get(bid)
        try:
            response = download(client, source["url"], evidence / bid, sleep=sleep)
            candidate, raw = boards.build_board(bid, response.text, today)
            candidate["last_successful_check"] = stamp
            candidate["methodology_sha256"] = methodology_hash(response.text)
            candidate["source_sha256"] = sha256(response.content).hexdigest()
            candidate["source_url"] = str(response.url)
            dump(evidence / bid / "candidate.json", candidate)
            check_candidate(candidate, old, approvals.get(bid, {}).get("candidate_sha256"))
            trial_registry, trial_models, trial_boards = deepcopy(registry), deepcopy(models), deepcopy(current)
            # Clear obsolete publisher reports before incorporating the latest ones.
            for model in trial_models.values():
                model["weights_reported"].pop(bid, None)
            boards.merge_models(trial_models, bid, raw)
            trial_boards[bid] = candidate
            boards.sync_registry(trial_registry, candidate)
            resolved = []
            for m in trial_models.values():
                weights, basis = boards.resolve_weights(m)
                resolved.append({**m, "weights": weights, "weights_basis": basis})
            errors = benchmarks.validate(trial_registry) + benchmarks.validate_boards(trial_registry, list(trial_boards.values()), {"models": resolved})
            if errors:
                raise ValueError("; ".join(errors))
            current, models, registry = trial_boards, trial_models, trial_registry
            report["sources"][bid] = {"status": "ok", "rows": len(candidate["entries"]), "last_successful_check": stamp}
        except (httpx.HTTPError, ValueError, KeyError, IndexError, StopIteration, TypeError) as exc:
            report["sources"][bid] = {"status": "failed", "error": str(exc),
                "last_successful_check": old.get("last_successful_check", old.get("retrieved")) if old else None}
    # Errors/evidence remain available even if the aggregate validation fails.
    dump(evidence / "report.json", report)
    registry["catalog_updated"] = today
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".benchmark-stage-", dir=output.parent))
    try:
        for bid, board in current.items():
            dump(stage / "benchmarks/boards" / f"{bid}.json", board)
        dump(stage / "benchmarks/registry.json", registry)
        boards.write_models(models, stage / "benchmarks/models.json")
        errors = benchmarks.validate(registry) + benchmarks.validate_boards(registry, list(current.values()), read(stage / "benchmarks/models.json"))
        if errors:
            raise ValueError("; ".join(errors))
        benchmarks.build_outputs(registry, stage / "benchmarks.json", stage / "catalog.md",
            boards_dir=stage / "benchmarks/boards", models_path=stage / "benchmarks/models.json")
        catalog = read(stage / "benchmarks.json")
        # No source exception text is exposed in the public UI/feed.
        catalog["refresh"] = {**report, "sources": {bid: {k: v for k, v in state.items() if k != "error"} for bid, state in report["sources"].items()}}
        catalog["refresh"]["snapshot_id"] = sha256(json.dumps(catalog, sort_keys=True).encode()).hexdigest()
        dump(stage / "benchmarks.json", catalog)
        os.replace(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("ids", nargs="*")
    args = parser.parse_args()
    if set(args.ids) - boards.SOURCES.keys():
        parser.error("Unknown board ID")
    with httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": "CalibrationArenaCatalogBot/1.0 (+https://calibrationarena.ai/benchmarks/method)"}) as client:
        report = refresh(boards.ROOT, args.output.resolve(), args.evidence.resolve(), client,
                         previous=args.previous, ids=args.ids or None)
    for bid, result in report["sources"].items():
        print(f"{bid}: {result['status']} {result.get('error', '')}")
    # Partial/total source failures still produce a coherent fallback publication.
    # CI marks the run failed AFTER publishing and verifying healthy-source updates.


if __name__ == "__main__":
    main()
