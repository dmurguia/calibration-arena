import { useRef } from 'react'
import { FileText, Paperclip, X } from 'lucide-react'
import { financeAssetAccept } from './financeWorkflows'

export function QuestionAttachments({ files, onAdd, onRemove }: {
  files: File[]
  onAdd: (files: File[]) => void
  onRemove: (index: number) => void
}) {
  const input = useRef<HTMLInputElement>(null)
  return <div className="p-question-attachments">
    <div className="p-question-upload-row">
      <input ref={input} className="sr-only" type="file" multiple accept={financeAssetAccept} aria-label="Attach accounting files" tabIndex={-1} onChange={event => { onAdd(Array.from(event.currentTarget.files ?? [])); event.currentTarget.value = '' }} />
      <button type="button" className="p-question-upload" disabled={files.length >= 2} onClick={() => input.current?.click()}><Paperclip size={15} aria-hidden="true" />Attach files</button>
      <span>CSV, XLSX, PDF, TXT · Up to 2 files, 2 MB each</span>
    </div>
    {!!files.length && <>
      <ul className="p-question-file-list" aria-label="Attached files">{files.map((file, index) => <li key={`${file.name}-${file.lastModified}-${index}`}>
        <FileText size={16} aria-hidden="true" /><span title={file.name}>{file.name}</span>
        <button type="button" aria-label={`Remove ${file.name}`} onClick={() => onRemove(index)}><X size={15} /></button>
      </li>)}</ul>
      <p className="p-question-file-note">When you compare, extracted file text is saved with your question and sent to both models. PDFs must contain selectable text.</p>
    </>}
  </div>
}
