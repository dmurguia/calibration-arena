# Finance & accounting benchmark registry

`registry.json` is the single source of truth for the public benchmark catalog at `/benchmarks`.
Everything else is generated from it:

| File | Produced by | Purpose |
| --- | --- | --- |
| `benchmarks/registry.json` | Hand-edited (PR review) | Canonical metadata and result snapshots |
| `frontend/public/benchmarks.json` | `make benchmarks-build` | Data served to the `/benchmarks` page and reusable as open data |
| `docs/research/public-finance-accounting-benchmarks.md` | `make benchmarks-build` | Readable catalog for the repo and research docs |
| `benchmarks/source-state.json` | `make benchmarks-check` | Last observed HTTP status, redirect and text hash for every cited URL |

`backend/tests/test_benchmarks.py` fails if the generated files are out of date with the registry.

## What we maintain vs. what publishers maintain

This follows the Design Arena pattern (stable model IDs, periodic cached snapshots, explicit
freshness and a "preliminary" state) but without their voting methodology. We are a directory of
other people's benchmarks, not a re-scoring service.

| Calibration Arena owns | The benchmark publisher owns |
| --- | --- |
| Stable `id`, name, taxonomy (`domains`, `task_format`, `grader`) | Methodology, tasks, data release, license |
| `data_access`, `results_status`, `relevance` classification | Scores, leaderboard, model list |
| A dated snapshot of the headline result (`results`) with a source link | The grader implementation and version |
| `last_verified`, freshness flags, lifecycle (`archived`) | Deprecation or retirement decisions |

Rules:

1. **Never edit, normalize or re-rank a publisher's score.** Copy the headline figure, metric and
   `as_of` date exactly as the linked source states them. If the source is ambiguous, leave
   `leader`/`leader_score` null and explain in `results.note`.
2. **Label provenance.** `results.source_type` is `first_party` (the publisher's own page),
   `vendor_report` (a company benchmarking its own product or its partners), `paper`, or `mirror`
   (a third-party aggregator republishing someone else's numbers). Vendor-run benchmarks are flagged
   in the UI.
3. **Status is independent of data access.** A benchmark can have a live leaderboard with private
   data (DualEntry), or open data and no published results.
4. **Absence is a first-class state.** A related benchmark with no public model results is listed as
   `unpublished`, not omitted. Products that make accuracy claims without a public evaluation go in
   `products` as `claim_only`; products with no claim found are `none_found`. Both appear under
   "Awaiting public results" on the site.
5. **Snapshots, not realtime.** Every result carries `as_of`; every row carries `last_verified`.
   Nothing on the page implies the numbers are live.

## Status vocabulary

- `leaderboard` – the publisher maintains a public results page that is updated as models ship.
- `snapshot` – results published once (paper, blog post, report) and not maintained.
- `archived` – there was a leaderboard but the publisher has stopped updating it or taken it down.
- `unpublished` – the benchmark exists but has no public model results.
- `unknown` – we have not been able to verify whether results exist.

## Freshness

Computed at build time against `catalog_updated`, so rebuilds are deterministic:

- `review_due` – `last_verified` more than 45 days before `catalog_updated`.
- `results_stale` – a `leaderboard` whose `as_of` is more than 180 days old.
- `undated_results` – a `leaderboard` whose source shows no date.
- `vendor_published`, `mirror_source` – provenance flags shown alongside results.

## Update cadence

| Cadence | Action |
| --- | --- |
| Weekly | `make benchmarks-check`. Review `unreachable`, `redirected` and `changed` URLs. A changed hash means "look at it", not "the score changed". For each leaderboard that actually changed, update `results` and `last_verified`. |
| Monthly | `make benchmarks-report` for the review queue. Re-verify every `review_due` row. Search for new benchmarks (arXiv, Hugging Face, vendor blogs, Vals/Artificial Analysis) and add them. Re-check `unpublished` and `claim_only` entries for newly published results. |
| On any edit | Bump `catalog_updated`, run `make benchmarks-build`, commit the registry and generated files in the same PR. |

A registry change is a normal PR: the diff of `registry.json` is the audit trail of what changed
between snapshots and who reviewed it.

## Adding a benchmark

1. Add an object to `benchmarks` with every required key (see an existing entry and the enums in
   `backend/pipeline/benchmarks.py`). Use a kebab-case `id` that will never change.
2. Link the canonical source. Prefer the publisher's page over a mirror; if only a mirror exists,
   set `source_type: "mirror"`.
3. Set `last_verified` to the date you opened the source.
4. `make benchmarks-validate && make benchmarks-build`, then open a PR.

Outside publishers can request a listing or correction by opening an issue titled
"Benchmark listing: <name>" with a link to their results.

## Retiring or renaming

Never delete or rename an `id`. If a benchmark is retired set `results_status: "archived"` and
explain in `notes`; if it moves, update `links` and note the old URL in `notes`.
