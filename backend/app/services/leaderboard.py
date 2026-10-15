"""Leaderboard pipeline: votes → Bradley-Terry fit → persisted snapshot.

The leaderboard API never ranks on the fly; it reads the latest snapshot, the
same shape a nightly batch job would produce. Snapshots are recomputed (a) by
the CLI pipeline (pipeline/compute_ratings.py), (b) in the background whenever
a battle completes, and (c) by the seed script.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..categories import CATEGORIES, OVERALL
from ..config import get_settings
from ..models import ArenaModel, ModelRating, RatingSnapshot, Vote
from .ratings import compute_ratings


def compute_snapshot(db: Session, category: str, bootstrap_rounds: int | None = None) -> RatingSnapshot | None:
    # Published boards use verified votes only: credential weight >= 1.0
    # (work-domain tier and up, plus the flagged synthetic bootstrap) and
    # votes that cleared the behavioral floor.
    q = select(Vote.winner_model_id, Vote.loser_model_id, Vote.weight).where(
        Vote.counted.is_(True), Vote.weight >= 1.0
    )
    if category != OVERALL:
        q = q.where(Vote.category == category)
    # Inactive foundation models (retired from the roster) drop off the board;
    # their vote rows stay in the table as history.
    hidden = set(db.scalars(select(ArenaModel.id).where(
        ArenaModel.active.is_(False), ArenaModel.kind == "foundation")))
    pairs = [(w, l, wt) for w, l, wt in db.execute(q) if w not in hidden and l not in hidden]
    if not pairs:
        return None

    rounds = get_settings().ci_bootstrap_rounds if bootstrap_rounds is None else bootstrap_rounds
    rows = compute_ratings(pairs, bootstrap_rounds=rounds)

    snapshot = RatingSnapshot(category=category, algo="bradley-terry", vote_count=len(pairs))
    db.add(snapshot)
    db.flush()
    for r in rows:
        db.add(
            ModelRating(
                snapshot_id=snapshot.id,
                model_id=r.model_id,
                rank=r.rank,
                rating=r.rating,
                ci_low=r.ci_low,
                ci_high=r.ci_high,
                wins=r.wins,
                losses=r.losses,
                votes=r.votes,
            )
        )
    db.commit()
    return snapshot


def compute_all_snapshots(db: Session, bootstrap_rounds: int | None = None) -> list[str]:
    computed = []
    for cat in [*CATEGORIES.keys(), OVERALL]:
        if compute_snapshot(db, cat, bootstrap_rounds=bootstrap_rounds) is not None:
            computed.append(cat)
    return computed


def latest_snapshot(db: Session, category: str) -> RatingSnapshot | None:
    return db.scalars(
        select(RatingSnapshot)
        .where(RatingSnapshot.category == category)
        .order_by(RatingSnapshot.computed_at.desc(), RatingSnapshot.id.desc())
        .options(selectinload(RatingSnapshot.entries).selectinload(ModelRating.model))
        .limit(1)
    ).first()


def previous_ranks(db: Session, category: str) -> dict[int, int]:
    """model_id → rank in the snapshot before the latest (for movement arrows)."""
    prev = db.scalars(
        select(RatingSnapshot)
        .where(RatingSnapshot.category == category)
        .order_by(RatingSnapshot.computed_at.desc(), RatingSnapshot.id.desc())
        .options(selectinload(RatingSnapshot.entries))
        .offset(1)
        .limit(1)
    ).first()
    if prev is None:
        return {}
    return {e.model_id: e.rank for e in prev.entries}
