"""User-selected work types. This is explicit routing, not an intent classifier."""
TASKS = {
    "journal-entry": {
        "label": "Journal entry",
        "placeholder": "Describe the transaction, amounts and period…",
        "instruction": "Prepare the journal entry with clearly labeled debits and credits, calculations, timing, and a short supporting memo. State missing facts before making assumptions.",
    },
    "treatment-memo": {
        "label": "Treatment memo",
        "placeholder": "Describe the accounting question, policy and facts…",
        "instruction": "Write a concise accounting treatment memo: issue, relevant facts, assumptions, analysis, conclusion, and unresolved questions. Distinguish the supplied policy from authoritative standards.",
    },
    "workpaper-review": {
        "label": "Workpaper review",
        "placeholder": "Paste a draft or describe the work you want reviewed…",
        "instruction": "Review the supplied workpaper or draft. Identify errors and missing support, explain necessary corrections, and give an approval-readiness conclusion. If no draft is supplied, ask for it rather than inventing one.",
    },
}


def case_task(case_id):
    return "workpaper-review" if case_id in {"utilities-accrual", "software-prepaid"} else "journal-entry"
