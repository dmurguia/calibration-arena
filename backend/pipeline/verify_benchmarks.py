"""Check the public feed for expected publication, failed sources and missed runs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import httpx


def health_errors(catalog: dict, now: datetime, expected: str | None = None) -> list[str]:
    errors = []
    refresh = catalog.get("refresh", {})
    if expected and refresh.get("snapshot_id") != expected:
        errors.append("Expected snapshot is not public yet")
    def overdue(value):
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            hours = (now - moment).total_seconds() / 3600
            return hours > 36 or hours < -1
        except (ValueError, TypeError, AttributeError):
            return True
    if overdue(refresh.get("checked_at")):
        errors.append("Daily refresh is overdue or missing")
    board_list = catalog.get("boards", [])
    if not board_list:
        errors.append("No published boards")
    for board in board_list:
        bid = board["benchmark_id"]
        if overdue(board.get("last_successful_check", board.get("retrieved"))):
            errors.append(f"{bid}: last successful check is overdue")
        if refresh.get("sources", {}).get(bid, {}).get("status") != "ok":
            errors.append(f"{bid}: latest check failed or is missing")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://calibrationarena.ai/benchmark-feed/benchmarks.json")
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--wait-seconds", type=int, default=0)
    parser.add_argument("--publication-only", action="store_true", help="Verify snapshot delivery; health check is a separate step")
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text())["refresh"]["snapshot_id"] if args.expected else None
    deadline = time.monotonic() + args.wait_seconds
    while True:
        try:
            response = httpx.get(args.url, headers={"Cache-Control": "no-cache"}, timeout=20, follow_redirects=True)
            response.raise_for_status()
            value = response.json()
            if args.publication_only:
                errors = [] if expected and value.get("refresh", {}).get("snapshot_id") == expected else ["Expected snapshot is not public yet"]
            else:
                errors = health_errors(value, datetime.now(timezone.utc), expected)
        except (httpx.HTTPError, ValueError, AttributeError, TypeError, KeyError) as exc:
            errors = [f"Public feed unavailable: {exc}"]
        if not errors or time.monotonic() >= deadline:
            break
        time.sleep(15)
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print("Public benchmark feed verified")


if __name__ == "__main__":
    main()
