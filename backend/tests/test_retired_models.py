"""Models dropped for launch stay out of matches and off the leaderboard."""
from sqlalchemy import select

from app.db import RETIRED_MODEL_SLUGS, SessionLocal, _retire_models
from app.models import ArenaModel, Vote
from app.services.arena import eligible_models
from app.services.leaderboard import compute_snapshot
from app.categories import CATEGORIES, OVERALL
from pipeline.seed import ROSTER


def test_roster_drops_retired_models():
    slugs = {r[0] for r in ROSTER}
    assert not slugs & set(RETIRED_MODEL_SLUGS)
    assert "gemini-3-pro" in slugs


def test_startup_deactivates_previously_seeded_rows(client):
    with SessionLocal() as db:
        # Simulate a database seeded before the cut: rows exist, active, with votes.
        rows = []
        for slug in RETIRED_MODEL_SLUGS:
            m = db.scalar(select(ArenaModel).where(ArenaModel.slug == slug))
            if m is None:
                m = ArenaModel(slug=slug, name=slug, organization="o", provider="openrouter",
                               provider_model_id=slug, kind="foundation")
                db.add(m)
            m.active = True
            rows.append(m)
        db.flush()
        keep = db.scalar(select(ArenaModel).where(ArenaModel.slug == "gpt-5-5"))
        cat = next(iter(CATEGORIES))
        db.add(Vote(category=cat, winner_model_id=rows[0].id, loser_model_id=keep.id, synthetic=True))
        db.commit()
        ids = {m.id for m in rows}

    _retire_models()
    _retire_models()  # idempotent

    with SessionLocal() as db:
        for slug in RETIRED_MODEL_SLUGS:
            assert db.scalar(select(ArenaModel.active).where(ArenaModel.slug == slug)) is False
        # History kept: the vote row still references the retired model.
        assert db.scalar(select(Vote.id).where(Vote.winner_model_id.in_(ids))) is not None
        for c in CATEGORIES:
            assert not ids & {m.id for m in eligible_models(db, c)}
        snap = compute_snapshot(db, OVERALL, bootstrap_rounds=0)
        if snap is not None:
            assert not ids & {e.model_id for e in snap.entries}

    board = client.get(f"/api/leaderboard/{OVERALL}").json()
    assert not {e["model"]["slug"] for e in board["entries"]} & set(RETIRED_MODEL_SLUGS)
