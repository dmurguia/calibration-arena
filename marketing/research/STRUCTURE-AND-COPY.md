# Calibrated company website: structure and editorial decisions

Original structure proposal, prepared 22 September 2026. **Superseded in part by the [wording review and cleanup](COPY-REVIEW.md): the hero, homepage structure and supporting copy have since been simplified.** The intended company domain is **calibrated.co**, following the founder's final correction. This work does not change DNS or publish a site.

## Reference analysis

These are structural references, not templates to copy. Their customers, results, infrastructure, certifications and team credentials are not Calibrated's evidence.

| Reference | Observed structure | Adaptation for Calibrated |
| --- | --- | --- |
| [AfterQuery homepage](https://www.afterquery.com/) | Compact navigation, short positioning statement, two immediate actions, then the problem and offering. Research, careers and a detailed footer extend the company story. | A clear opening, one commercial action and one path to inspect the work. Keep enterprise, approach, leaderboard and company navigation. Omit research/blog until there is material to publish. |
| [AfterQuery enterprise page](https://www.afterquery.com/solutions) | A lifecycle introduction leads into named services, each with a concrete description and supporting evidence. Visitors can enter at a specific stage. | Explain the scope, handoff and reason for each part of an engagement. Replace unsupported customer proof with an inspectable example and clear evidence boundaries. |
| [AfterQuery products](https://www.afterquery.com/products) | A broad taxonomy describes types of training material and environments, without forcing a single product interface. | Organize around what the customer receives: evaluations, reviewed material, environments and an iteration record. Avoid a sprawling catalog of unbuilt capabilities. |
| [Applied Compute homepage](https://www.appliedcompute.com/) | The page moves from company proposition to product explanation and partnership models, with substantial customer and technical proof. Embedded and managed work are made explicit. | Use separate embedded and managed engagement descriptions, with scope and responsibilities. Do not borrow infrastructure claims, customer logos or certification badges. |
| [Applied Compute training](https://www.appliedcompute.com/training) | Product visuals sit beside specific descriptions of training work. Deeper capabilities and evidence follow, before a closing action. | Show one working example and a compact explanation of the practice loop, followed by the shape of a deliverable. Keep product detail proportionate to current evidence. |
| [Applied Compute blog](https://www.appliedcompute.com/blog) | A categorized index separates company, platform, research and case-study content. It supplies a substantial evidence layer. | Reserve this pattern for later. An empty publication section would add navigation without adding credibility. |

References were read live and the AfterQuery homepage and Applied Compute training page were visually inspected. Wording, illustrations and product claims were not copied into the Calibrated pages.

## Positioning

**Company:** Calibrated Co. helps teams turn professional standards into the evaluation and training material their knowledge-work agents need.

**Brand idea:** The art of better.

**Commercial audience:** Enterprise teams building agents that perform professional work. The homepage needs to help a buyer identify a useful first project. It must also give prospective employees and investors a coherent company thesis.

**Product relationship:** Calibration Arena is the accounting workspace and engagement tool. It is an example of the company's work, not the definition of the company. The site does not imply that an accountant practice vote is independently validated training evidence.

**Evidence available:** Approved brand kit; current repository implementation; authored accounting practice cases; deterministic posting checks. No customer names, commercial outcomes or public model-quality results have been provided.

**Proposed commercial scope:** Evaluations, training material and RL environments are offered as scoped project discussions. The site does not claim an operating end-to-end training cloud, GPU fleet, performance uplift or deployment capability.

## Information architecture

| Page | Visitor question | Content | Next step |
| --- | --- | --- | --- |
| Home | What is this company and why should I care? | Positioning, practice example, outputs, partnerships, company thesis | Discuss a project; inspect the approach |
| For enterprises | What would we work on together? | A scoped workflow; criteria, materials, assessment and revision handoffs; embedded/managed; practical questions | Discuss the workflow |
| Our approach | Is there real substance behind the offer? | A compact practice loop, functional Arena excerpt, distinct checks, artifact table | Scope a project |
| Leaderboard | Where can I inspect comparisons? | Honest publication status, evidence required for rankings, relationship to Arena | Inspect the sample; configurable Arena destination |
| Company | What is the thesis and working culture? | Craft, current accounting starting point, working principles, collaboration | Start a conversation |
| Get data | Can we get training material? | Purposeful placeholder for the future data offering; no invented catalog | Prepare a data brief |
| Contact | How do I take a concrete next step? | Local project-brief preparation, copy and download; configurable real contact destination | Share through the configured email/booking route after launch |
| Privacy / Terms | How is this site operated? | Actual preview behavior and marked draft notices | Complete operator details before public launch |

Private review routes: `/review/`, `/directions/craft/`, `/directions/outcomes/`. These are excluded from the public sitemap and always noindex.

## Two directions

### Craft

Opening: **The art of better agents.**

The graphite study shares the first screen with a direct descriptor and two actions. The sequence is company thesis, outputs, example, partnerships, company and closing action. The hypothesis is that a memorable company introduction will help people understand the craft and care behind the work.

### Outcomes

Opening: **Agents that meet the standard of your work.**

The opening is more direct about the enterprise job. A compact charcoal section explains the process before the working example; outputs and partnerships follow. The hypothesis is that a buyer can more quickly recognize an engagement. This is the initial default after the JEV comparison, with uncertainty documented separately.

## Brand execution

Use the merged September 21 kit in `brand/calibrated/`. Paper `#F4F1E9`, charcoal `#464643`, graphite `#656460`, and small leather accents `#70543E`. The primary mark is paper on charcoal. Lettering is the supplied outlined wordmark. IBM Plex Sans Regular carries reading and headings; IBM Plex Mono is limited to metadata and numbers. Font licenses accompany the exports.

Both designs avoid gradients, stock icon libraries, fabricated evidence, feature-card triplets, bento panels, terminals, glass effects, rounded cards, decorative orbs, dot grids and hover motion. All meaningful text is live HTML. The source list's request for loading treatment is met by avoiding unnecessary loading states: copy and the sample data arrive in the initial HTML, with no model or data fetch to mask.

## Why the interactive example is credible within its limits

The insurance-cutoff fixture is copied from `backend/app/pilot_cases.py`, including structured postings, expected postings and original provenance. The browser computes balancing and exact policy matching. Draft B balances but records expense before coverage starts. This is a functioning check on a real repository fixture, not a screenshot of an invented dashboard. Independent accountant validation remains pending, and no benchmark claim follows from it.

## Before public release

Connect a confirmed contact destination. Confirm the legal operator and complete the two draft notices for the actual host. Supply a verified Arena URL if it should be linked. Review commercial wording against the work you want to commit to. Then approve hosting and domain changes as a separate step. The current local demo is complete without those external actions.
