"""Editable prompt starters. These have no answer key and are not validated cases."""
STARTERS = [
    {'id': 'duplicate-accrual', 'version': '1', 'title': 'An accrual recorded twice',
     'brief': 'Fictional US GAAP manufacturer, August close: $86,400 of steel received August 29 is already recorded as inventory with a credit to received-not-invoiced. AP also posted an $86,400 debit to inventory and credit to accrued liabilities because the invoice had not arrived. The September 3 invoice is $87,100 and all the steel is still on hand. Explain what needs correcting, how to handle the invoice, and what evidence to check before posting.'},
    {'id': 'late-invoice', 'version': '1', 'title': 'An invoice after close',
     'brief': 'Fictional US GAAP company: a $18,600 maintenance invoice dated January 8 relates to work completed and accepted December 22. Nothing was accrued at December 31. The work restored existing equipment to normal condition without extending its life or increasing capacity. Explain the December close treatment, the supporting evidence needed, and the later payment entry.'},
    {'id': 'payment-mismatch', 'version': '1', 'title': 'A payment that does not match',
     'brief': 'Fictional company: a bank payment of $12,480 has a reference matching an open supplier invoice for $12,000. The accounts-payable ledger shows no other open items for this supplier. The remittance advice is missing. A draft reconciliation books the $480 difference to bank fees. Review that proposal and explain what to investigate and what can safely be concluded from these facts.'},
]
