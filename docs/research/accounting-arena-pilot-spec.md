# Pilot spec: the 10-accountant test and the 50-rater study

**Companion to:** `accounting-arena-evaluation-methodology.md` (§13) and `accounting-arena-decision-memo.md`.
**Purpose:** the minimum set of experiences to put in front of ~10 friendly accountants, the redesigned wider study behind it, and a hand-off build prompt so any model/tool can spin up the experience.
**Interactive reference:** a clickable demo of the judgment screen exists (Claude artifact "Calibration Arena Demo"); the build prompt in Appendix B reproduces it as a real app.

---

## 1. Study shape: many raters × one hour, not few raters × four

The methodology report originally sketched 24 raters × ~4 hours. The founder's instinct — spread the same budget across ~50 people at ~1 hour each — is **better for most of what the study needs**, and cheaper (≈50 paid hours vs 96):

- **What improves:** inter-rater agreement (V1) and variance decomposition (V5) are estimated *across* raters; 50 independent raters beat 24 with more items each. Krippendorff's α handles incomplete overlap natively, so not everyone needs to see everything. Recruiting yes is easier for a 1-hour ask.
- **What degrades, and the patch:**
  - *Per-rater calibration precision:* ~3 gold items per person is far too few to score an individual (see report §8.1 — even 5 traps misclassify badly). Accepted: **this study scores the panel and the format, not individuals.** Individual calibration scores come later, accumulated over weeks of normal use.
  - *Test–retest:* needs the same person twice. Patch: invite a random ~15 of the 50 back for one 10-minute session ≥1 week later (2 repeat items each, different surface parameters).
  - *Trajectory depth:* a 10-minute trajectory review eats a 1-hour session. Patch: only ~half the raters get one trajectory item.
- **Cost re-estimate [assumption: $100–150/hr senior CPA freelance — verify at recruitment]:** 50 × 1h + 15 × 10min ≈ 52.5 hrs → **$5.3–7.9K** rater cost, plus ~$300–800 generation compute. The 10-friend pilot before it: $0.

**Sequencing:** friends pilot (this doc, §2–5) → fix format → 50-rater study (§6) → publish methodology note → leaderboard decisions per the report's pre-registered rules.

---

## 2. The 10-friend pilot: minimum experience set

Goal: watch 10 real accountants use the thing, capture the data structure end-to-end, learn where the format breaks. **Not** a source of model rankings or calibration claims.

**Seven screens, ~25–30 minutes per person:**

| # | Experience | Family | Contains | ~Time |
|---|---|---|---|---|
| 1 | Judgment screen (warm-up) | Journal entry | 4 drafts, all pass checks | 3–4 min |
| 2 | Judgment screen | Journal entry | 4 drafts incl. 1 planted defect (plausible subtlety) | 3–4 min |
| 3 | Judgment screen | Journal entry | 4 drafts, all pass; 2 rubric chips added | 4 min |
| 4 | Judgment screen | Journal entry | 4 drafts incl. 1 planted defect (subtle) | 4 min |
| 5 | Judgment screen | Accrual memo | 4 memos, all defensible (pure judgment) | 5 min |
| 6 | Judgment screen | Accrual memo | 4 memos incl. 1 with undisclosed-assumption defect | 5 min |
| 7 | Trajectory review | Reconciliation | 2 recorded agent runs, side by side | 6–8 min |

**The judgment screen gesture (demo'd in the artifact):** per draft — *"Would you sign off?"* (Sign off / Don't sign / Can't tell) → rank all four, ties allowed → one confidence tap → optional one-line note → submit → reveal (authors + objective-check results + whether they caught the planted item). The sign-off checkbox replaces the hidden trap round: a planted item is just a draft they should refuse to sign.

**Screen 7 (trajectory review):** two condensed storyboards of *real recorded* agent runs on the same reconciliation (each: numbered step list of what the agent examined and posted, the proposed adjusting entries, the final ledger state). Questions: *"Which would you trust to close your client's month?"* / *"What would you check first before signing either?"* (free text — this is Phase-2 product discovery, not measurement). For the pilot, produce the two runs by hand: run two different models through the reconciliation materials in a chat/agent session, transcribe honestly, do not edit their mistakes.

**Capture per screen (the schema that shapes the MVP):** `{rater_id, scenario_id@version, per_draft: {sign_off, rank}, confidence, note?, decision_ms, planted_item_caught?, screen_order, format_variant}` — plus, per person, 5 minutes of talk-aloud notes.

**What you learn:** time per screen and drop-off point; whether "sign off" reads naturally; planted-defect catch rate at two subtlety levels (directional); whether ranks-with-ties confuse anyone; whether rubric chips (screen 3) feel like homework; which trajectory presentation earns trust. **What you must not conclude:** anything about models, anything statistical.

---

## 3. The six scenarios to author (hand-written; no generator yet)

Each needs: brief, policy pack, ground truth, acceptable-solution notes, and (where marked) a planted defect. Author the drafts by prompting 4 different models once each and lightly curating (fix formatting, never substance); label any hand-written draft as such internally.

1. **JE-1 (warm-up):** Machine purchase $45,000 on credit + $2,500 freight paid cash; record acquisition + one month straight-line depreciation (5-yr, no salvage). Ground truth: capitalize $47,500; depreciation $792/mo. All four drafts pass; variation is memo/schedule quality. *(Upgrade of `fixed-asset-purchase`, `backend/app/scenarios.py:93-101`.)*
2. **JE-2 (planted, plausible):** Prepaid annual subscription — $18,000 cash Nov 1, 12-month term; record receipt + November recognition. Planted draft: full $18,000 to Sales Revenue at receipt, confident memo. *(This is the demo scenario; upgrade of `annual-prepaid-saas`, `scenarios.py:83-91`.)*
3. **JE-3 (rubric chips):** Bad-debt write-off $8,400 under allowance method + unexpected $3,000 recovery. Chips: "memo states method?" / "recovery reinstated before collection?" *(Upgrade of `bad-debt-writeoff`, `scenarios.py:103-111`.)*
4. **JE-4 (planted, subtle):** Prepaid insurance $14,400 paid Mar 15 for 12 months from Apr 1. Planted draft: begins amortization in March (one month early) — arithmetically tidy, off-by-one period. Tests fine attention, not gross error.
5. **MEMO-1 (pure judgment):** Year-end bonus accrual: pool = 8% of EBITDA over $2.0M threshold; prelim EBITDA $3.1M with a flagged-uncertain $150K revenue item; board discretion ±20%, prior year −10%. All four memos defensible, different assumptions/presentation. (Worked example 11.3 in the report.)
6. **MEMO-2 (planted, judgment-flavored):** Same family, different company. Planted memo asserts a −10% board discretion as fact with no disclosure and silently includes the uncertain revenue item — the *documentation* is the defect, not the arithmetic.

Reconciliation for screen 7: the Harbor Deli bank rec from report §11.2, cut down to ~20 bank lines and 4 planted discrepancies (duplicate, deposit in transit, unrecorded bank fee, transposition).

---

## 4. What changes in the current MVP (shaping list)

Keep: blinded side-by-side rendering, sandboxed iframes, server-side timing, guest flow, reveal moment, snapshot pipeline. Change:

1. **Session = one screen per scenario**, not a 5-round bracket: replace the `Match` sequence with a single judgment record per (rater, scenario). The bracket FSM (`backend/app/services/arena.py:22,101-106,192-206`) goes away.
2. **Judgment payload** replaces `VoteIn` (`backend/app/schemas.py:160-162`): per-draft sign-off + rank, confidence, optional note; ties allowed.
3. **Hidden trap round → planted-draft mechanic:** a calibration item is a fifth… no — one of the four drafts, flagged server-side (`is_trap` on the generation already exists, `backend/app/models.py:105`); "Don't sign" on it = pass. Delete the separate calibration match.
4. **Reveal shows objective-check results** per draft (pass/fail + why), sourced from the scenario's stored ground truth (`scenarios.py` already stores expected postings — start checking against them).
5. **Prompt box (pilot version):** scenario chips + free text that only fills parameters (amount/date/name substitution); no classifier yet; never silently swap (`frontend/src/components/workspace/PromptComposer.tsx:49-52` currently discards the prompt).
6. **No leaderboard shown in the pilot.** Boards return after the 50-rater study; seeded synthetic votes never in a published fit (`backend/pipeline/seed.py:105-132`).
7. **Remove hard-coded marketing stats** (`frontend/src/components/about/StatBand.tsx:3-7`).

---

## 5. Pilot measurement sheet (fill per rater)

`rater | screens completed | total minutes | JE planted (plausible) caught? | JE planted (subtle) caught? | MEMO planted caught? | ties used? | notes left? | chips completed? | trajectory pick + first-check quote | verbal friction points`

Aggregate: median time/screen; catch rate by subtlety; % sessions completed; % using ties; % leaving notes. Decision heuristics (not statistics): if ≥8/10 finish and the plausible-defect catch rate is high while the subtle one splits people — the format works and difficulty tiers are real. If people sign everything or quit at screen 5, the format needs work before spending on the 50-rater study.

---

## 6. The 50-rater study (Stage B, redesigned)

- **Raters:** 50 paid, credential-verified (CPA or ≥5 yrs close experience); mix of controllers, seniors, auditors recorded as cohort labels.
- **Materials:** 3 families × 10 scenarios × 3 surface variants (this *does* need the parameterized generator), 4 configs + 1 hidden expert golden draft.
- **Assignment:** each item judged by ≥3 raters; each rater ≈ 10 judgment items + 3 gold + (half of raters) 1 trajectory packet ≈ 55–60 min. Format A/B: half rank-with-ties, half pairwise-with-full-response-set, to measure forced-choice bias and format speed.
- **Retest:** 15 raters × 10 min, ≥1 week later, 2 repeat items each.
- **Measures & pre-registered decision rules:** as report §13 (α ≥ 0.4 or role-structured disagreement; defect-catch ROC by subtlety; preference-vs-rubric regression; variance components) — unchanged except the assignment design.
- **Explicit trade accepted:** no individual rater gets a meaningful calibration score from this study; that accrues in-product afterward.

---

## Appendix A — pilot run-of-show (per friend)

1. 2-min intro script: "You're grading four anonymous drafts of the same task. Would you sign each? Rank them. One is sometimes planted wrong — don't tell me which you think it is, just judge." 2. Screens 1–7 while they talk aloud (record with consent). 3. 5-min debrief: hardest screen? anything feel like homework? would you do 3 of these a week for a calibration badge? 4. Log the measurement sheet same day.

---

## Appendix B — build prompt for another model/tool

Paste everything between the lines into v0/Lovable/Bolt/Claude to spin up the pilot experience. It reproduces and extends the published demo.

---

You are building "Calibration Arena — pilot", a small web app for blind expert review of AI-generated accounting work. Stack: single-page React (or vanilla JS) + a tiny backend (or Supabase/local JSON) that persists judgment records. No auth beyond a name/email field on entry (this is a 10-person pilot).

**Core flow.** A session is a fixed sequence of 7 scenario screens. Each of screens 1–6 shows: (a) a scenario brief card (2–3 sentences, plus policy chips like "accrual basis", "revenue ratable over service period", "materiality $500"); (b) FOUR anonymous draft cards in a 2×2 grid (stack on mobile), labeled Draft A–D, each rendering an accounting work product: journal-entry tables (Account / Debit / Credit columns, right-aligned tabular numerals, totals row) and an italic memo line; (c) per draft, two controls: a segmented "Would you sign off?" (Sign off / Don't sign / Can't tell) and a rank picker 1–4 where the same number may be assigned to two drafts (tie); (d) a session footer: 3-way confidence segment (Not very / Fairly / Very), an optional one-line text input "what tipped your ranking?", and a Submit button disabled until all four drafts have both a sign-off and a rank plus a confidence tap.

**Reveal.** On submit, in place: each draft card shows a verdict strip — green "Passes objective checks" or red "Fails objective checks" with a one-sentence reason from the scenario data; author pseudonyms replace "Author hidden"; a summary panel states whether the user declined to sign the planted draft (if this scenario has one), phrased exactly as: caught → "You caught the planted defect."; can't-tell → "You hesitated on the planted defect."; signed → "You signed off on the planted defect." plus one sentence explaining the defect. Then a "Next scenario" button.

**Screen 3 variant:** after ranking, show two yes/no rubric chips (from scenario data, e.g. "Does the memo state the method used?") before submit. **Screen 7 variant (trajectory review):** instead of four drafts, TWO side-by-side "recorded agent run" cards, each with a numbered step list (~8–12 steps, e.g. "Opened bank statement PDF", "Flagged duplicate entry #1042", "Posted adjusting entry: Dr Bank Fees $45 / Cr Cash $45"), a proposed-entries table, and an end-state line ("Clearing account balance after run: $0.00" / "$1,290.00"). Controls: "Which run would you trust to close the month?" (A / B / Neither), and a required free-text "What would you check first before signing either?"

**Data model.** Persist one record per submitted screen: `{rater_name, rater_email, scenario_id, scenario_version, started_at, submitted_at, decision_ms, per_draft: [{draft_id, sign_off, rank}], confidence, note, rubric_chips?, trajectory_choice?, trajectory_check_first?}`. Provide an export-all-JSON button on a hidden `/admin` route.

**Content.** Scenario data lives in one `scenarios.json`. Include this example as scenario 2 and stub the other six with the same shape (titles: fixed-asset purchase; bad-debt write-off w/ chips; prepaid insurance off-by-one-month planted; two bonus-accrual memo scenarios; one reconciliation-trajectory scenario):

```json
{
  "id": "JE-PP-004", "version": 1, "family": "journal-entry",
  "brief": "On November 1, Meridian Fitness LLC collected $18,000 cash for a 12-month software subscription beginning that day. Record the cash receipt and November's revenue recognition, with memos a reviewer could rely on.",
  "policy_chips": ["FY2026 · accrual basis", "Policy: revenue ratable over service period", "Materiality $500"],
  "planted_draft": "C",
  "drafts": [
    {"id":"A","author_pseudonym":"Atlas 4","passes_checks":true,
     "verdict":"Correct deferral and ratable recognition; memo cites policy and shows remaining deferred balance.",
     "entries":[{"desc":"Cash receipt, Nov 1","lines":[["Cash",18000,0],["Deferred Revenue",0,18000]]},
                {"desc":"November recognition","lines":[["Deferred Revenue",1500,0],["Subscription Revenue",0,1500]]}],
     "memo":"$18,000 deferred at receipt per ratable-recognition policy; 1/12 recognized for November. Deferred balance carried forward: $16,500."},
    {"id":"B","author_pseudonym":"Ledger-1","passes_checks":true,
     "verdict":"Amounts and treatment correct; documentation thin (no policy reference).",
     "entries":[{"desc":"Cash receipt","lines":[["Cash",18000,0],["Deferred Revenue",0,18000]]},
                {"desc":"Revenue recognition","lines":[["Deferred Revenue",1500,0],["Subscription Revenue",0,1500]]}],
     "memo":"As discussed."},
    {"id":"C","author_pseudonym":"Corvid 9","passes_checks":false,
     "verdict":"Recognizes the full $18,000 on day one and credits Sales Revenue directly, violating the ratable-recognition policy.",
     "entries":[{"desc":"Sale recorded, Nov 1","lines":[["Cash",18000,0],["Sales Revenue",0,18000]]}],
     "memo":"Full contract value recorded at point of sale. Entry verified and in balance; no further entries required."},
    {"id":"D","author_pseudonym":"Fathom 2","passes_checks":true,
     "verdict":"Correct treatment with a full amortization schedule; wordier memo.",
     "entries":[{"desc":"Cash receipt, Nov 1","lines":[["Cash",18000,0],["Deferred Revenue",0,18000]]},
                {"desc":"November recognition","lines":[["Deferred Revenue",1500,0],["Subscription Revenue",0,1500]]}],
     "memo":"Consideration received in advance of performance is deferred and recognized ratably over the twelve-month service period beginning November 1, consistent with company policy. Full schedule maintained in the recognition workpaper."}
  ]
}
```

**Visual direction.** Professional workpaper feel, not startup-gradient: light paper ground with a slight green cast (#F7F8F5), white cards, near-black green ink (#1B2420), one spruce accent (#2E5E4E); IBM Plex Sans for UI, IBM Plex Serif inside draft documents, IBM Plex Mono for amounts/labels with tabular numerals; red/green reserved for fail/pass verdicts only. Support dark mode via CSS tokens. Progress ticks "N of 7" in the header. Footer on every screen: "Demo pilot · fictional companies and author names · no client data."

**Acceptance checklist.** (1) Cannot submit until 4 sign-offs + 4 ranks + confidence. (2) Ties allowed and stored. (3) decision_ms measured server/app-side from screen open to submit. (4) Reveal never appears before submit; author names hidden until reveal. (5) All 7 records exportable as JSON. (6) Works on a phone. (7) No real vendor or model names anywhere.

---

*End of pilot spec.*
