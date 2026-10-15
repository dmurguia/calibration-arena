import { Building2, ChartNoAxesCombined, FilePenLine, Landmark, ListChecks, ReceiptText, type LucideIcon } from 'lucide-react'

export interface FinanceWorkflow {
  id: string
  label: string
  icon: LucideIcon
  /** Accent for the icon tile; muted so the six read as a set with distinct associations. */
  tone: 'gold' | 'sage' | 'slate' | 'clay' | 'teal' | 'plum'
  prompt: string
  assets: { role: string; label: string; hint: string }[]
}

export const financeWorkflows: FinanceWorkflow[] = [
  {
    id: 'bank-reconciliation', label: 'Bank reconciliation', icon: Landmark, tone: 'gold',
    prompt: 'Reconcile the uploaded bank statement against the cash ledger for the same period. Show matched transactions, outstanding items, bank fees and unexplained differences. Propose any adjusting entries with supporting calculations, and identify missing facts before making assumptions.',
    assets: [
      { role: 'bank-statement', label: 'Bank statement', hint: 'Transactions and opening / closing balances for the period.' },
      { role: 'cash-ledger', label: 'Cash ledger', hint: 'Cash account transactions or journal entries for the same period.' },
    ],
  },
  {
    id: 'close-management', label: 'Close management', icon: ListChecks, tone: 'sage',
    prompt: 'Review the uploaded general ledger and close checklist. Identify unusual journal entries, unreconciled balances, missing support and close blockers. Prioritize the items to resolve, explain the evidence for each, and propose follow-up checks. Do not mark tasks complete without evidence.',
    assets: [
      { role: 'general-ledger', label: 'General ledger', hint: 'Account balances and journal entries for the close period.' },
      { role: 'close-checklist', label: 'Close checklist', hint: 'Tasks, owners, due dates and current status.' },
    ],
  },
  {
    id: 'consolidation', label: 'Entity & account consolidation', icon: Building2, tone: 'slate',
    prompt: 'Review the uploaded entity trial balances and consolidation mapping. Prepare a proposed consolidated view, show intercompany eliminations separately, and flag unmapped accounts or differences. State the reporting currency and ownership assumptions. Ask for missing FX rates or ownership details rather than inventing them.',
    assets: [
      { role: 'entity-trial-balances', label: 'Entity trial balances', hint: 'Balances identified by entity, account, period and currency.' },
      { role: 'consolidation-mapping', label: 'Consolidation mapping', hint: 'Group account mappings, entity ownership and intercompany balances.' },
    ],
  },
  {
    id: 'accounts-receivable', label: 'Accounts receivable', icon: ReceiptText, tone: 'clay',
    prompt: 'Review the uploaded open invoices and customer payments. Identify unapplied receipts, overdue invoices, disputes and collection priorities. Explain how each payment is matched and flag ambiguous matches. Draft follow-up actions for review without sending reminders or changing customer balances.',
    assets: [
      { role: 'open-invoices', label: 'Open invoices', hint: 'Invoice IDs, customers, amounts, due dates and balances.' },
      { role: 'customer-payments', label: 'Customer payments', hint: 'Receipts with dates, amounts and customer / invoice references.' },
    ],
  },
  {
    id: 'ar-reporting', label: 'AR reporting', icon: ChartNoAxesCombined, tone: 'teal',
    prompt: 'Prepare an accounts receivable aging summary from the uploaded AR ledger. Use the supplied reporting date, show current, 1–30, 31–60, 61–90 and over-90-day balances, and highlight overdue concentration by customer. Reconcile totals to the source. Only calculate trends or DSO when the necessary history or sales data is supplied.',
    assets: [
      { role: 'ar-ledger', label: 'AR ledger or aging export', hint: 'Invoice dates, due dates, open balances and the reporting date.' },
    ],
  },
  {
    id: 'invoicing', label: 'Invoicing', icon: FilePenLine, tone: 'plum',
    prompt: 'Prepare a draft invoice from the uploaded billing terms and billable items. Show the customer, invoice period, line items, quantities, rates, applicable tax and payment terms. Reconcile the total to the source and flag missing or conflicting terms. Do not invent tax treatment or issue the invoice.',
    assets: [
      { role: 'billing-terms', label: 'Contract or billing terms', hint: 'Customer, pricing, payment terms and any supplied tax instructions.' },
      { role: 'billable-items', label: 'Billable items', hint: 'Approved services, usage, quantities or milestones for the invoice period.' },
    ],
  },
]

export const financeAssetAccept = '.csv,.xlsx,.pdf,.txt'
export const financeAssetMaxBytes = 2 * 1024 * 1024

export function encodeAsset(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error(`Could not read ${file.name}. Choose the file again.`))
    reader.onload = () => resolve(String(reader.result).split(',')[1])
    reader.readAsDataURL(file)
  })
}
