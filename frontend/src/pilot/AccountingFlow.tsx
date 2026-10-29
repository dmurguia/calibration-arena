import { FileSpreadsheet, FileText, Sparkles } from 'lucide-react'
import { CalibratedMark } from '../components/brand/CalibratedMark'
import type { FinanceWorkflow } from './financeWorkflows'

/** An illustration of the comparison process, not a sample result. */
export function AccountingFlow({ workflow }: { workflow?: FinanceWorkflow }) {
  const documents = workflow?.assets.map(asset => asset.label) ?? ['Trial balance', 'Invoices & receipts']
  return <section className="p-accounting-flow" aria-labelledby="accounting-flow-title">
    <p className="p-flow-eyebrow">How it works</p>
    <h2 id="accounting-flow-title">Compare AI responses using your own files.</h2>
    <p className="p-flow-intro">Upload a statement, ledger, or invoice. Ask a question and review two responses side by side.</p>
    <div className="p-flow-visual" aria-hidden="true">
      <div className="p-flow-documents">
        {documents.map((name, index) => <div className="p-flow-document" key={name}>
          <span className={`p-flow-file-icon p-flow-file-${index}`}>{index === 0 ? <FileSpreadsheet size={21} /> : <FileText size={21} />}</span>
          <span><strong>{name}</strong><span className="p-flow-document-lines"><i /><i /></span></span>
        </div>)}
      </div>
      <div className="p-flow-engine"><span className="p-flow-path p-flow-path-in" /><span className="p-flow-orbit" /><span className="p-flow-core"><CalibratedMark size={30} /></span><Sparkles className="p-flow-spark" size={15} /><span className="p-flow-path p-flow-path-out" /></div>
      <div className="p-flow-responses">
        {['A', 'B'].map(letter => <div className={`p-flow-response p-flow-response-${letter.toLowerCase()}`} key={letter}><span className="p-flow-response-letter">{letter}</span><div><strong>Response {letter}</strong><span className="p-flow-answer-lines"><i /><i /><i /></span></div></div>)}
      </div>
    </div>
    <div className="p-flow-captions"><span>Upload files + ask a question</span><span>Compare responses side by side</span></div>
    <p className="p-flow-finish">Choose the response you prefer. Reveal the models behind it.</p>
  </section>
}
