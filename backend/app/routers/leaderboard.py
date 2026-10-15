from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..categories import CATEGORIES, OVERALL, is_valid_category
from ..db import get_db
from ..models import ArenaModel
from ..schemas import ArenaModelOut, DeclinedVendorOut, LeaderboardEntryOut, LeaderboardOut
from ..services.leaderboard import compute_all_snapshots, latest_snapshot, previous_ranks

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


def _declined_vendors(db: Session, category: str) -> list[DeclinedVendorOut]:
    """Invited vendors missing from this board — rendered as empty chairs."""
    q = select(ArenaModel).where(ArenaModel.kind == "declined")
    if category != OVERALL:
        q = q.where(ArenaModel.vertical == CATEGORIES[category]["vertical"])
    return [
        DeclinedVendorOut(name=m.name, organization=m.organization, vertical=m.vertical, note=m.description)
        for m in db.scalars(q.order_by(ArenaModel.name))
    ]


@router.get("/{category}", response_model=LeaderboardOut)
def leaderboard(category: str, db: Session = Depends(get_db)) -> LeaderboardOut:
    if category != OVERALL and not is_valid_category(category):
        raise HTTPException(status_code=404, detail=f"Unknown category '{category}'.")
    declined = _declined_vendors(db, category)
    snap = latest_snapshot(db, category)
    if snap is None:
        return LeaderboardOut(category=category, algo="bradley-terry", computed_at=None, vote_count=0,
                              entries=[], declined=declined)
    prev = previous_ranks(db, category)
    return LeaderboardOut(
        category=category,
        algo=snap.algo,
        computed_at=snap.computed_at,
        vote_count=snap.vote_count,
        entries=[
            LeaderboardEntryOut(
                rank=e.rank,
                model=ArenaModelOut.model_validate(e.model),
                rating=e.rating,
                ci_low=e.ci_low,
                ci_high=e.ci_high,
                wins=e.wins,
                losses=e.losses,
                votes=e.votes,
                win_rate=round(e.wins / e.votes, 3) if e.votes else 0.0,
                rank_delta=(prev[e.model_id] - e.rank) if e.model_id in prev else None,
                is_new=bool(prev) and e.model_id not in prev,
            )
            for e in snap.entries
            # Snapshots computed before a model was retired still hold it.
            if e.model.active or e.model.kind != "foundation"
        ],
        declined=declined,
    )


@router.post("/recompute")
def recompute(db: Session = Depends(get_db)) -> dict:
    """Recompute all snapshots on demand (dev convenience; the batch pipeline
    in pipeline/compute_ratings.py is the production path)."""
    computed = compute_all_snapshots(db)
    return {"ok": True, "computed": computed}
