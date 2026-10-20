# Finance & accounting benchmark registry

`registry.json` is the single source of truth for the public benchmark catalog at `/benchmarks`.
Everything else is generated from it:

| File | Produced by | Purpose |
| --- | --- | --- |
| `benchmarks/registry.json` | Hand-edited (PR review) | Canonical metadata and result snapshots |
| `frontend/public/benchmarks.json` | `make benchmarks-build` | Data served to the `/benchmarks` page. Catalog metadata is open (CC BY 4.0); result snapshots stay under each publisher's terms and are cited, not relicensed |
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

## Licensing

Two layers travel together in `benchmarks.json`, and only one of them is ours to license:

- **Catalog metadata** (`id`, name, taxonomy, status, freshness, links, notes) is published under CC BY 4.0. Reusers credit "Calibration Arena benchmark catalog".
- **Result figures and board snapshots** are the publishers' work. We reproduce the headline figure, metric and date as cited facts with a link to the source. We do not relicense them, and a reuser of `benchmarks.json` must follow each publisher's own terms. Several publishers (Artificial Analysis, Mercor, BenchLM) restrict republishing or commercial reuse; see `docs/research/benchmark-reuse-terms.md` before adding a board adapter for a new publisher.

## Status vocabulary

- `leaderboard` – the publisher maintains a public results page that is updated as models ship.
- `snapshot` – results published once (paper, blog post, report) and not maintained.
- `archived` – there was a leaderboard but the publisher has stopped updating it or taken it down.
- `unpublished` – the benchmark exists but has no public model results.
- `unknown` – we have not been able to verify whether results exist.

## Freshness

Saved flags are computed at build time against `catalog_updated` for deterministic
exports. The website recalculates these flags against the visitor's current time
every minute, so a stopped publisher or scheduler cannot freeze freshness warnings:

- `review_due` – `last_verified` more than 45 days before `catalog_updated`.
- `results_stale` – a `leaderboard` whose `as_of` is more than 180 days old.
- `undated_results` – a `leaderboard` whose source shows no date.
- `vendor_published`, `mirror_source` – provenance flags shown alongside results.

## Daily publication

`.github/workflows/benchmarks-daily.yml` refreshes the nine model boards at 13:17 UTC
daily (6:17 a.m. Los Angeles during daylight time, 5:17 a.m. during standard time).
Additional watchdog checks run at 01:47, 07:47 and 19:47 UTC. Schedules run from
`main`; GitHub can delay scheduled jobs. Manual dispatch is also supported.

The public repository uses standard Linux runners. No paid API, Vercel token,
deployment hook or personal GitHub token is needed. The publication step alone
receives the workflow's short-lived `GITHUB_TOKEN`. Its job requests contents-write
permission to update **only `benchmark-data`**, never the application branch.

Flow: independent fetches with bounded retries → per-source validation → aggregate
validation in a staging directory → one Git commit/ref update → public-feed check →
browser verification of all nine boards. A source failure retains that source's
previous board and model observations while healthy sources advance. The job is
marked failed *after* publishing and verifying a coherent partial update. A build
or aggregate-validation failure publishes nothing. Failed Actions runs are the
alert channel; repository watchers/maintainers must enable Actions failure
notifications in their GitHub notification preferences to receive email/web alerts.
The watchdog uses GitHub too: a GitHub-wide scheduler outage cannot notify until it
recovers. The website independently marks checks older than 36 hours overdue.

The Vercel rewrite serves `/benchmark-feed/benchmarks.json` from the public
`benchmark-data` branch. The page falls back to its bundled catalog if that feed
cannot be loaded, and clearly labels this fallback. `benchmarks.json` at the site
root remains the bundled snapshot. GitHub raw delivery can take several minutes to
reflect a new commit; the publication check polls for up to ten minutes.

`last_successful_check` is when a board passed validation. `retrieved` retains its
date-only compatibility field. `as_of` is strictly the publisher's date or null;
neither a fetch nor an unchanged successful check invents a publisher update date.
`last_verified` remains the separate editorial metadata-review date. Vals archive
status propagates to the catalog and cards. “Checked daily” applies only to the
nine imported boards, not the entire 59-entry directory.

Raw HTML, HTTP outcomes, content hashes, candidate JSON, the failure report and
browser verification images are retained as Actions artifacts for 14 days. Public
snapshot commits are kept indefinitely on `benchmark-data`. Raw HTML is not copied
into the public feed or data branch. Published result figures retain publisher terms.

### Run and review locally

```sh
python -m pip install -r backend/requirements-benchmarks.txt
PYTHONPATH=backend python -m pipeline.refresh_benchmarks \
  --output /tmp/benchmark-publication --evidence /tmp/benchmark-evidence
# To preserve a previously published snapshot, supply --previous DIR, where
# DIR/benchmarks.json is the most recent publication. Output must not exist.
PYTHONPATH=backend python -m pipeline.verify_benchmarks
```

The old `make benchmarks-fetch-boards` entry point now creates an immutable
temporary candidate rather than overwriting tracked inputs. It prints the path
and returns failure if any source was rejected.

Review gates reject invalid scores, missing metrics, duplicate publisher
model/configuration identities, metric-definition changes, backwards source dates,
and row-count losses over 20%. Explicitly headed methodology sections are hashed;
a change or disappearance requires review. This detector cannot establish that an
entire evaluation protocol is unchanged: unheaded prose, papers, and upstream
grader changes still need editorial review. Initial snapshots establish the first
methodology hash. The full source evidence is available for that review.

For a legitimate result-round replacement or methodology edit, inspect the saved
`candidate.json` and source HTML, update relevant editorial metadata, and add its
exact `candidate_digest` with a rationale to `refresh-approvals.json` through normal
code review. This only permits the reviewed row-loss/methodology transition; it
does not bypass score, metric, duplicate, date or aggregate validation. Unrelated
future content cannot reuse the approval. Do not weaken a guard to make a run green.

### Activation and rollback

1. Merge the application and workflow changes into `main` and deploy the frontend
   rewrite/UI. Confirm Actions is enabled and contents-write is permitted.
2. Dispatch **Daily benchmark snapshots** on `main`. Its first publication creates
   `benchmark-data`; a successful run verifies the canonical site's JSON snapshot
   identifier and rendered dates for every board. Check the workflow's result and
   evidence, not just the timestamp in the UI.
3. On a bad data release, stop new scheduled publications while investigating and
   restore the desired historical tree as a **new commit** on `benchmark-data`.
   Keep history; do not force-push. Run the public verifier afterward. A restored
   old snapshot will deliberately show old dates/overdue warnings. Re-enable the
   schedule after fixing the importer. Code/rewrite rollback is a separate app deployment.

## Editorial update cadence

| Cadence | Action |
| --- | --- |
| Weekly | `make benchmarks-check`. Review `unreachable`, `redirected` and `changed` URLs across the wider catalog. A changed hash means "look at it", not "the score changed". Review methodology and metadata separately from the automated board checks. |
| Monthly | `make benchmarks-report` for the review queue. Re-verify every `review_due` row. Search for new benchmarks (arXiv, Hugging Face, vendor blogs, Vals/Artificial Analysis) and add them. Re-check `unpublished` and `claim_only` entries for newly published results. |
| On any edit | Bump `catalog_updated`, run `make benchmarks-build`, commit the registry and generated files in the same PR. |

A registry change is a normal PR: the diff of `registry.json` is the audit trail of what changed
between snapshots and who reviewed it.

## Model boards

Publisher adapters copy structured leaderboard data into dated per-benchmark snapshots; they do not
rerun, rescale, or compare results across benchmarks. Weight labels record their basis: `publisher`
means stated by a benchmark publisher, `family` is a curated rule for a well-established model
family, `conflict` means publishers disagree and the status is therefore `unknown`, and `none`
means there is no report or family rule. Cost is shown only when the publisher reports it.

Frontier charts are within-benchmark only and must never be compared across benchmarks. Boards use
daily refresh cadence above. Publisher page changes can break an adapter, in which case
that source keeps its last good snapshot and the workflow reports failure: fix the adapter and
regenerate the snapshot; never hand-edit a board snapshot.

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
