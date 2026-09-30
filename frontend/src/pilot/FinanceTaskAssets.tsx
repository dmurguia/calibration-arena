import { Check, Upload, X } from 'lucide-react'
import { financeAssetAccept, type FinanceWorkflow } from './financeWorkflows'

export function FinanceTaskAssets({ workflow, files, onFile, onClear }: {
  workflow: FinanceWorkflow
  files: Record<string, File>
  onFile: (role: string, file: File | null) => void
  onClear: () => void
}) {
  return <section className="p-task-assets" aria-label={`${workflow.label} source files`}>
    <div className="p-task-assets-heading"><strong>{workflow.label}</strong><button type="button" onClick={onClear}>Clear task <X size={13} /></button></div>
    <p>Add the source files, then tweak the question above.</p>
    <div className="p-task-asset-grid">
      {workflow.assets.map(asset => <div className="p-task-asset" key={asset.role}>
        <label className="p-asset-label" htmlFor={`asset-${asset.role}`}>{asset.label} <span>Required</span></label>
        <p id={`asset-hint-${asset.role}`}>{asset.hint}</p>
        <input className="sr-only" id={`asset-${asset.role}`} type="file" accept={financeAssetAccept} aria-describedby={`asset-hint-${asset.role}`} onChange={event => { onFile(asset.role, event.currentTarget.files?.[0] ?? null); event.currentTarget.value = '' }} />
        {files[asset.role] ? <div className="p-attached-file"><Check size={15} /><span title={files[asset.role].name}>{files[asset.role].name}</span><button type="button" aria-label={`Remove ${asset.label}`} onClick={() => onFile(asset.role, null)}><X size={15} /></button></div>
          : <label className="p-asset-upload" htmlFor={`asset-${asset.role}`}><Upload size={15} />Upload file</label>}
      </div>)}
    </div>
    <p className="p-asset-formats">CSV, XLSX, text-based PDF or TXT · Up to 2 MB per file</p>
    <p className="p-asset-disclosure">When you compare, extracted file text is saved with your question and sent to both models.</p>
  </section>
}
