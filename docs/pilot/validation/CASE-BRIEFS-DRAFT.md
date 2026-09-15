# Three close cases for independent validation

Prepared 9 September 2026. **DRAFT: no human validation, approved rubric or model-output pack yet.** All entities, documents and amounts below are fictional. These are intake briefs, not accounting guidance or answer keys. Do not distribute them as validated shared comparisons.

Send each reviewer the same exact case text and a separate copy of the [independent-review form](../templates/INDEPENDENT-REVIEW.md). Each reviewer independently solves it, identifies missing facts, cites the applicable authoritative guidance and proposes acceptable answers/material-error criteria before seeing the other's work. Reconcile only after both submissions; revise and reapprove any changed brief. Preserve the original submissions privately. David has not yet assigned reviewers; no outreach has been sent.

The full approved brief must include every fact the models and voters need. Evidence fields in the pack are an index of the quoted support below; models receive the approved brief itself, not an unseen attachment or the rubric. Set brief/evidence/rubric hashes only after reconciliation. Generation must happen after both timestamped approvals. The importer checks the records and hashes; an operator must verify that the referenced reviews and approvals actually exist.

## CLOSE-01 · Duplicate receipt accrual · draft v1

**Framework and period:** US GAAP; 31 August 2026 close, still open for adjustments. USD. For this exercise, all identified errors require correction; do not waive a difference on materiality grounds. Ignore tax and foreign exchange. No other transactions affect this receipt.

**Complete case text:** Cedar Works purchased steel and took ownership on delivery. Receiving report RR-829 confirms receipt and acceptance on 29 August. All steel remains on hand at 31 August and on 3 September. The approved purchase order price was $86,400. The perpetual inventory system posted debit Inventory $86,400 / credit Received-not-invoiced $86,400 on 29 August. A separate manual AP close entry posted debit Inventory $86,400 / credit Accrued liabilities $86,400 for the same receipt on 31 August. Neither posting has been reversed, and the supplier invoice has not been entered in AP.

On 3 September, invoice INV-903 for $87,100 arrives. The $700 difference is a contractually agreed delivery charge attributable to this receipt. A signed purchasing addendum dated 28 August supports the charge; it was omitted from the purchase-order amount used by receiving. No goods have been consumed or sold, and no invoice or payment posting has yet occurred. The August financial statements have not been issued.

**Requested response:** Identify the duplicate and any other August adjustment needed. Show proposed entries and resulting receipt-related inventory/liability balances at August close. Explain how the September invoice should clear the existing accruals without double counting and list posting checks. State assumptions if the ledger's clearing mechanism matters.

**Evidence index:** RR-829 receipt; PO price; GL system entry; GL manual entry; INV-903; signed 28 August addendum. All relevant contents are stated above. Reviewers must verify whether alternative clearing-entry presentations are equivalent and resolve timing ambiguity before approval.

## CLOSE-02 · Maintenance invoice after close · draft v1

**Framework and period:** US GAAP; 31 December 2026 year-end close, still open for adjustment. USD. All identified errors require correction for this exercise. Ignore tax, FX and discounting.

**Complete case text:** Alder Services' maintenance contractor completed repairs on 22 December. The operations manager signed a completion and acceptance certificate that day. The work restored an existing production machine to its prior operating condition; it added no capacity, did not extend its originally estimated useful life and did not replace a separately tracked major component. The agreed fixed price in the signed work order was $18,600, with no variable consideration or dispute.

The contractor issued an invoice dated 8 January 2027 for $18,600, received on 9 January. It confirms only the work accepted on 22 December. The December trial balance includes neither a payable/accrual nor an expense or asset for this work. The accounts-payable subledger has no invoice for it. Payment is scheduled for 20 January. The December statements have not been issued.

**Requested response:** Explain the December accounting and proposed entry; identify support to retain. Show how January invoice processing and payment should work without recognizing the cost twice. Explain whether the work changes the equipment balance, using the stated facts.

**Evidence index:** Signed work order; 22 December acceptance certificate; 8 January invoice; December GL and AP search confirming no posting. All relevant contents are stated above. Reviewers must cite authoritative treatment guidance and define which wording or clearing presentations are acceptable alternatives.

## CLOSE-03 · Unexplained supplier-payment difference · draft v1

**Framework and period:** US GAAP; 30 September 2026 close. USD. The $480 difference cannot be waived on materiality grounds in this exercise. Ignore tax and FX. The accountant can request documents but cannot presume their contents.

**Complete case text:** Birch Supply's September bank statement shows an outgoing $12,480 payment dated 29 September with reference SUP-440. The approved payment register also shows $12,480 to supplier SUP-440. The bank balance is confirmed. The general ledger has already recorded debit Payment clearing $12,480 / credit Cash $12,480. No AP-clearing entry has yet been posted.

The AP subledger contains one open invoice for SUP-440: INV-120, $12,000, already recorded to the appropriate expense and AP. No other open item for this supplier appears in the subledger. Remittance advice and the supplier statement have not been obtained. There is no bank-fee advice, settlement agreement, credit note or documented explanation for the extra $480. A preparer proposes debit AP $12,000 / debit Bank fees $480 / credit Payment clearing $12,480 based solely on the matching supplier reference.

**Requested response:** Review the proposed clearing entry. Distinguish what the evidence establishes from what remains unresolved. Explain which confirmations/documents are needed, what can be posted now (if anything), and how to track/escalate the unresolved balance at close. Do not invent a fee, settlement or overpayment explanation.

**Evidence index:** Bank statement; payment register; cash/clearing GL entry; AP open-item search; proposed clearing entry. All relevant contents and missing documents are stated above. Reviewers must resolve whether partial AP clearing is defensible on these facts, enumerate acceptable approaches and define the evidence required for final disposition. If no unambiguous assessable requirement set emerges, revise or exclude the case.

## Handoff and freeze checklist

- Two private independent forms per case, with relevant experience and prior exposure recorded.
- Reconciliation record retaining disagreements and explicitly approved alternatives.
- Final full brief, evidence index, criterion IDs and material-error definitions; two approvals with timezones.
- Generate exactly one pair using the chosen fixed model IDs after approval; retain raw responses and both attempts. Do not cherry-pick retries.
- Validate and import the immutable pack; assign to participants through Close examples.
- Have experts assess anonymous frozen outputs separately, criterion by criterion, preserving original assessments and later adjudication.

These three candidates support close-exception preference and, after expert assessment, case-specific correctness observations. They do not establish general accounting capability or a population model ranking.
