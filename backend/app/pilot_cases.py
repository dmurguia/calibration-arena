"""Authored practice cases, not model runs or independently validated benchmarks.

Rubrics describe the explicit policy in the brief. Ledger checks operate on
structured postings, not on an LLM's claims about its own answer.
"""
from copy import deepcopy
from hashlib import sha256
import json


def draft(key, text, postings, expected, note):
    return {"artifact_id": key, "text": text, "postings": deepcopy(postings),
            "expected_postings": deepcopy(expected), "review_note": note,
            "author": "Authored practice draft", "model_id": None,
            "origin": "authored-fixture", "version": "1"}


def checks(d):
    rows = d["postings"]
    return [
        {"label": "Debits equal credits", "passed": all(sum(r[2] for r in rows if r[0] == date) == 0 for date in {r[0] for r in rows})},
        {"label": "Amounts, accounts and dates match the stated case policy", "passed": sorted(rows) == sorted(d["expected_postings"])},
    ]


def entry(date, debit, credit, amount):
    return [[date, debit, amount], [date, credit, -amount]]


insurance = entry("March 15", "Prepaid insurance", "Cash", 1440000)
revenue = entry("November 1", "Cash", "Deferred revenue", 1800000) + entry("November 30", "Deferred revenue", "Revenue", 150000)
accrual = entry("December 31", "Utilities expense", "Accrued liabilities", 240000)
asset = entry("May 1", "Equipment", "Accounts payable", 4500000) + entry("May 1", "Equipment", "Cash", 250000)
prepaid = entry("June 1", "Prepaid software", "Cash", 1200000) + entry("June 30", "Software expense", "Prepaid software", 100000)

CASES = [
    {"id": "insurance-cutoff", "title": "The books balance. Does the timing?", "topic": "Prepaids · period cutoff", "minutes": 3,
     "brief": "A fictional company pays $14,400 on March 15 for insurance covering April 1 through March 31 next year. Review the March payment and month-end treatment. Policy: recognize insurance expense evenly over the coverage period; no expense before coverage starts. Amounts are material. No other adjustments apply.",
     "takeaway": "A balanced entry can still belong to the wrong period.",
     "expected": "At payment: Dr Prepaid insurance $14,400; Cr Cash $14,400. March insurance expense is $0. Begin $1,200 monthly recognition in April, when coverage starts.",
     "drafts": [draft("insurance-supported-v1", "March 15\nDr Prepaid insurance   $14,400\nCr Cash                $14,400\n\nMarch close\nNo amortization entry. Coverage has not begun.\n\nReview note\nRetain the policy dates with the schedule. Recognize $1,200 each month from April through March next year.", insurance, insurance, "Payment and expense recognition use different dates. This draft follows the stated coverage policy."),
                draft("insurance-early-v1", "March 15\nDr Prepaid insurance   $14,400\nCr Cash                $14,400\n\nMarch close\nDr Insurance expense    $1,200\nCr Prepaid insurance    $1,200\n\nReview note\nThe annual premium is allocated at $1,200 per month beginning in the payment month. Remaining prepaid balance: $13,200.", insurance + entry("March 31", "Insurance expense", "Prepaid insurance", 120000), insurance, "This planted cutoff error starts expense a month early. Equal debits and credits do not resolve the period error.")]},
    {"id": "subscription-revenue", "title": "Cash today. Revenue over time.", "topic": "Deferred revenue · recognition", "minutes": 3,
     "brief": "A fictional software company receives $18,000 on November 1 for 12 months of service starting that day. Policy: revenue is earned equally each month over the service term. Review the receipt and November close entries. There are no separate deliverables, taxes or refunds.",
     "takeaway": "Cash received and revenue earned answer different questions.",
     "expected": "November 1: Dr Cash $18,000; Cr Deferred revenue $18,000. November 30: Dr Deferred revenue $1,500; Cr Revenue $1,500. Closing deferred revenue: $16,500.",
     "drafts": [draft("revenue-schedule-v1", "November 1\nDr Cash                $18,000\nCr Deferred revenue    $18,000\n\nNovember 30\nDr Deferred revenue     $1,500\nCr Revenue              $1,500\n\nReview note\nOne month of twelve delivered. Closing liability: $16,500. Release $1,500 monthly while the stated service pattern continues.", revenue, revenue, "Recognition follows the explicit ratable-service policy."),
                draft("revenue-cash-v1", "November 1\nDr Cash                $18,000\nCr Revenue             $18,000\n\nNovember 30\nNo adjustment required.\n\nReview note\nThe annual fee has been received in full, so recognize the contract value on receipt.", entry("November 1", "Cash", "Revenue", 1800000), revenue, "This planted error treats collection as completion of the service.")]},
    {"id": "utilities-accrual", "title": "Which workpaper would you keep?", "topic": "Accruals · reviewability", "minutes": 3,
     "brief": "A fictional company's December electricity has been consumed but not invoiced. Its approved usage estimate is $2,400. Policy: accrue consumed utilities at month-end using the approved estimate, then reverse on January 1 before processing the invoice. Review only the December entry. Both drafts use the same approved estimate.",
     "takeaway": "Correct numbers can leave room for a real preference about documentation.",
     "expected": "December 31: Dr Utilities expense $2,400; Cr Accrued liabilities $2,400. Both drafts match the case policy. Documentation preference is your judgment; no objectively correct winner is assigned.",
     "drafts": [draft("utilities-concise-v1", "December 31\nDr Utilities expense    $2,400\nCr Accrued liabilities  $2,400\n\nReview note\nRecord December electricity using the approved usage estimate. Reverse January 1; reconcile to the invoice when received.", accrual, accrual, "The compact memo states the source and reversal action. Whether it needs more detail is a review preference."),
                draft("utilities-checklist-v1", "December 31\nDr Utilities expense    $2,400\nCr Accrued liabilities  $2,400\n\nBasis\nDecember service consumed; vendor invoice pending. Measurement: approved usage estimate, $2,400.\n\nClose checklist\n• Attach approved estimate to this workpaper.\n• Reverse the entry January 1.\n• Reconcile the eventual bill against the estimate and investigate differences.", accrual, accrual, "The longer checklist makes follow-up work explicit. Both drafts have the same posting; length alone is not correctness.")]},
    {"id": "asset-freight", "title": "A small cost with a different home.", "topic": "Fixed assets · classification", "minutes": 3,
     "brief": "A fictional company buys equipment for $45,000 on credit on May 1 and pays $2,500 freight in cash that day to bring it to its operating location. Policy: capitalize purchase price and directly attributable inbound freight. Review acquisition entries only; exclude depreciation, tax and installation.",
     "takeaway": "A correct total is not enough when costs land in the wrong accounts.",
     "expected": "Capitalize $47,500 total: Dr Equipment $45,000 / Cr Accounts payable $45,000, and Dr Equipment $2,500 / Cr Cash $2,500. Depreciation is outside this case.",
     "drafts": [draft("asset-capitalized-v1", "May 1\nDr Equipment           $45,000\nCr Accounts payable    $45,000\n\nDr Equipment            $2,500\nCr Cash                 $2,500\n\nReview note\nTotal acquisition cost: $47,500, including inbound freight under the stated policy. Depreciation is handled separately.", asset, asset, "The freight is assigned to the asset under the supplied capitalization policy."),
                draft("asset-expensed-v1", "May 1\nDr Equipment           $45,000\nCr Accounts payable    $45,000\n\nDr Freight expense      $2,500\nCr Cash                 $2,500\n\nReview note\nEquipment acquired on account. Delivery paid in cash and expensed as a current operating cost.", entry("May 1", "Equipment", "Accounts payable", 4500000) + entry("May 1", "Freight expense", "Cash", 250000), asset, "The planted classification error expenses freight despite the explicit case policy.")]},
    {"id": "software-prepaid", "title": "The same answer, a different handoff.", "topic": "Prepaids · reviewability", "minutes": 3,
     "brief": "A fictional company pays $12,000 on June 1 for software access from June 1 through May 31 next year. Policy: record the payment as a prepaid asset and expense an equal amount each month. Review payment and June close. No implementation costs or other components apply.",
     "takeaway": "Professional preference often lives in the handoff, after the arithmetic agrees.",
     "expected": "June 1: Dr Prepaid software $12,000 / Cr Cash $12,000. June 30: Dr Software expense $1,000 / Cr Prepaid software $1,000. Both drafts meet the stated policy; closing prepaid is $11,000.",
     "drafts": [draft("software-brief-v1", "June 1\nDr Prepaid software    $12,000\nCr Cash                $12,000\n\nJune 30\nDr Software expense     $1,000\nCr Prepaid software     $1,000\n\nReview note\nRecognize 1/12 of annual access in June. Remaining prepaid: $11,000.", prepaid, prepaid, "Both postings are supported; the compact handoff leaves schedule maintenance implicit."),
                draft("software-handoff-v1", "June 1\nDr Prepaid software    $12,000\nCr Cash                $12,000\n\nJune 30\nDr Software expense     $1,000\nCr Prepaid software     $1,000\n\nReview note\nService period: June 1–May 31. Allocate $12,000 / 12 = $1,000 monthly. June ending balance: $11,000.\n\nHandoff\nAttach the contract, schedule the remaining eleven monthly releases, and confirm a zero prepaid balance at May close.", prepaid, prepaid, "Both postings are supported; the explicit handoff may be useful or unnecessary for your workflow.")]},
]


def snapshot(case):
    data = deepcopy(case)
    data.update(version="pilot-cases-v1", rubric_version="stated-policy-v1", validation="Authored practice case; independent accountant validation pending")
    for d in data["drafts"]:
        d["checks"] = checks(d)
        d["sha256"] = sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
    return data
