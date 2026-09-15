# Case validation and correctness

This is an operator workflow, separate from the one-click public comparison. No current sample becomes independently validated merely because this document exists.

## Before model generation

1. Select two experienced accountants with relevant task/framework experience. Record the basis for qualification, identity, conflicts and review date privately.
2. Give each the same numbered brief, framework, period, materiality and source policy. Give neither the proposed key, authored drafts nor the other's response. Each completes a separate copy of [the independent review form](templates/INDEPENDENT-REVIEW.md).
3. Ask each to solve the case, list acceptable alternatives, identify necessary missing facts, and define what a material error would be. “Insufficient facts” is valid when accompanied by the specific fact and how it changes the answer.
4. After both submit, compare their solutions. Reconcile differences in a written adjudication record. If interpretation remains disputed, revise and re-review the case or exclude it. Do not choose the answer a model happened to produce.
5. Freeze the brief, agreed criterion checklist, acceptable alternatives, sources and versions. Both reviewers sign the final scope. Any substantive later edit creates a new version and revalidation requirement.
6. Only then generate real model responses with fixed settings, preserve the exact outputs and randomize their display order. Keep a separate `model-output-assessment` copy of the checklist for each frozen output.

For the existing samples, validators should independently solve the brief before seeing the authored drafts. Those drafts cannot retrospectively become real model outputs.

## What correctness means

Use case-specific requirements, not a single vague “correct” button. Each requirement has an expected result, acceptable alternatives, materiality, evidence and status: **met / not met / not assessable / not applicable**. “Not assessable” must name the missing evidence; it is not half a pass. Report it separately. Professional writing quality and preference are separate dimensions.

Example checklist for the fictional insurance sample's stated policy (illustrative, not independently validated):

| Criterion | Expected requirement | Type |
|---|---|---|
| Initial recognition | $14,400 debit to prepaid insurance and credit to cash on March 15 | Account treatment / amount |
| Recognition period | No insurance expense in March because coverage starts April 1 | Timing |
| Monthly expense | $1,200 each covered month, April through the following March | Calculation / timing |
| Reconciliation | March prepaid balance remains $14,400; postings balance | Calculation / completeness |
| Explanation | Tie the treatment to the supplied coverage dates and policy | Evidence / policy |

Automate exact checks where the output contains inspectable structured postings. Human reviewers assess prose, reasoning, missing facts and acceptable alternatives. A balanced journal entry alone does not prove correct accounting. An LLM can suggest issue categories; it cannot serve as the sole correctness authority.

## Capture during ordinary use

The product stores optional issue reports under each response. Capture the selected category and note verbatim, answer artifact/hash, position, participant/run IDs, timestamp, taxonomy version and whether authors were already revealed. Do not turn a report into a verified defect until an expert assesses it. Do not treat a missing report as a passed criterion.

The current categories are calculation, timing, account treatment, policy/framework, missing facts, unsupported claim and other. The open note captures specifics such as “March expense should be zero; coverage begins April 1.” Both fields are useful: categories make patterns countable; text makes a report inspectable.

## Assessing frozen real outputs

Have both experts independently mark every applicable criterion against each anonymous model response. Record a short quotation/location and correction for failures. Resolve disagreements only after preserving both original assessments. Summarize material errors, unmet criteria and unresolved items separately from the public preference tally. Do not require the everyday user to do this full assessment.

Keep three distinct records:

- **Case validation:** is the task well specified and its acceptable-answer rubric defensible?
- **Output assessment:** does this exact model output meet that rubric?
- **User preference:** which output would this reviewer rather use?

Private files are enough for the first six cases. Store completed forms outside the public repository and commit only blank templates, synthetic case versions and consent-cleared aggregate findings. The current application exports preferences and issue reports; it does not yet ingest signed expert validation forms or distribute a shared model-output benchmark pack.
