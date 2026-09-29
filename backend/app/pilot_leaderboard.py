from datetime import datetime, timezone

from .services.ratings import compute_ratings


NOTE = "Preference among participating accountants; not a correctness score."


def build_leaderboard(runs, task_type: str | None = None) -> dict:
    pairs = []
    participants = set()
    for run in runs:
        data = run.data
        if task_type and data.get("task_type") != task_type:
            continue
        if data.get("mode") in ("authored-fixture", "sample"):
            continue
        if data.get("evaluation_scope") == "unblinded-conversation":
            continue
        judgment = data.get("judgment") or {}
        if judgment.get("mechanism") != "preference-v2":
            continue
        preference = judgment.get("preference")
        drafts = data.get("drafts") or []
        if preference not in ("a", "b") or len(drafts) != 2:
            continue
        model_a, model_b = drafts[0].get("model_id"), drafts[1].get("model_id")
        if not model_a or not model_b:
            continue
        winner, loser = (model_a, model_b) if preference == "a" else (model_b, model_a)
        pairs.append((winner, loser))
        participants.add(run.participant_id)

    rows = [
        {
            "rank": row.rank,
            "model_id": row.model_id,
            "rating": row.rating,
            "ci_low": row.ci_low,
            "ci_high": row.ci_high,
            "wins": row.wins,
            "losses": row.losses,
            "votes": row.votes,
        }
        for row in compute_ratings(pairs)
    ]
    return {
        "rows": rows,
        "total_votes": len(pairs),
        "participants": len(participants),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": NOTE,
    }
