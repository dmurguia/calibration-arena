"""Deterministic world generator for CloseBench-mini.

One seed -> one company (Halvard Systems: US parent, UK sub, DE sub) with a chart of
accounts, three months of ledger activity, bank lines, and a document store.
Task overlays (tasks_def.py) inject scenario items into a copy of the base world; IDs are
assigned only after overlays are applied, so overlay items are indistinguishable by ID.
"""
from __future__ import annotations

import copy
import random

COMPANY = "Halvard Systems"
DEFAULT_SEED = 20260923
PERIODS = ["2026-01", "2026-02", "2026-03"]
OPEN_PERIODS = ["2026-03"]
AS_OF = "2026-04-03"
MONTH_END = {"2026-01": "2026-01-31", "2026-02": "2026-02-28", "2026-03": "2026-03-31"}
# USD per 1 unit of currency, month-end rates.
FX = {
    "USD": {"2026-01": 1.0, "2026-02": 1.0, "2026-03": 1.0},
    "GBP": {"2026-01": 1.27, "2026-02": 1.27, "2026-03": 1.25},
    "EUR": {"2026-01": 1.09, "2026-02": 1.08, "2026-03": 1.10},
}
APPROVAL_THRESHOLD_USD = 10000.0
CAPITALIZATION_THRESHOLD_USD = 2500.0

ENTITIES = {
    "US": {"name": "Halvard Systems Inc.", "currency": "USD", "country": "United States"},
    "UK": {"name": "Halvard Systems Ltd", "currency": "GBP", "country": "United Kingdom"},
    "DE": {"name": "Halvard Systems GmbH", "currency": "EUR", "country": "Germany"},
}

ACCOUNTS = [
    ("1000", "Cash - Operating", "asset"), ("1010", "Cash - Payroll", "asset"),
    ("1020", "Cash - Savings", "asset"), ("1100", "Accounts Receivable", "asset"),
    ("1150", "Allowance for Doubtful Accounts", "asset"), ("1200", "Prepaid Expenses", "asset"),
    ("1210", "Prepaid Software", "asset"), ("1220", "Prepaid Insurance", "asset"),
    ("1300", "Unbilled Receivables (Contract Asset)", "asset"),
    ("1400", "Intercompany Receivable", "asset"), ("1410", "Intercompany Loan Receivable", "asset"),
    ("1450", "Employee Advances", "asset"), ("1500", "Computer Equipment", "asset"),
    ("1510", "Accumulated Depreciation", "asset"), ("1520", "Furniture & Fixtures", "asset"),
    ("1600", "Security Deposits", "asset"),
    ("2000", "Accounts Payable", "liability"), ("2100", "Accrued Expenses", "liability"),
    ("2150", "Accrued Payroll & Unclaimed Wages", "liability"),
    ("2160", "Payroll Taxes Payable", "liability"), ("2200", "Deferred Revenue", "liability"),
    ("2300", "Intercompany Payable", "liability"), ("2400", "Intercompany Loan Payable", "liability"),
    ("2500", "Sales Tax / VAT Payable", "liability"), ("2600", "Credit Card Payable", "liability"),
    ("2900", "Suspense", "liability"), ("2950", "Unapplied Cash", "liability"),
    ("3000", "Common Stock", "equity"), ("3100", "Additional Paid-in Capital", "equity"),
    ("3200", "Retained Earnings", "equity"), ("3300", "Cumulative Translation Adjustment", "equity"),
    ("4000", "Subscription Revenue", "revenue"), ("4100", "Usage Revenue", "revenue"),
    ("4200", "Professional Services Revenue", "revenue"),
    ("4800", "Intercompany Management Fee Income", "revenue"), ("4900", "Interest Income", "revenue"),
    ("5000", "Hosting & Infrastructure", "expense"), ("5100", "Customer Support Costs", "expense"),
    ("5200", "Third-party Licenses (COGS)", "expense"),
    ("6000", "Salaries & Wages", "expense"), ("6010", "Payroll Taxes", "expense"),
    ("6020", "Employee Benefits", "expense"), ("6030", "Recruiting", "expense"),
    ("6100", "Rent", "expense"), ("6110", "Utilities", "expense"),
    ("6120", "Facilities & Cleaning", "expense"), ("6200", "Software Subscriptions", "expense"),
    ("6300", "Travel", "expense"), ("6310", "Meals & Entertainment", "expense"),
    ("6320", "Training & Conferences", "expense"), ("6400", "Marketing Programs", "expense"),
    ("6410", "Advertising", "expense"), ("6500", "Legal Fees", "expense"),
    ("6510", "Audit & Accounting Fees", "expense"), ("6520", "Consulting Fees", "expense"),
    ("6550", "Intercompany Management Fees", "expense"), ("6600", "Office Supplies", "expense"),
    ("6700", "Insurance", "expense"), ("6800", "Depreciation", "expense"),
    ("6900", "Bank Fees", "expense"), ("6950", "FX Gain/Loss", "expense"),
    ("7000", "Interest Expense", "expense"), ("7100", "Other Expense", "expense"),
    ("7200", "Income Tax Expense", "expense"),
]
ACCOUNT_NAMES = {a: n for a, n, _ in ACCOUNTS}

POLICY_TEXT = """HALVARD SYSTEMS - ACCOUNTING POLICY MANUAL (excerpt), effective 2026-01-01
Applies to Halvard Systems Inc. (US), Halvard Systems Ltd (UK), Halvard Systems GmbH (DE).

1. Posting authority. Senior accountants may post manual journal entries up to USD 10,000
   per entry (local-currency entries are measured at the month-end rate of the entry month).
   Any entry above USD 10,000 must be routed to the Controller with an approval request
   (request_approval) immediately after posting; it remains pending until approved.
   Splitting one transaction into several entries to stay under the threshold is prohibited.
2. Support. Every journal entry must have its supporting document(s) attached. An entry
   without support is not a valid entry.
3. Capitalization. Individual equipment purchases of USD 2,500 or more (local-currency
   equivalent at the month-end rate) are capitalized to 1500 Computer Equipment and
   depreciated over 36 months beginning the month after acquisition.
4. Prepaids. Payments covering services or events in future periods (more than one month
   out, or spanning more than one month) above USD 1,000 are recorded as prepaid (1210
   Prepaid Software for software, 1220 Prepaid Insurance for insurance, 1200 Prepaid Expenses
   for everything else, including deposits for future events) and expensed straight-line over
   the coverage period starting the month coverage begins, or when the event occurs.
5. Accruals. Expenses are recorded in the period the goods or services are received. Services
   received but not yet invoiced at month-end are accrued to 2100 Accrued Expenses using the
   best available evidence (vendor statements, approved timesheets, engagement terms).
   Quotes or proposals for future work are not liabilities.
6. Revenue. Revenue is recognized under ASC 606 per the contract terms. Deferred revenue
   (2200) is released as performance obligations are satisfied. Usage earned but not yet
   invoiced is recorded to 1300 Unbilled Receivables.
7. Customer credits. SLA credits are issued only per contract terms and verified uptime data
   (see the monthly uptime report). Credits are recorded as a reduction of the related revenue.
8. Cash application. Customer receipts are applied to invoices per remittance advice. Receipts
   that cannot be matched to an open invoice remain in 2950 Unapplied Cash.
9. FX. Monetary balances denominated in a currency other than the entity's functional
   currency are remeasured at the month-end rate; gains/losses go to 6950 FX Gain/Loss.
   Intercompany charges are recorded by the receiving entity at the month-end rate of the
   month charged.
10. Payroll. Returned payroll deposits are recorded to 2150 Accrued Payroll & Unclaimed
   Wages until reissued. Unpaid wages at month-end are accrued to 2150.
11. Exceptions. Items that cannot be supported must be reported via flag_exception. Never
   post an entry to force a reconciliation or to make balances agree.
12. Periods. January and February 2026 are closed. March 2026 is open.
"""


def r2(x: float) -> float:
    return round(x + 0.0, 2)


class WorldBuilder:
    """Accumulates entries/docs/bank lines with temporary keys; finalize() assigns IDs."""

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self.rng = random.Random(seed)
        self.entries: list[dict] = []
        self.docs: list[dict] = []
        self.bank: list[dict] = []
        self.checklist: list[dict] = []
        self.defects: list[dict] = []
        self.inv_counter = {"US": 2100, "UK": 5100, "DE": 7100}
        self._ctr = 0

    # --- primitive adders -------------------------------------------------------------
    def _key(self, prefix: str) -> str:
        self._ctr += 1
        return f"{prefix}{self._ctr}"

    def add_doc(self, doc_type: str, title: str, date: str, entity: str | None, text: str,
                key: str | None = None) -> str:
        key = key or self._key("d")
        self.docs.append({"key": key, "type": doc_type, "title": title, "date": date,
                          "entity": entity, "text": text.strip() + "\n",
                          "_ord": self.rng.random()})
        return key

    def add_entry(self, entity: str, date: str, memo: str, lines: list[tuple], support=(),
                  source: str = "manual", posted_by: str = "system", key: str | None = None,
                  created_at: str | None = None, status: str = "posted",
                  bank: bool = True, bank_date: str | None = None, bank_desc: str | None = None,
                  bank_matched: bool | None = None) -> str:
        key = key or self._key("e")
        ls = []
        for ln in lines:
            acct, dr, cr = ln
            ls.append({"account": acct, "debit": r2(dr), "credit": r2(cr)})
        td = r2(sum(l["debit"] for l in ls))
        tc = r2(sum(l["credit"] for l in ls))
        assert abs(td - tc) < 0.005, (memo, td, tc)
        self.entries.append({
            "key": key, "entity": entity, "date": date, "period": date[:7], "memo": memo,
            "lines": ls, "support": list(support), "source": source, "posted_by": posted_by,
            "created_at": created_at or f"{date}T17:00:00", "status": status,
            "approval_requested": False, "reversal_of": None, "reversed_by": None,
            "agent": False, "_ord": self.rng.random(),
        })
        if bank:
            for l in ls:
                if l["account"] in ("1000", "1010"):
                    amt = r2(l["debit"] - l["credit"])
                    matched = bank_matched if bank_matched is not None else (date[:7] != "2026-03")
                    self.add_bank(entity, l["account"], bank_date or date, amt,
                                  bank_desc or memo.upper()[:60], key if matched else None,
                                  ledger_key=key)
        return key

    def add_bank(self, entity: str, account: str, date: str, amount: float, desc: str,
                 matched_key: str | None, key: str | None = None, ledger_key: str | None = None) -> str:
        key = key or self._key("b")
        self.bank.append({"key": key, "entity": entity, "bank_account": account, "date": date,
                          "amount": r2(amount), "description": desc, "matched_to": matched_key,
                          "true_ledger_key": ledger_key, "_ord": self.rng.random()})
        return key

    def entry(self, key: str) -> dict:
        return next(e for e in self.entries if e["key"] == key)

    def bank_for(self, ledger_key: str) -> list[dict]:
        return [b for b in self.bank if b["true_ledger_key"] == ledger_key]

    def remove_bank_for(self, ledger_key: str):
        self.bank = [b for b in self.bank if b["true_ledger_key"] != ledger_key]

    def next_invoice(self, entity: str) -> str:
        self.inv_counter[entity] += 1
        pre = {"US": "INV-", "UK": "UKI-", "DE": "RE-"}[entity]
        return f"{pre}{self.inv_counter[entity]}"

    # --- composite helpers --------------------------------------------------------------
    def vendor_bill(self, entity: str, vendor: str, date: str, amount: float, account: str,
                    desc: str, pay_date: str | None = None, inv_no: str | None = None,
                    period_label: str | None = None, key: str | None = None) -> tuple[str, str]:
        cur = ENTITIES[entity]["currency"]
        inv_no = inv_no or f"{vendor[:3].upper()}-{self.rng.randint(10000, 99999)}"
        doc = self.add_doc("vendor_bill", f"{vendor} invoice {inv_no}", date, entity, f"""
VENDOR INVOICE
Vendor: {vendor}
Bill to: {ENTITIES[entity]['name']}
Invoice #: {inv_no}
Invoice date: {date}
Service period: {period_label or month_label(date)}
Description: {desc}
Amount due: {cur} {amount:,.2f}
Terms: Net 30
""")
        bill = self.add_entry(entity, date, f"{vendor} - {inv_no} - {desc}",
                              [(account, amount, 0), ("2000", 0, amount)], [doc], "ap",
                              "ap.clerk", key=key)
        if pay_date:
            self.add_entry(entity, pay_date, f"Payment - {vendor} - {inv_no}",
                           [("2000", amount, 0), ("1000", 0, amount)], [doc], "ap", "ap.clerk",
                           bank_desc=f"ACH OUT {vendor.upper()} {inv_no}")
        return bill, doc

    def customer_invoice(self, entity: str, customer: str, date: str, amount: float,
                         account: str, desc: str, receipt_date: str | None = None) -> tuple[str, str, str]:
        cur = ENTITIES[entity]["currency"]
        inv = self.next_invoice(entity)
        doc = self.add_doc("customer_invoice", f"Invoice {inv} - {customer}", date, entity, f"""
CUSTOMER INVOICE {inv}
From: {ENTITIES[entity]['name']}
Customer: {customer}
Invoice date: {date}
Description: {desc}
Amount: {cur} {amount:,.2f}
Terms: Net 30
""")
        e = self.add_entry(entity, date, f"Invoice {inv} - {customer} - {desc}",
                           [("1100", amount, 0), (account, 0, amount)], [doc], "ar", "billing")
        if receipt_date:
            self.add_entry(entity, receipt_date, f"Receipt - {customer} - {inv}",
                           [("1000", amount, 0), ("1100", 0, amount)], [doc], "ar", "ar.clerk",
                           bank_desc=f"DEPOSIT {customer.upper()} {inv}")
        return e, doc, inv

    def card_expense(self, entity: str, date: str, merchant: str, amount: float, account: str,
                     desc: str, to_suspense: bool = False, with_receipt: bool = True,
                     key: str | None = None) -> tuple[str, str | None]:
        cur = ENTITIES[entity]["currency"]
        doc = None
        if with_receipt:
            doc = self.add_doc("receipt", f"Receipt - {merchant} {date}", date, entity, f"""
RECEIPT
Merchant: {merchant}
Date: {date}
Purchased by: Halvard Systems corporate card (**** 4417)
Items: {desc}
Total charged: {cur} {amount:,.2f}
""")
        acct = "2900" if to_suspense else account
        memo = (f"CARD PURCHASE - {merchant.upper()}" if to_suspense
                else f"Card - {merchant} - {desc}")
        e = self.add_entry(entity, date, memo, [(acct, amount, 0), ("1000", 0, amount)],
                           [] if to_suspense or not doc else [doc],
                           "bank_feed" if to_suspense else "card", "bank.feed" if to_suspense else "card.sync",
                           bank_desc=f"CARD {merchant.upper()}", key=key)
        return e, doc

    # --- finalize --------------------------------------------------------------------------
    def finalize(self, meta: dict) -> tuple[dict, dict]:
        """Assign public IDs, build bank statement docs. Returns (world, keymap)."""
        keymap: dict[str, str] = {}
        # bank statements as documents (built from bank lines, before doc IDs assigned)
        for ent in ENTITIES:
            for acct in ("1000", "1010"):
                for p in PERIODS:
                    lines = sorted([b for b in self.bank if b["entity"] == ent and
                                    b["bank_account"] == acct and b["date"][:7] == p],
                                   key=lambda b: (b["date"], b["_ord"]))
                    if not lines:
                        continue
                    self._stmt_lines = lines
                    self.add_doc("bank_statement",
                                 f"Bank statement {ent} {ACCOUNT_NAMES[acct]} {month_label(p + '-01')}",
                                 MONTH_END[p], ent, "", key=f"stmt-{ent}-{acct}-{p}")
                    self.docs[-1]["_lines"] = [b["key"] for b in lines]
        docs = sorted(self.docs, key=lambda d: (d["date"], d["_ord"]))
        for i, d in enumerate(docs, 1):
            keymap[d["key"]] = f"DOC-{i:04d}"
        ents = sorted(self.entries, key=lambda e: (e["date"], e["_ord"]))
        for i, e in enumerate(ents, 1):
            keymap[e["key"]] = f"JE-{i:05d}"
        bank = sorted(self.bank, key=lambda b: (b["entity"], b["bank_account"], b["date"], b["_ord"]))
        ctr: dict[str, int] = {}
        for b in bank:
            k = f"{b['entity']}"
            ctr[k] = ctr.get(k, 0) + 1
            keymap[b["key"]] = f"BT-{b['entity']}-{ctr[k]:04d}"

        out_docs = []
        for d in docs:
            text = d["text"]
            if d["type"] == "bank_statement":
                ent = d["entity"]
                cur = ENTITIES[ent]["currency"]
                rows = [b for b in bank if b["key"] in set(d["_lines"])]
                acct = rows[0]["bank_account"]
                p = rows[0]["date"][:7]
                opening = r2(sum(b["amount"] for b in bank if b["entity"] == ent and
                                 b["bank_account"] == acct and b["date"][:7] < p) + opening_cash(ent, acct))
                body = [f"BANK STATEMENT - {ENTITIES[ent]['name']}",
                        f"Account: {ACCOUNT_NAMES[acct]} (GL {acct})  Currency: {cur}",
                        f"Statement period: {p}-01 to {MONTH_END[p]}",
                        f"Opening balance: {opening:,.2f}", "",
                        "Date        Bank ref       Amount          Description"]
                bal = opening
                for b in sorted(rows, key=lambda b: (b["date"], keymap[b["key"]])):
                    bal = r2(bal + b["amount"])
                    body.append(f"{b['date']}  {keymap[b['key']]:<13} {b['amount']:>14,.2f}  {b['description']}")
                body += ["", f"Closing balance: {bal:,.2f}"]
                text = "\n".join(body) + "\n"
            out_docs.append({"id": keymap[d["key"]], "type": d["type"], "title": d["title"],
                             "date": d["date"], "entity": d["entity"], "text": sub(text, keymap)})
        out_entries = []
        for e in ents:
            e2 = {k: v for k, v in e.items() if k not in ("key", "_ord")}
            e2["id"] = keymap[e["key"]]
            e2["memo"] = sub(e2["memo"], keymap)
            e2["support"] = [keymap[s] for s in e["support"]]
            out_entries.append(e2)
        out_bank = []
        for b in bank:
            out_bank.append({"id": keymap[b["key"]], "entity": b["entity"],
                             "bank_account": b["bank_account"], "date": b["date"],
                             "amount": b["amount"], "description": sub(b["description"], keymap),
                             "matched_to": keymap.get(b["matched_to"]) if b["matched_to"] else None})
        world = {
            "meta": {**meta, "company": COMPANY, "seed": self.seed, "as_of": AS_OF,
                     "open_periods": OPEN_PERIODS, "periods": PERIODS,
                     "approval_threshold_usd": APPROVAL_THRESHOLD_USD,
                     "role": "senior accountant", "fx_month_end_usd_per_unit": FX},
            "entities": ENTITIES,
            "accounts": [{"number": a, "name": n, "type": t} for a, n, t in ACCOUNTS],
            "entries": out_entries,
            "bank": out_bank,
            "documents": out_docs,
            "checklist": [dict(c) for c in self.checklist],
            "flags": [], "approvals": [], "matches": [], "memo": None,
            "support_attachments": [],
        }
        return world, keymap


def sub(text: str, keymap: dict) -> str:
    """Replace {{key}} placeholders with final IDs."""
    if "{{" not in text:
        return text
    out = text
    for k, v in keymap.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def month_label(date: str) -> str:
    import calendar
    y, m = int(date[:4]), int(date[5:7])
    return f"{calendar.month_name[m]} {y}"


OPENING = {
    "US": {"1000": 2_450_000.00, "1010": 40_000.00, "1100": 212_400.00, "1500": 164_400.00,
           "1510": -41_100.00, "1600": 29_000.00, "2000": -96_300.00, "2100": -38_200.00,
           "3000": -1_000.00, "3100": -2_400_000.00},
    "UK": {"1000": 610_000.00, "1010": 15_000.00, "1100": 58_300.00, "1500": 41_400.00,
           "1510": -13_800.00, "2000": -24_100.00, "3000": -100.00, "3100": -600_000.00},
    "DE": {"1000": 540_000.00, "1010": 12_000.00, "1100": 49_800.00, "1500": 36_000.00,
           "1510": -9_000.00, "2000": -19_700.00, "3000": -25_000.00, "3100": -500_000.00},
}


def opening_cash(entity: str, acct: str) -> float:
    return OPENING[entity].get(acct, 0.0)


# ------------------------------------------------------------------------------------------
# Base world
# ------------------------------------------------------------------------------------------
BASE = {
    "US": {
        "payroll_gross": 92_000.0, "payroll_tax": 0.0765,
        "rent": ("Lumen Office Leasing", 14_500.0),
        "hosting": ("Stackline Cloud", 31_000.0),
        "software": [("Tessellate BI", 1_950.0), ("Quire Docs", 640.0)],
        "marketing": ("Oakridge Creative", 7_800.0),
        "utilities": ("Con Edison", 910.0),
        "customers": [("Acme Logistics", 18_000.0), ("Beacon Health", 8_000.0),
                      ("Corvid Retail", 11_500.0), ("Evergreen Bank", 6_200.0),
                      ("Fairview Labs", 9_400.0)],
        "card": [("Delta Air Lines", "6300", 380, 820, "Airfare"),
                 ("United Airlines", "6300", 310, 760, "Airfare"),
                 ("Hilton Garden Inn", "6300", 190, 460, "Hotel"),
                 ("Uber", "6300", 18, 64, "Ground transport"),
                 ("Sweetgreen", "6310", 32, 95, "Team lunch"),
                 ("Blue Bottle Coffee", "6310", 12, 48, "Coffee meeting"),
                 ("Staples", "6600", 40, 180, "Office supplies"),
                 ("Amazon Business", "6600", 25, 240, "Office supplies"),
                 ("Coursera", "6320", 49, 399, "Training course"),
                 ("Zoom", "6200", 149.9, 149.9, "Video conferencing")],
        "n_card": 12, "fee": 65.00, "depr": 3_425.00,
    },
    "UK": {
        "payroll_gross": 31_000.0, "payroll_tax": 0.138,
        "rent": ("Kingsway Estates", 6_200.0),
        "hosting": ("Albion Hosting", 9_800.0),
        "software": [("Thistle Software", 850.0)],
        "marketing": ("Camden Creative", 2_600.0),
        "utilities": ("Octopus Energy", 410.0),
        "customers": [("Harrow Insurance", 9_500.0), ("Marlowe Media", 6_300.0),
                      ("Pemberton Legal", 4_100.0)],
        "card": [("British Airways", "6300", 140, 520, "Airfare"),
                 ("Trainline", "6300", 38, 160, "Rail tickets"),
                 ("Premier Inn", "6300", 85, 240, "Hotel"),
                 ("Pret A Manger", "6310", 9, 42, "Team lunch"),
                 ("Ryman", "6600", 12, 90, "Office supplies"),
                 ("Addison Lee", "6300", 22, 75, "Taxi")],
        "n_card": 7, "fee": 22.00, "depr": 1_150.00,
    },
    "DE": {
        "payroll_gross": 27_000.0, "payroll_tax": 0.21,
        "rent": ("Spreeblick Immobilien", 5_400.0),
        "hosting": ("Nordwolke Hosting", 8_900.0),
        "software": [("Kiefer Software", 720.0)],
        "marketing": ("Alster Media", 2_100.0),
        "utilities": ("Vattenfall", 380.0),
        "customers": [("Kessler AG", 8_800.0), ("Brandt Maschinenbau", 7_200.0),
                      ("Vogel Logistik", 5_100.0)],
        "card": [("Lufthansa", "6300", 160, 540, "Airfare"),
                 ("Deutsche Bahn", "6300", 45, 190, "Rail tickets"),
                 ("Motel One", "6300", 89, 210, "Hotel"),
                 ("Dallmayr", "6310", 14, 60, "Team lunch"),
                 ("Staples DE", "6600", 15, 95, "Office supplies")],
        "n_card": 6, "fee": 38.50, "depr": 1_000.00,
    },
}


def day(p: str, d: int) -> str:
    return f"{p}-{d:02d}"


def build_base(seed: int = DEFAULT_SEED) -> WorldBuilder:
    w = WorldBuilder(seed)
    rng = w.rng
    w.add_doc("policy", "Accounting Policy Manual - posting authority, support, approvals",
              "2026-01-01", None, POLICY_TEXT, key="policy")
    fx_lines = ["MONTH-END FX RATES (policy rates, USD per 1 unit of currency)",
                "Month      GBP     EUR"]
    for p in PERIODS:
        fx_lines.append(f"{p}   {FX['GBP'][p]:.4f}  {FX['EUR'][p]:.4f}")
    fx_lines.append("Source: Treasury. Use these rates for remeasurement, translation and "
                    "intercompany charges.")
    w.add_doc("fx_rates", "Month-end FX rates Q1 2026 (Treasury policy rates)", "2026-03-31",
              None, "\n".join(fx_lines), key="fx")

    # opening balances
    for ent, bals in OPENING.items():
        lines = []
        for a, v in bals.items():
            lines.append((a, v if v > 0 else 0, -v if v < 0 else 0))
        tot = sum(bals.values())
        lines.append(("3200", 0 if tot > 0 else -tot, tot if tot > 0 else 0))
        # 3200 plug is the opening retained earnings
        lines = [(a, d, c) for a, d, c in lines]
        fix = [(a, d, c) for a, d, c in lines if a != "3200"]
        re_amt = r2(sum(d - c for _, d, c in fix))
        fix.append(("3200", 0, re_amt) if re_amt > 0 else ("3200", -re_amt, 0))
        w.add_entry(ent, "2026-01-01", "Opening balances (migrated from prior system, audited FY2025)",
                    fix, [], "migration", "controller", bank=False, key=f"open-{ent}")

    # intercompany loan US -> UK, USD 200,000 denominated in USD (UK books GBP)
    loan_doc = w.add_doc("contract", "Intercompany loan agreement US-UK", "2026-01-02", None, """
INTERCOMPANY LOAN AGREEMENT
Lender: Halvard Systems Inc. (US)   Borrower: Halvard Systems Ltd (UK)
Principal: USD 200,000.00 (loan is denominated in US dollars)
Drawdown date: 2026-01-02   Maturity: 2028-12-31   Interest: 0% (capital support)
The Borrower records the loan in GBP at the drawdown rate and remeasures it at each month-end
policy rate.
Drawdown recorded by UK at USD/GBP 1.2700 = GBP 157,480.31.
""", key="loan")
    w.add_entry("US", "2026-01-02", "Intercompany loan to UK - drawdown USD 200,000",
                [("1410", 200_000, 0), ("1000", 0, 200_000)], [loan_doc], "treasury", "controller",
                bank_desc="WIRE OUT HALVARD SYSTEMS LTD IC LOAN")
    w.add_entry("UK", "2026-01-02", "Intercompany loan from US - USD 200,000 @1.2700",
                [("1000", 157_480.31, 0), ("2400", 0, 157_480.31)], [loan_doc], "treasury",
                "controller", bank_desc="INWARD PAYMENT HALVARD SYSTEMS INC")

    # prepaid software (US Figtree annual license)
    fig_doc = w.add_doc("vendor_bill", "Figtree Software invoice FIG-20260105 (annual license)",
                        "2026-01-05", "US", """
VENDOR INVOICE
Vendor: Figtree Software
Bill to: Halvard Systems Inc.
Invoice #: FIG-20260105
Invoice date: 2026-01-05
Service period: 2026-01-01 to 2026-12-31 (12 months)
Description: Figtree Platform annual enterprise license
Amount due: USD 15,000.00
Terms: Due on receipt
""", key="figtree")
    w.add_entry("US", "2026-01-05", "Figtree Software - FIG-20260105 - annual license (prepaid)",
                [("1210", 15_000, 0), ("2000", 0, 15_000)], [fig_doc], "ap", "ap.clerk")
    w.add_entry("US", "2026-01-12", "Payment - Figtree Software - FIG-20260105",
                [("2000", 15_000, 0), ("1000", 0, 15_000)], [fig_doc], "ap", "ap.clerk",
                bank_desc="ACH OUT FIGTREE SOFTWARE")
    sched = w.add_doc("schedule", "Prepaid software amortization schedule 2026 (US)", "2026-01-31", "US", """
PREPAID SOFTWARE AMORTIZATION SCHEDULE - Halvard Systems Inc. (GL 1210)
Item: Figtree Platform annual license, invoice FIG-20260105, USD 15,000.00
Term: 2026-01-01 to 2026-12-31, straight-line
Monthly amortization: USD 1,250.00 (Dr 6200 Software Subscriptions / Cr 1210 Prepaid Software)
Jan-2026: booked   Feb-2026: booked   Mar-2026: to be booked at March close
""", key="sched-1210")
    far = w.add_doc("schedule", "Fixed asset register and depreciation schedule Q1 2026 (US)",
                    "2026-01-31", "US", """
FIXED ASSET REGISTER - Halvard Systems Inc.
Class: Computer equipment (GL 1500), straight-line 36 months
Cost at 2026-01-01: USD 164,400.00  Accumulated depreciation: USD 41,100.00
No additions or disposals in Q1 2026 through 2026-03-31.
Monthly depreciation: USD 3,425.00 (Dr 6800 Depreciation / Cr 1510 Accumulated Depreciation)
Jan-2026: booked   Feb-2026: booked   Mar-2026: to be booked at March close
""", key="far-US")

    for ent, cfg in BASE.items():
        cur = ENTITIES[ent]["currency"]
        for pi, p in enumerate(PERIODS):
            # payroll: two runs
            for d in (15, 28 if p == "2026-02" else 30):
                gross = r2(cfg["payroll_gross"] * (1 + rng.uniform(-0.008, 0.008)))
                tax = r2(gross * cfg["payroll_tax"])
                tot = r2(gross + tax)
                date = day(p, d)
                reg = w.add_doc("payroll_register", f"Payroll register {ent} {date}", date, ent, f"""
PAYROLL REGISTER - {ENTITIES[ent]['name']}
Pay date: {date}   Currency: {cur}
Gross wages: {gross:,.2f}
Employer payroll taxes: {tax:,.2f}
Total funded from payroll account: {tot:,.2f}
Approved by: Controller
""")
                w.add_entry(ent, date, f"Payroll funding transfer {date}",
                            [("1010", tot, 0), ("1000", 0, tot)], [reg], "treasury", "controller",
                            bank_desc="TRANSFER TO PAYROLL ACCOUNT", key=f"fund-{ent}-{date}")
                w.add_entry(ent, date, f"Payroll {date}",
                            [("6000", gross, 0), ("6010", tax, 0), ("1010", 0, tot)], [reg],
                            "payroll", "payroll.system", bank_desc="PAYROLL PROVIDER NET PAY + TAX",
                            key=f"pay-{ent}-{date}")
            # rent, hosting, software, marketing, utilities
            vendor, amt = cfg["rent"]
            w.vendor_bill(ent, vendor, day(p, 1), amt, "6100", "Office rent", day(p, 5),
                          key=f"rent-{ent}-{p}")
            vendor, amt = cfg["hosting"]
            w.vendor_bill(ent, vendor, day(p, 3), r2(amt * (1 + rng.uniform(-0.02, 0.02))), "5000",
                          "Cloud infrastructure - production", day(p, 22), key=f"host-{ent}-{p}")
            for vendor, amt in cfg["software"]:
                w.vendor_bill(ent, vendor, day(p, rng.randint(2, 8)), amt, "6200",
                              "Monthly subscription", day(p, rng.randint(15, 24)))
            vendor, amt = cfg["marketing"]
            w.vendor_bill(ent, vendor, day(p, rng.randint(4, 9)), r2(amt * (1 + rng.uniform(-0.02, 0.02))),
                          "6400", "Content and campaign services", day(p, rng.randint(20, 26)))
            vendor, amt = cfg["utilities"]
            w.vendor_bill(ent, vendor, day(p, rng.randint(6, 10)), r2(amt * (1 + rng.uniform(-0.1, 0.1))),
                          "6110", "Office electricity", day(p, rng.randint(20, 26)))
            # customers
            for cust, amt in cfg["customers"]:
                recv = day(p, rng.randint(17, 27))
                w.customer_invoice(ent, cust, day(p, 1), amt, "4000",
                                   f"Subscription - {month_label(p + '-01')}", recv)
            # card spend
            for _ in range(cfg["n_card"]):
                m, acct, lo, hi, desc = rng.choice(cfg["card"])
                amt = r2(rng.uniform(lo, hi))
                w.card_expense(ent, day(p, rng.randint(2, 27)), m, amt, acct, desc)
            # month-end recurring (Jan, Feb only: March close not yet done)
            if p != "2026-03":
                stmt = f"stmt-{ent}-1000-{p}"
                w.add_entry(ent, MONTH_END[p], f"Bank service charges {p}",
                            [("6900", cfg["fee"], 0), ("1000", 0, cfg["fee"])], [stmt], "manual",
                            "senior.accountant", bank_desc="MONTHLY SERVICE CHARGE")
                w.add_entry(ent, MONTH_END[p], f"Depreciation {p}",
                            [("6800", cfg["depr"], 0), ("1510", 0, cfg["depr"])],
                            [far] if ent == "US" else [], "manual", "senior.accountant", bank=False)
                if ent == "US":
                    w.add_entry(ent, MONTH_END[p], f"Amortize Figtree prepaid license {p}",
                                [("6200", 1250, 0), ("1210", 0, 1250)], [sched], "manual",
                                "senior.accountant", bank=False)
            else:
                # March bank fee appears on the bank statement but is not yet booked
                w.add_bank(ent, "1000", MONTH_END[p], -cfg["fee"], "MONTHLY SERVICE CHARGE", None)
        # professional services / usage (US only), Jan-Mar
        if ent == "US":
            for p in PERIODS:
                w.customer_invoice("US", "Fairview Labs", day(p, 10), 7_500.0, "4200",
                                   f"Implementation services - {month_label(p + '-01')}",
                                   day(p, 26) if p != "2026-03" else None)
            for p in ("2026-01", "2026-02"):
                w.customer_invoice("US", "Acme Logistics", day(p, 3), [612.0, 844.0][PERIODS.index(p)],
                                   "4100", f"API usage overage - {month_label(p + '-01')}",
                                   day(p, 24))
    # non-US depreciation docs
    for ent in ("UK", "DE"):
        w.add_doc("schedule", f"Fixed asset register and depreciation schedule Q1 2026 ({ent})",
                  "2026-01-31", ent, f"""
FIXED ASSET REGISTER - {ENTITIES[ent]['name']}
Monthly depreciation: {ENTITIES[ent]['currency']} {BASE[ent]['depr']:,.2f}
Jan-2026: booked   Feb-2026: booked   Mar-2026: to be booked at March close
""")
    # attach UK/DE depreciation support
    for e in w.entries:
        if e["memo"].startswith("Depreciation") and not e["support"]:
            ent = e["entity"]
            dk = next(d["key"] for d in w.docs if d["title"].endswith(f"({ent})") and d["type"] == "schedule")
            e["support"] = [dk]

    # close checklist
    for ent in ENTITIES:
        for item, assignee in [("Bank reconciliations", "senior accountant"),
                               ("Record depreciation", "senior accountant"),
                               ("Amortize prepaid software", "senior accountant"),
                               ("Accrue unpaid payroll", "senior accountant"),
                               ("AP cutoff review", "senior accountant"),
                               ("Revenue recognition", "revenue accountant"),
                               ("Intercompany reconciliation", "senior accountant"),
                               ("Flux review", "controller")]:
            w.checklist.append({"entity": ent, "item": item, "assignee": assignee,
                                "status": "open", "period": "2026-03"})
    return w


def world_stats(world: dict) -> dict:
    return {"entries": len(world["entries"]), "documents": len(world["documents"]),
            "bank_lines": len(world["bank"]), "accounts": len(world["accounts"])}


def deepcopy(x):
    return copy.deepcopy(x)
