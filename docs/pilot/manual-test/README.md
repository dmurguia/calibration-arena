# Manual test pack: invoicing, AR reporting, bank rec, open prompt

Prompts and files for checking the finance tasks by hand. Synthetic data only: Harbor & Pine Coffee Roasters LLC,
Ledgerline Advisory LLC and their counterparties are fictional. Each file passes `pilot_assets.prepare_assets` (the
server's own extractor), and every task stays far below the 25,000-character combined limit.

**Use the answer keys to check plumbing, not to rank models.** The keys were drafted by Claude, which is also one
side of the local pair, so agreement with a key is partly agreement with Claude's own priors. Arithmetic (totals,
caps, aging buckets) is safe to check against. Judgment calls, listed under each task as "contestable", should be
judged by an accountant, not scored. No independent accountant has reviewed these keys yet.

## Running a manual test

1. Start the backend on http://localhost:8000/ with `ARENA_INFERENCE_BACKEND=local-cli` (see
   [Local models](../LOCAL-MODELS.md)), and rebuild `frontend/dist` if you have pulled since the last build.
2. Pick the task, attach the files below, paste the prompt and send.
3. The CLI bridge works when both answers come back and, after you vote, the reveal names the configured Codex and
   Claude models. "Live models are not connected yet" means the bridge did not start. "Failed to fetch" with every
   request red in the network tab means the server is not running.
4. The run's `generation_attempts` in `pilot_runs` record each CLI binary, the requested and resolved model, and
   token usage. The Claude CLI uses its own login, not the `ANTHROPIC_API_KEY` in `.env` (the bridge strips API keys).
   On a Claude subscription, the reported cost is a list-price estimate, not a charge.

## Changing the pack

Edit the data in [generate.py](generate.py), then from the repository root run:

```bash
.venv/bin/python docs/pilot/manual-test/generate.py
```

It rewrites the files here and prints the answer-key figures. Copy changed figures into this README.
`backend/tests/test_manual_test_pack.py` fails if a file stops passing the extractor, the bank rec stops tying, or a
key total printed by the generator no longer appears below.

Known issues to fix in a later revision:
- The invoicing period (October 2026) runs past the date the pack was written, so a model that knows today's date
  may flag the change order and time entries as future-dated.
- The billable-items file has a "Client Approved" column, but the terms never say approval is needed before billing.
  See the invoicing contestable points.

| Task in the composer | Attach (role → file) |
|---|---|
| Invoicing | Contract or billing terms → `billing-terms.txt`; Billable items → `billable-items.csv` |
| AR reporting | AR ledger or aging export → `ar-ledger.xlsx` |
| Bank reconciliation | Bank statement → `bank-statement.pdf` (or `bank-statement.csv`); Cash ledger → `cash-ledger.csv` |
| Open prompt | No task, no files |

Choosing a task pre-fills the app's default prompt. Paste the prompt below over it, or keep the default as a control.

---

## 1. Invoicing

> Prepare the October 2026 draft invoice for Sunset Hotel Group under SOW #3. Use only the attached terms and billable items. Show each line (retainer, time and materials by role, expenses, software, tax) with quantity, rate and amount, and list every billable item you excluded or adjusted with the reason. Apply the fee cap and change order exactly as written; if a term is ambiguous, say how you treated it rather than choosing silently. Do not issue the invoice.

**Answer key**

| Line | Amount |
|---|---|
| ERP support retainer | 3,000.00 |
| Engagement Director 20.0 h × 240 | 4,800.00 |
| Senior Associate 79.0 h × 165 | 13,035.00 |
| Associate 8.0 h × 110 (18.0 h worked, 10.0 h covered by retainer) | 880.00 |
| Travel and mileage (784.40 incurred, capped) | 750.00 |
| Software seats 6 × 95 | 570.00 |
| Sales tax on software, 8.625% | 49.16 |
| **Total** | **23,084.16** |

Checkable:
- 9/30 Alvarez 3.0 h is outside the October period. It belongs on September's invoice, so it should be flagged, not dropped silently.
- 10/15 Alvarez 7.5 h "ASC 842 memo draft" appears twice ($1,237.50 duplicate).
- 10/10 internal training is non-billable.
- The 10/20 Nguyen note says "Bill at Senior rate per J. Kim". §1.4 says that needs a change order, so bill it at the Associate rate and flag it.
- Time and materials comes to 18,715.00, above the original $18,000 cap; pre-10/20 T&M was only $8,402.50.
- Travel totals $784.40 (mileage 76 × 0.70 = 53.20 + hotel 412.80 + air 318.40) against a $750 cap. The $186.25 client dinner has no pre-approval.
- The resale certificate is not on file, so the 8.625% tax applies. Services and the retainer are not taxed.
- PO-SHG-7781 must appear on the invoice. Terms are 2/10, net 30.

Contestable:
- 10/28 Nguyen 3.0 h is marked "Client Approved = N", but the terms never require client approval to bill time. The key
  holds it back ($330, total 23,084.16). Billing it on a literal reading of the terms (total $23,414.16) is defensible.
  In the first local run, Claude held it back and Codex billed it.
- CO-2 is effective 10/20, mid-month, but the cap is monthly. The key treats October's cap as $22,000; the answer
  should name the ambiguity either way. Cutting the bill to $18,000 without explanation is a miss.

## 2. AR reporting

> Prepare the AR aging as of the reporting date in the attached ledger: current, 1–30, 31–60, 61–90 and over 90 days past due, by customer and in total. Reconcile the aging total to the subledger total and to the GL control account, and explain any difference. Call out overdue concentration, credits or unapplied cash, and any rows whose dates or terms don't make sense. Calculate DSO only if the file gives you what you need, and show the formula.

**Answer key** (aged by due date; credits shown as current and not netted against invoices)

| Customer | Current | 1–30 | 31–60 | 61–90 | Over 90 | Total |
|---|---:|---:|---:|---:|---:|---:|
| Northside Grocers Co-op | 9,585.85 | 4,980.00 | – | 5,120.00 | – | 19,685.85 |
| Bayside Cafe | 1,290.10 | – | 985.40 | – | 1,460.00 | 3,735.50 |
| Mission District Bagels | 1,280.00 | 2,615.80 | – | – | 2,240.00 | 6,135.80 |
| Sunset Hotel Group | 21,345.00 | – | 9,850.00 | – | – | 31,195.00 |
| Golden Gate Coworking | 3,930.00 | – | 1,875.00 | – | – | 5,805.00 |
| Marin Farm Market | 2,890.00 | 2,765.00 | – | – | 3,180.00 | 8,835.00 |
| Telegraph Ave Books & Brew | 910.00 | 845.00 | – | – | – | 1,755.00 |
| **Total** | **41,230.95** | **11,205.80** | **12,710.40** | **5,120.00** | **6,880.00** | **77,147.15** |

Checkable:
- The GL control account is 77,622.15 against a subledger of $77,147.15. The $475.00 difference is unexplained; the answer should call for investigation, not force a plug.
- INV-2210 has no due date. Net 30 gives 9/11, so 19 days past due.
- Mission Bagels has $1,200 of unapplied cash with no remittance. Sunset's CM-0412 for −$350 is meant for INV-2215 but has not been applied.
- INV-2236 and INV-2219 have zero balances and drop out.
- Things to flag: the disputed INV-2161, INV-2129 in collections, and Bayside on credit hold.
- Concentration: Sunset is 40.4% of total AR. Past-due AR is $35,916.20, led by Northside ($10,100) and Sunset ($9,850).
- DSO ≈ 77,147.15 / 118,460 × 92 days ≈ 59.9 days (about 60.3 on the GL balance). The $4,200 allowance sits below the $6,880 that is over 90 days.

Contestable:
- INV-2201 shows a due date of 9/16, which does not match Net 30 from 7/18 (8/17). The key ages it by the terms
  (44 days, 31–60); the recorded date gives 14 days (1–30). Either is fine if the conflict is flagged.
- The key shows the $1,200 unapplied cash and CM-0412 as current. Netting CM-0412 against INV-2215 is also reasonable.

## 3. Bank reconciliation

> Reconcile the September 2026 bank statement for operating account ****4417 to the 1010 cash ledger. Show the adjusted bank balance and the adjusted book balance side by side, list outstanding checks and deposits in transit, and propose the journal entries needed to correct the books. Flag anything you cannot explain from these two documents, including differences carried in from the prior month, and tell me what support you'd need before posting.

**Answer key**

| Bank | | Book | |
|---|---:|---|---:|
| Statement balance 9/30 | 22,708.59 | Ledger balance 9/30 | 28,878.08 |
| + Deposit in transit 9/30 | 4,275.60 | − Service fee | 45.00 |
| − O/S check 1112 | 2,318.75 | + Interest | 12.38 |
| − O/S check 1114 | 960.00 | − NSF Bayside chk 4471 | 1,150.00 |
| − O/S check 1091 (August) | 615.40 | − Returned item fee | 35.00 |
| | | + Check 1105 transposition (1,524 booked vs 1,254 cleared) | 270.00 |
| | | − Duplicate Square 9/19 | 2,860.42 |
| | | − Unrecorded ACH KDZ Holdings | 1,980.00 |
| **Adjusted bank** | **23,090.04** | **Adjusted book** | **23,090.04** |

Checkable:
- **Deliberate gap:** check 1091 ($615.40) appears in neither file. The August opening difference is $1,324.60, which equals the 3,180.00 deposit cleared 9/1, less check 1088 for 1,240.00 cleared 9/3, less $615.40. A good answer isolates the $615.40 and asks for the August reconciliation instead of inventing a check.
- Check sequence: 1110 is void in the ledger, and 1113 is missing from both documents.
- The NSF should reopen Bayside INV-2219 in AR.
- Correcting the Valley Dairy check is Dr Cash / Cr AP (or the original expense) for $270, not a new payment.

Contestable:
- The key's adjusted balance assumes the $615.40 is check 1091, outstanding from August. An answer that leaves it as an
  unreconciled opening difference is also sound.
- The $1,980 KDZ Holdings debit has no support. The key holds it in suspense pending investigation; posting it to an
  expense needs a stated assumption.
- Whether the $35 returned-item fee is recharged to the customer.

## 4. Open prompt (no files)

> We're a US GAAP SaaS company with a calendar year-end. On September 15, 2026 we signed a three-year contract: $180,000 per year subscription billed annually in advance, plus a $45,000 one-time implementation fee. Implementation is mostly data migration and configuration that only we perform, and it takes about six weeks. Access starts October 1. The customer can terminate at the end of year one or year two with 60 days' notice and a $20,000 termination fee. They paid $225,000 on October 1. Walk me through the contract term, performance obligations, transaction price, and the revenue, deferred revenue and contract balances at September 30 and December 31, 2026, with journal entries. State any judgments and where reasonable accountants could disagree.

This prompt is mostly judgment, so there is no single right answer. The points below are what a strong answer
should address, not a score sheet.
- Whether the $20,000 fee is a substantive termination penalty. If it is not, the enforceable contract term is one year, with renewal-like options after that.
- Whether implementation is distinct. If it is not, the $45,000 combines with the subscription and is recognized over the period the service is provided. The answer should also say whether the upfront fee creates a material right over the renewal years.
- At September 30 there should be no revenue and no receivable or deferred revenue, since nothing has been billed, paid or transferred.
- At December 31, with a one-year term and implementation combined: (180,000 + 45,000) × 3/12 = $56,250 recognized and $168,750 deferred. The answer should show how a material-right view changes this.
- It should not recognize the implementation fee at a point in time without arguing that implementation is distinct.
