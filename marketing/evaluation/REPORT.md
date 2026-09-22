# JEV homepage comparison

## Recommendation

Use **Outcomes** as the initial enterprise homepage. Keep **Craft** available for founder review. The recommendation combines the founder's enterprise priority with the one stable persona preference in this evaluation; it is not a claim that one design wins across all audiences.

## What ran

Two successful live requests to `typesafe-ai/jev` through the founder's existing Vercel AI Gateway, using `ai@7.0.107`. Run times: 22 September 2026, 07:43:50 and 07:43:53 UTC. Both requests evaluated ten typed questions. Each used 8,322 input tokens and reported 482 output tokens. No credentials, request headers or raw SDK response objects are saved.

The input contains the built homepage text, heading hierarchy, shared supporting pages, six persona briefs and explicit evidence limits. Candidate IDs were neutral. The second pass reversed the candidates to expose order sensitivity. The same criteria allowed a **no clear difference** answer. There was no cherry-picking or third pass selected to force a winner.

The API performs a structured text assessment. It did not view screenshots, recruit actual people, measure conversion or establish customer demand. Its probabilities represent its classification distribution for these prompts, not the likelihood that a visitor buys or likes a page.

## Results

| Persona | Pass 1: Craft first | Pass 2: Outcomes first | Interpretation |
| --- | --- | --- | --- |
| Enterprise buyer | Outcomes (0.69) | Outcomes (0.67) | The only stable direction preference. Supports Outcomes for the primary audience. |
| Technical lead | No clear difference (0.41) | Outcomes (0.52) | Some support for Outcomes; not stable enough for a strong claim. |
| Procurement sponsor | Outcomes (0.49) | No clear difference (0.56) | Weak separation; common scope and partnership pages do much of the work. |
| Investor | Craft (0.35) | Outcomes (0.35) | Essentially tied and order-sensitive. No reliable winner. |
| Prospective employee | Craft (0.52) | Outcomes (0.38) | Order-sensitive; second-pass top probability ties the displayed no-difference probability after rounding. No reliable winner. |
| Domain expert | Craft (0.42) | Outcomes (0.48) | Order-sensitive with substantial no-difference probability. No reliable winner. |

Numbers in parentheses are the returned probability of the selected class, retained to make weak preferences visible. They must not be presented as persona conversion rates or human test results. A two-pass swap detects instability but does not isolate position bias from ordinary model variability.

Both candidates' largest-gap classifications selected the **unconfigured contact path** in both passes (0.76–0.84). Both received relatively high probability on clearly distinguishing current examples and stage from proven results (0.87–0.89). These are model judgments, not an independent legal or factual certification.

## Decision made

The default `/` now uses the unchanged Outcomes candidate. `/directions/craft/` and `/directions/outcomes/` retain the evaluated versions. The enterprise, approach, company and inquiry pages are shared. Subsequent visual spacing, mobile navigation and no-JavaScript refinements do not alter the evaluated marketing copy. The internal review page was expanded to display these findings.

The immediate practical improvement is a confirmed contact email or booking URL. It was requested from the founder; no address has been guessed. The placeholder prepares a useful brief and states plainly that it has not been submitted.

## Reproduce and audit

- `run-1-input.json`, `run-2-input.json`: full evidence packets and questions.
- `run-1-result.json`, `run-2-result.json`: raw typed answers, model, SDK version, timestamps, usage and SHA-256 input hashes.
- `summary.json`: choices mapped back to the real directions.
- `../scripts/evaluate.mjs`: sequential runner with bounded timeout, safe error reporting and hash-matched result reuse.

The official [Vercel model page](https://vercel.com/ai-gateway/models/jev) documents JEV's typed evaluation interface. The installed SDK types were also inspected before the run. Existing credentials were loaded into the evaluation process only. The public marketing application has no dependency on the Gateway or an API key.

Next validation should be a small set of actual conversations: ask enterprise builders to explain what the company does, what they would ask for and what evidence they need before a pilot. Record their words before revising the positioning. That work has not been performed here.
