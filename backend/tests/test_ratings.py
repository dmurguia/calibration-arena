from app.pilot_ratings import compute_ratings, strength_to_rating


def test_empty_votes():
    assert compute_ratings([]) == []


def test_ordering_recovers_dominance():
    # 1 beats 2 far more often than it loses; 2 dominates 3 likewise.
    pairs = [(1, 2)] * 30 + [(2, 1)] * 5 + [(2, 3)] * 30 + [(3, 2)] * 5 + [(1, 3)] * 20 + [(3, 1)] * 2
    rows = compute_ratings(pairs, bootstrap_rounds=5)
    ordered = [r.model_id for r in rows]
    assert ordered == [1, 2, 3]
    assert rows[0].rank == 1 and rows[2].rank == 3
    assert rows[0].rating > rows[1].rating > rows[2].rating


def test_counts_and_win_rate_inputs():
    pairs = [(1, 2), (1, 2), (2, 1)]
    rows = compute_ratings(pairs, bootstrap_rounds=0)
    by_id = {r.model_id: r for r in rows}
    assert by_id[1].wins == 2 and by_id[1].losses == 1 and by_id[1].votes == 3
    assert by_id[2].wins == 1 and by_id[2].losses == 2


def test_all_wins_stays_finite():
    rows = compute_ratings([(1, 2)] * 10, bootstrap_rounds=0)
    by_id = {r.model_id: r for r in rows}
    assert by_id[1].rating > by_id[2].rating
    assert abs(by_id[1].rating) < 3000  # smoothing keeps it bounded


def test_anchor_scale():
    assert strength_to_rating(1.0) == 1200.0
    assert round(strength_to_rating(10.0)) == 1600
