"""Ratings math: weighted Bradley-Terry (MM algorithm) over pairwise votes.

Every vote is a pairwise outcome carrying a weight from the rater's credential
tier; BT strengths are fit by Hunter's minorization-maximization iteration and
mapped onto an Elo-like scale anchored at 1200 so scores read familiarly.
Confidence intervals come from bootstrap resampling of the vote set.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass

ANCHOR = 1200.0
SCALE = 400.0  # Elo-style: +400 rating ≈ 10x BT strength

# (winner_model_id, loser_model_id, weight)
Pair = tuple[int | str, int | str, float]


@dataclass
class RatingRow:
    model_id: int | str
    rating: float
    ci_low: float
    ci_high: float
    wins: int
    losses: int
    votes: int
    rank: int = 0


def _normalize(pairs: list) -> list[Pair]:
    return [(p[0], p[1], float(p[2]) if len(p) > 2 else 1.0) for p in pairs]


def _fit_bt(pairs: list[Pair], iters: int = 200, tol: float = 1e-9) -> dict[int | str, float]:
    """Fit Bradley-Terry strengths from weighted (winner, loser, w) pairs via MM.

    Returns strengths normalized to geometric mean 1.0.
    """
    models: set[int | str] = set()
    wins: dict[int | str, float] = defaultdict(float)
    games: dict[tuple[int | str, int | str], float] = defaultdict(float)
    for w, l, wt in pairs:
        if wt <= 0:
            continue
        models.add(w)
        models.add(l)
        wins[w] += wt
        key = (min(w, l), max(w, l))
        games[key] += wt

    if not models:
        return {}

    # Smoothing: one virtual split game per observed pairing keeps strengths
    # finite for models with all-wins/all-losses records.
    for (a, b) in list(games):
        games[(a, b)] += 1.0
        wins[a] += 0.5
        wins[b] += 0.5

    p = {m: 1.0 for m in models}
    for _ in range(iters):
        delta = 0.0
        new_p = {}
        for m in models:
            denom = 0.0
            for (a, b), n in games.items():
                if m == a or m == b:
                    denom += n / (p[a] + p[b])
            if denom <= 0:
                new_p[m] = p[m]
                continue
            new_p[m] = wins[m] / denom
        log_mean = sum(math.log(v) for v in new_p.values() if v > 0) / len(new_p)
        norm = math.exp(log_mean)
        for m in new_p:
            new_p[m] = new_p[m] / norm
            delta = max(delta, abs(new_p[m] - p[m]))
        p = new_p
        if delta < tol:
            break
    return p


def strength_to_rating(strength: float) -> float:
    if strength <= 0:
        return ANCHOR - 4 * SCALE
    return ANCHOR + SCALE * math.log10(strength)


def compute_ratings(
    pairs: list,
    bootstrap_rounds: int = 40,
    seed: int = 7,
) -> list[RatingRow]:
    """Compute ranked rating rows from (winner, loser[, weight]) pairs."""
    pairs = _normalize(pairs)
    pairs = [p for p in pairs if p[2] > 0]
    if not pairs:
        return []

    strengths = _fit_bt(pairs)

    wins: dict[int | str, int] = defaultdict(int)
    losses: dict[int | str, int] = defaultdict(int)
    for w, l, _ in pairs:
        wins[w] += 1
        losses[l] += 1

    # Bootstrap CI on the rating scale.
    samples: dict[int | str, list[float]] = defaultdict(list)
    rng = random.Random(seed)
    for _ in range(max(bootstrap_rounds, 0)):
        resample = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
        for m, s in _fit_bt(resample, iters=60).items():
            samples[m].append(strength_to_rating(s))

    rows: list[RatingRow] = []
    for m, s in strengths.items():
        rating = strength_to_rating(s)
        dist = sorted(samples.get(m, [rating]))
        lo = dist[max(0, int(0.025 * len(dist)) - 1)] if len(dist) > 1 else rating
        hi = dist[min(len(dist) - 1, int(0.975 * len(dist)))] if len(dist) > 1 else rating
        rows.append(
            RatingRow(
                model_id=m,
                rating=round(rating, 1),
                ci_low=round(min(lo, rating), 1),
                ci_high=round(max(hi, rating), 1),
                wins=wins[m],
                losses=losses[m],
                votes=wins[m] + losses[m],
            )
        )

    rows.sort(key=lambda r: r.rating, reverse=True)
    for i, r in enumerate(rows):
        r.rank = i + 1
    return rows
