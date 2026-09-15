import { createContext, FormEvent, ReactNode, useContext, useEffect, useRef, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, Copy, ChevronLeft, BookOpen, ArrowUp, Plus, FileText, PanelLeft, X, Info, Download } from 'lucide-react'
import { DialMark } from '../components/brand/DialMark'
import { CalibrationLens } from '../components/brand/CalibrationLens'
import { Resolve } from '../components/brand/Resolve'
import { call, Case, CaseAssignment, Config, Draft, Me, Run, saveToken, token } from './api'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './pilot.css'

const Context = createContext<{ me: Me | null; config: Config | null; cases: Case[]; refresh: () => Promise<void> }>({ me: null, config: null, cases: [], refresh: async () => {} })
const usePilot = () => useContext(Context)
const errorText = (e: unknown) => e instanceof Error ? e.message : 'Something went wrong. Please try again.'
const date = (s: string) => new Date(s).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
const labels: Record<string, string> = { a: 'Draft A', b: 'Draft B', tie: 'Equivalent', neither: 'Neither', unsure: 'Insufficient evidence', ready: 'Ready to approve', revise: 'Needs revision' }

function Eyebrow({ children }: { children: ReactNode }) { return <p className="p-eyebrow">{children}</p> }
function ErrorNote({ message }: { message: string }) { return message ? <p className="p-error" role="alert">{message}</p> : null }
export default function Pilot() {
  const [me, setMe] = useState<Me | null>(null)
  const [config, setConfig] = useState<Config | null>(null)
  const [cases, setCases] = useState<Case[]>([])
  const [error, setError] = useState('')
  const [ready, setReady] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()
  const refresh = async () => { if (token()) setMe(await call<Me>('/me')) }
  useEffect(() => { Promise.all([call<Config>('/config').then(setConfig), call<Case[]>('/cases').then(setCases), refresh()]).catch(e => setError(errorText(e))).finally(() => setReady(true)) }, [])
  useEffect(() => { if (me) call('/events', { name: 'visit' }).catch(() => {}) }, [me?.participant.id])
  useEffect(() => { window.scrollTo(0, 0); setMenuOpen(false) }, [location.pathname])
  return <Context.Provider value={{ me, config, cases, refresh }}><div className="pilot">
    <a className="p-skip" href="#main">Skip to content</a>
    <div className="p-mobile-header"><Link className="p-brand" to="/"><DialMark size={26} /><span>Calibrated</span></Link><button aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen} aria-controls="pilot-sidebar" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={20} /> : <PanelLeft size={20} />}</button></div>
    {menuOpen && <button className="p-sidebar-backdrop" aria-label="Close navigation overlay" onClick={() => setMenuOpen(false)} />}
    <aside id="pilot-sidebar" className={`p-sidebar ${menuOpen ? 'is-open' : ''}`}>
      <Link className="p-brand" to="/"><DialMark size={28} /><span>Calibrated</span></Link>
      <div className="p-area"><span>WORKSPACE</span><strong><BookOpen size={15} />Accounting</strong></div>
      <nav aria-label="Main navigation">
        <NavLink to="/" end onClick={() => setMenuOpen(false)}><Plus size={16} />New comparison</NavLink>
        <NavLink to="/cases"><FileText size={16} />Close examples</NavLink>
        <NavLink to="/record"><BookOpen size={16} />Notebook</NavLink>
      </nav>
      {!!me?.runs.length && <div className="p-sidebar-recent"><p>RECENT</p>{me.runs.slice(0, 5).map(r => <Link key={r.id} to={`/session/${r.id}`}>{r.kind === 'ask' ? r.brief.slice(0, 45) : r.title}</Link>)}</div>}
      <div className="p-sidebar-bottom"><NavLink to="/method"><Info size={15} />How it works</NavLink><span>Built by Corsac</span></div>
    </aside>
    <div className="p-main-column">
    <main id="main"><ErrorNote message={error} />{!ready ? <p className="p-loading" role="status">Opening the practice room…</p> : <Routes>
      <Route path="/" element={<Home key={location.key} />} /><Route path="/cases" element={<CaseLibrary />} /><Route path="/ask" element={<Ask />} /><Route path="/case/:caseId" element={<CaseStart />} />
      <Route path="/session/:runId" element={<Session />} /><Route path="/record" element={<Notebook />} /><Route path="/method" element={<Method />} />
      <Route path="/founder" element={<Founder />} /><Route path="*" element={<NotFound />} />
    </Routes>}</main>
    <footer className="p-footer"><span>Calibrated · Built by Corsac</span><span>Professional judgment, in practice.</span><Link to="/method#data-use">Data use <ArrowUpRight size={13} /></Link></footer>
  </div></div></Context.Provider>
}

function Home() {
  return <div className="p-arena-page"><CalibrationLens radius={76} intensity={0.10} /><div className="p-arena-content"><Ask embedded /></div></div>
}

async function beginGuest(invite: string, refresh: () => Promise<void>) {
  if (!token()) {
    const response = await call<{ token: string }>('/guests', { invite_code: invite, source: new URLSearchParams(location.search).get('source')?.slice(0, 100) || 'direct' })
    saveToken(response.token)
  }
  await refresh()
}

function InviteField({ invite, setInvite }: { invite: string; setInvite: (v: string) => void }) {
  const { config, me } = usePilot()
  return config?.invite_required && !me ? <label className="p-invite-field">Invitation code<input value={invite} onChange={e => setInvite(e.target.value)} required autoComplete="off" /></label> : null
}

function CaseLibrary() {
  const { cases, me, refresh } = usePilot(); const navigate = useNavigate()
  const [assignments, setAssignments] = useState<CaseAssignment[]>([]); const [loading, setLoading] = useState(true)
  const [error, setError] = useState(''); const [busy, setBusy] = useState(''); const [invite, setInvite] = useState('')
  useEffect(() => {
    let cancelled = false
    if (!me) { setLoading(false); return }
    setLoading(true)
    call<CaseAssignment[]>('/assignments', {}).then(a => { if (!cancelled) setAssignments(a) }).catch(e => { if (!cancelled) setError(errorText(e)) }).finally(() => { if (!cancelled) setLoading(false) })
    call('/events', { name: 'close_examples_opened' }).catch(() => {})
    return () => { cancelled = true }
  }, [me?.participant.id])
  const open = async (a: CaseAssignment) => {
    setBusy(a.id); setError('')
    try { const run = await call<Run>(`/assignments/${a.id}/start`, {}); await refresh(); navigate(`/session/${run.id}`) } catch (e) { setError(errorText(e)) } finally { setBusy('') }
  }
  const row = (a: CaseAssignment, i: number) => <button className="p-case-row p-assigned-row" onClick={() => open(a)} disabled={!!busy} key={a.id}><span className="p-case-number">{String(i + 1).padStart(2, '0')}</span><div><span className="p-meta">{a.framework}</span><h3>{a.title}</h3></div><span className="p-case-time">{busy === a.id ? 'Opening…' : a.status === 'completed' ? 'Reviewed' : a.run_id ? 'Resume' : 'Compare'}</span><ArrowUpRight size={20} /></button>
  const first = assignments.slice(0, 3)
  return <div className="p-workspace"><Eyebrow>Accounting</Eyebrow><h1>Close examples</h1><p className="p-lead">Compare the same responses to a few month-end questions. Progress stays in this notebook; return to your own questions whenever you like.</p>
    {!me && <form onSubmit={async e => { e.preventDefault(); setBusy('enroll'); setError(''); try { await beginGuest(invite, refresh) } catch (e) { setError(errorText(e)) } finally { setBusy('') } }}><InviteField invite={invite} setInvite={setInvite} /><button className="p-button" disabled={!!busy}>{busy ? 'Opening…' : 'Open examples'} <ArrowRight size={16} /></button></form>}
    {me && loading && <p role="status">Loading saved progress…</p>}
    {me && !loading && !assignments.length && <p className="p-empty-cases">No shared comparisons have been added yet. <Link to="/">Ask a question</Link> or explore a practice example below.</p>}
    {!!first.length && <><p className="p-case-progress" role="status">{first.filter(a => a.status === 'completed').length} of {first.length} reviewed</p><div className="p-case-list">{first.map(row)}</div>{assignments.length > 3 && <details className="p-more-cases"><summary>More close examples ({assignments.length - 3})</summary><div className="p-case-list">{assignments.slice(3).map((a, i) => row(a, i + 3))}</div></details>}</>}
    <ErrorNote message={error} /><p><Link className="p-text-link" to="/">Ask a new question <Plus size={14} /></Link></p>
    <details className="p-practice-library"><summary>Practice examples</summary><p className="p-fine">Fixed, authored drafts with a policy-based explanation. These are separate from shared model comparisons.</p><div className="p-case-list">{cases.map((c, i) => <Link className="p-case-row" to={`/case/${c.id}`} key={c.id}><span className="p-case-number">{String(i + 1).padStart(2, '0')}</span><div><span className="p-meta">{c.topic}</span><h3>{c.title}</h3></div><span className="p-case-time">{me?.runs.some(r => r.case_id === c.id && r.status === 'completed') ? 'Reviewed' : 'Compare'}</span><ArrowUpRight size={20} /></Link>)}</div></details></div>
}

function Profile({ onReady }: { onReady: () => void }) {
  const { config, refresh, me } = usePilot()
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [followup, setFollowup] = useState(false)
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setBusy(true); setError('')
    const f = new FormData(e.currentTarget)
    try {
      const result = await call<{ token?: string }>(me ? '/profile' : '/participants', { name: f.get('name'), role: f.get('role'), experience: f.get('experience'), framework: f.get('framework'), email: followup ? f.get('email') : null, followup, research_consent: f.get('research') === 'on', source: new URLSearchParams(location.search).get('source')?.slice(0, 100) || 'direct', invite_code: f.get('invite') || '' })
      if (result.token) saveToken(result.token); await refresh(); onReady()
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <form className="p-card p-profile" onSubmit={submit}><Eyebrow>Your reviewer context · about 30 seconds</Eyebrow><h2>A little context for your judgment.</h2><p>Different accounting backgrounds bring different perspectives. Your background is self-reported.</p>
    <label>What should we call you?<input autoComplete="given-name" name="name" required maxLength={60} placeholder="First name or a nickname" /></label>
    <div className="p-form-grid"><label>Your work<select name="role" required defaultValue=""><option value="" disabled>Select your role</option>{['Public accountant', 'Industry accountant', 'Bookkeeper', 'Controller / finance leader', 'Other accounting professional'].map(x => <option key={x}>{x}</option>)}</select></label>
      <label>Accounting experience<select name="experience" required defaultValue=""><option value="" disabled>Select experience</option>{['0–2 years', '3–7 years', '8–15 years', '16+ years'].map(x => <option key={x}>{x}</option>)}</select></label></div>
    <label>Framework you usually work with<select name="framework" required defaultValue=""><option value="" disabled>Select a framework</option>{['US GAAP', 'IFRS', 'Local GAAP / other', 'Multiple / not applicable'].map(x => <option key={x}>{x}</option>)}</select></label>
    {config?.invite_required && !me && <label>Invitation code<input name="invite" required autoComplete="off" /></label>}
    <label className="p-checkbox"><input type="checkbox" checked={followup} onChange={e => setFollowup(e.target.checked)} />I’m open to a short follow-up conversation. (Optional)</label>
    {followup && <label>Email for follow-up<input name="email" type="email" required maxLength={254} autoComplete="email" /></label>}
    <label className="p-checkbox"><input name="research" type="checkbox" />Allow my submissions to be used in private research. Optional; this does not grant publication or model-training permission.</label>
    <p className="p-fine">Progress is saved for this browser. Use your own device. No password or verified account is created. Contact the person who invited you to withdraw or delete your data.</p>
    <ErrorNote message={error} /><button className="p-button" disabled={busy}>{busy ? 'Saving your profile…' : 'Save my background'} <ArrowRight size={16} /></button>
  </form>
}

function CaseStart() {
  const { caseId } = useParams(); const { cases, me, refresh } = usePilot(); const navigate = useNavigate()
  const c = cases.find(c => c.id === caseId); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const [invite, setInvite] = useState('')
  const start = async (e: FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { if (!me) await beginGuest(invite, refresh); const run = await call<Run>('/runs', { case_id: caseId, independent_first: false }); navigate(`/session/${run.id}`) } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }
  if (!c) return <NotFound />
  return <div className="p-narrow"><Link className="p-back" to="/"><ChevronLeft size={15} /> Arena</Link><Eyebrow>{c.topic} · {c.minutes} minutes</Eyebrow><h1>{c.title}</h1><p className="p-lead">Compare two responses, choose a preference, and see the explanation.</p><div className="p-brief"><Eyebrow>Case facts · synthetic company</Eyebrow><p>{c.brief}</p></div>
    <form onSubmit={start}><InviteField invite={invite} setInvite={setInvite} /><ErrorNote message={error} /><button className="p-button" disabled={busy}>{busy ? 'Opening case…' : 'Compare responses'} <ArrowRight size={16} /></button></form>
    <p className="p-fine">Authored sample case. Your work is saved for this browser. <Link to="/method">How it works</Link>.</p>
  </div>
}

function Ask({ embedded = false }: { embedded?: boolean }) {
  const { config, me, refresh } = usePilot(); const navigate = useNavigate()
  const [question, setQuestion] = useState(''); const [invite, setInvite] = useState('')
  const [starterId, setStarterId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError('')
    if (config?.ask_mode !== 'live') { setError('Live models are not connected yet. Your prompt stays here until they are available.'); return }
    setBusy(true)
    try {
      if (!me) await beginGuest(invite, refresh)
      const run = await call<Run>('/runs', { question, task_type: 'accounting-question', source_example_id: starterId })
      await refresh(); navigate(`/session/${run.id}`)
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <div className={embedded ? 'p-prompt-first' : 'p-narrow p-prompt-first'}>
    <Eyebrow>Accounting</Eyebrow><Resolve as="h1">What are you working on?</Resolve><p className="p-prompt-sub">Compare two answers to an accounting question.</p>
    <form className="p-composer" onSubmit={submit}>
      <label htmlFor="open-prompt" className="sr-only">Accounting prompt</label>
      <textarea id="open-prompt" required minLength={15} maxLength={5000} rows={4} value={question} onChange={e => setQuestion(e.target.value)} placeholder="Describe the question, paste a draft, or ask about a close issue…" />
      <div className="p-composer-bottom"><span>{config?.ask_mode === 'live' ? 'Two models · blind comparison' : 'Live models not connected'}</span><button className="p-send" aria-label="Compare answers" disabled={busy}><ArrowUp size={19} /></button></div>
      <InviteField invite={invite} setInvite={setInvite} /><ErrorNote message={error} />{busy && <p className="p-composer-status" role="status">Preparing both responses…</p>}
    </form>
    <div className="p-type-samples"><span>Try a question</span>{config?.prompt_starters?.map(c => <button key={c.id} type="button" onClick={() => { setQuestion(c.brief); setStarterId(c.id); setError(''); document.getElementById('open-prompt')?.focus() }}>{c.title}<ArrowUpRight size={12} /></button>)}</div>
    {starterId && <p className="p-sample-note">Edit the facts as needed. Both models will answer the prompt above.</p>}
  </div>
}

interface Report { id: string; position: string; category: string | null; note: string; after_reveal: boolean }
const issueTypes: [string, string][] = [['clarity', 'Clarity / presentation'], ['calculation', 'Calculation'], ['timing', 'Timing'], ['account-treatment', 'Account treatment'], ['policy', 'Policy / framework'], ['missing-facts', 'Missing facts'], ['unsupported-claim', 'Unsupported claim'], ['other', 'Other']]

function DraftPanel({ draft, reveal, authored }: { draft: Draft; reveal: boolean; authored: boolean }) {
  return <article className="p-draft">
    <header><strong>Response {draft.position.toUpperCase()}</strong><span className="p-meta">{reveal ? draft.author : 'Anonymous'}</span></header>
    <div className={`p-answer ${authored ? 'p-authored' : ''}`}>{authored ? draft.text : <Markdown remarkPlugins={[remarkGfm]} skipHtml components={{ img: () => null, a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer noopener">{children}</a>, table: ({ children }) => <div className="p-table-scroll"><table>{children}</table></div> }}>{draft.text}</Markdown>}</div>
    {reveal && !!draft.checks?.length && <details className="p-check-details"><summary>Case checks</summary>{draft.checks.map(check => <p key={check.label}>{check.passed ? '✓' : '↳'} {check.label}: {check.passed ? 'pass' : 'needs correction'}</p>)}<p>{draft.review_note}</p></details>}
  </article>
}

function ImprovementForm({ run, position }: { run: Run; position: string }) {
  const [inputs, setInputs] = useState<Record<string, { note: string; category: string }>>({}); const [reports, setReports] = useState<Report[]>([])
  const { note = '', category = '' } = inputs[position] || {}
  const setNote = (note: string) => setInputs(values => ({ ...values, [position]: { note, category } }))
  const setCategory = (category: string) => setInputs(values => ({ ...values, [position]: { note, category } }))
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [saved, setSaved] = useState(false)
  useEffect(() => { setSaved(false); setError('') }, [position])
  useEffect(() => { call<Report[]>(`/runs/${run.id}/issues`).then(setReports).catch(e => setError(errorText(e))) }, [run.id])
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError(''); setSaved(false)
    try { setReports(await call<Report[]>(`/runs/${run.id}/improvements`, { position, note, category: category || null })); setInputs(values => ({ ...values, [position]: { note: '', category: '' } })); setSaved(true) } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <section className="p-improvement"><form onSubmit={submit}>
    <label htmlFor="improvement-note">What should improve?</label><span className="p-feedback-target">{position === 'both' ? 'Feedback on this pair' : `Feedback on Response ${position.toUpperCase()}`}</span>
    <textarea id="improvement-note" rows={2} value={note} onChange={e => { setNote(e.target.value); setSaved(false) }} required maxLength={3000} placeholder="What would you change about the result?" />
    <div className="p-improvement-actions"><label className="sr-only" htmlFor="improvement-type">Issue type (optional)</label><select id="improvement-type" value={category} onChange={e => setCategory(e.target.value)}><option value="">Issue type (optional)</option>{issueTypes.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select><button className="p-secondary" disabled={busy || !note.trim()}>{busy ? 'Saving…' : 'Save feedback'}</button></div>
    <ErrorNote message={error} />{saved && <p className="p-fine" role="status">Feedback saved.</p>}
  </form>{!!reports.length && <details className="p-own"><summary>Saved feedback ({reports.length})</summary>{reports.map(r => <p key={r.id}><strong>{r.position === 'both' ? 'Pair' : `Response ${r.position.toUpperCase()}`}{r.category ? ` · ${issueTypes.find(t => t[0] === r.category)?.[1] || r.category}` : ''}</strong><br />{r.note || 'Issue type reported without a note.'}</p>)}</details>}
  </section>
}

function ResultReveal({ run, position, onSelect }: { run: Run; position: string; onSelect: (p: string) => void }) {
  const [message, setMessage] = useState('')
  const preferred = ['a', 'b'].includes(run.judgment!.preference) ? run.judgment!.preference : null
  const ordered = [...run.drafts].sort((a, b) => Number(b.position === preferred) - Number(a.position === preferred))
  const active = run.drafts.find(d => d.position === position) || ordered[0]
  const copy = async () => { try { await navigator.clipboard.writeText(active.text); call('/events', { name: 'response_copied', run_id: run.id, position: active.position }).catch(() => {}); setMessage('Response copied.') } catch { setMessage('Copy is unavailable. Download the response instead.') } }
  const download = () => {
    const content = `# ${run.title}\n\nAuthor: ${active.author || 'Unknown'}\nSource: ${run.mode}\nResponse: ${active.position.toUpperCase()}\nCreated: ${run.created_at}${run.history?.length ? '\n\n## Earlier conversation\n\n' + run.history.map(m => '### ' + (m.role === 'user' ? 'Prompt' : 'Selected response') + '\n\n' + m.content).join('\n\n') : ''}\n\n## Prompt\n\n${run.brief}\n\n## Response\n\n${active.text}\n`
    const url = URL.createObjectURL(new Blob([content], { type: 'text/markdown;charset=utf-8' })); const link = document.createElement('a')
    link.href = url; link.download = `calibrated-${run.id.slice(0, 8)}-${active.position}.md`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); setMessage('Markdown download started.'); call('/events', { name: 'response_downloaded', run_id: run.id, position: active.position }).catch(() => {})
  }
  return <section className="p-result"><div className="p-result-intro"><DialMark size={27} /><div><p>{preferred ? 'The response you preferred came from' : run.judgment!.preference === 'tie' ? 'A close call. Here are the authors.' : 'Here are the authors behind the responses.'}</p>{preferred && <h1>{run.drafts.find(d => d.position === preferred)?.author}</h1>}{run.mode === 'authored-fixture' && <span className="p-fine">Sample responses are authored examples.</span>}</div></div>
    <div className="p-result-tabs" role="tablist" aria-label="Revealed responses">{ordered.map(d => <button key={d.position} id={`result-tab-${d.position}`} role="tab" aria-selected={active.position === d.position} aria-controls="result-panel" tabIndex={active.position === d.position ? 0 : -1} onKeyDown={e => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) { e.preventDefault(); const next = e.key === 'Home' ? ordered[0] : e.key === 'End' ? ordered[ordered.length - 1] : ordered.find(x => x.position !== active.position)!; onSelect(next.position); setMessage(''); document.getElementById(`result-tab-${next.position}`)?.focus() } }} onClick={() => { onSelect(d.position); setMessage('') }}><span className="p-result-position">{d.position.toUpperCase()}</span><span>{d.author}</span>{d.position === preferred && <span className="p-preferred-label">Preferred</span>}</button>)}</div>
    <div className="p-result-toolbar"><span>Response {active.position.toUpperCase()}</span><div><button onClick={copy}><Copy size={14} />Copy response</button><button onClick={download}><Download size={14} />Download .md</button></div></div>
    <div id="result-panel" role="tabpanel" aria-labelledby={`result-tab-${active.position}`}><DraftPanel draft={active} reveal authored={run.mode === 'authored-fixture'} /></div>
    {message && <p className="p-export-message" role="status">{message}</p>}
  </section>
}

function RevisionComposer({ run, position }: { run: Run; position: string }) {
  const { config, refresh } = usePilot(); const navigate = useNavigate()
  const [question, setQuestion] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const active = run.drafts.find(d => d.position === position)
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError('')
    if (config?.ask_mode !== 'live') { setError('Live models are not connected. Your follow-up stays here until a connection is available.'); return }
    setBusy(true)
    try {
      const next = await call<Run>('/runs', { question, task_type: 'accounting-question', source_run_id: run.id, source_position: position, continuation_mode: 'followup' })
      await refresh(); navigate(`/session/${next.id}`)
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <section className="p-refine"><div className="p-refine-heading"><span className="p-fine">Continue from Response {position.toUpperCase()} · {active?.author}</span><Link to="/">New question <Plus size={14} /></Link></div>
    <form className="p-composer" onSubmit={submit}><label htmlFor="revision-prompt" className="sr-only">Follow-up prompt</label>
      <textarea id="revision-prompt" value={question} onChange={e => setQuestion(e.target.value)} rows={3} minLength={1} maxLength={5000} placeholder="Ask a follow-up or describe what to change…" required />
      <div className="p-composer-bottom"><span>Both models receive this conversation and the selected response</span><button className="p-send" disabled={busy} aria-label="Send follow-up"><ArrowUp size={18} /></button></div>
      <ErrorNote message={error} />{busy && <p role="status" className="p-composer-status">Preparing both responses…</p>}
    </form>
  </section>
}

function Session() {
  const { runId } = useParams(); const { refresh, me } = usePilot(); const [run, setRun] = useState<Run | null>(null)
  const [position, setPosition] = useState('a'); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [conclusion, setConclusion] = useState(''); const [copied, setCopied] = useState(false)
  useEffect(() => { setRun(null); setConclusion(''); setError(''); setCopied(false); call<Run>(`/runs/${runId}`).then(r => { setRun(r); setPosition(r.judgment?.preference === 'b' ? 'b' : 'a') }).catch(e => setError(errorText(e))) }, [runId])
  const latestRun = useRef<Run | null>(null); latestRun.current = run
  useEffect(() => () => { const r = latestRun.current; if (r && !['completed', 'failed'].includes(r.status)) call('/events', { name: 'left_session', run_id: r.id }).catch(() => {}) }, [runId])
  const save = async (path: string, data: unknown) => { setBusy(true); setError(''); try { const result = await call<Run>(`/runs/${runId}/${path}`, data); setRun(result); if (path === 'preference') { setPosition(result.judgment?.preference === 'b' ? 'b' : 'a'); requestAnimationFrame(() => document.querySelector('.p-result')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' })) }; await refresh() } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }
  if (!run) return <div className="p-narrow"><ErrorNote message={error} />{!error && <p role="status">Opening comparison…</p>}</div>
  const voted = run.status === 'completed'; const showing = voted || run.status === 'review'
  const share = async () => { try { await navigator.clipboard.writeText(`${location.origin}/case/${run.case_id}?source=peer-share`); setCopied(true); call('/events', { name: 'share_intent', run_id: run.id }).catch(() => {}) } catch { setError('Could not copy the link. Open the sample case and copy its address.') } }
  return <div className="p-workspace p-comparison">
    <div className="p-session-top"><span>Accounting · {run.title}</span><Link to="/record">Notebook <ArrowUpRight size={13} /></Link></div>
    {!!run.history?.length && <details className="p-thread-history"><summary>Earlier messages ({run.history.length})</summary>{run.history.map((m, i) => m.role === 'user' ? <section className="p-question" key={i}><Eyebrow>Prompt</Eyebrow><p>{m.content}</p></section> : <div className="p-history-answer" key={i}><Eyebrow>Selected response</Eyebrow><Markdown remarkPlugins={[remarkGfm]} skipHtml components={{ img: () => null }}>{m.content}</Markdown></div>)}</details>}
    <section className="p-question"><Eyebrow>{run.kind === 'ask' ? 'Prompt' : run.mode === 'authored-fixture' ? 'Practice · authored responses' : 'Close example'}</Eyebrow><p>{run.brief}</p>{run.source_run_id && <Link className="p-text-link" to={`/session/${run.source_run_id}`}>Previous comparison <ArrowUpRight size={12} /></Link>}</section>
    {run.status === 'conclusion' && <div className="p-independent"><h2>Compare the responses.</h2><button className="p-button" disabled={busy} onClick={() => save('skip-conclusion', {})}>Show responses <ArrowRight size={16} /></button>
      <details className="p-own"><summary>Make an independent note first (optional)</summary><form onSubmit={e => { e.preventDefault(); save('conclusion', { conclusion }) }}><label htmlFor="independent-note">Initial conclusion</label><textarea id="independent-note" value={conclusion} onChange={e => setConclusion(e.target.value)} minLength={10} maxLength={3000} required rows={3} /><button className="p-secondary" disabled={busy}>Save note and show responses</button></form></details></div>}
    {showing && <>
      {voted ? <ResultReveal run={run} position={position} onSelect={setPosition} /> : <><div className="p-pair-heading"><DialMark size={25} /><h1>Which response would you prefer to use?</h1></div>
      <div className="p-drafts">{run.drafts.map(d => <DraftPanel key={`${run.id}-${d.position}`} draft={d} reveal={false} authored={run.mode === 'authored-fixture'} />)}</div></>}
      {!voted && <div className="p-vote-area"><div className="p-vote-bar" role="group" aria-label="Choose a preferred response"><button disabled={busy} onClick={() => save('preference', { preference: 'a' })}>Prefer A</button><DialMark size={24} /><button disabled={busy} onClick={() => save('preference', { preference: 'b' })}>Prefer B</button></div><div className="p-vote-alternatives"><button disabled={busy} onClick={() => save('preference', { preference: 'tie' })}>About the same</button><span>·</span><button disabled={busy} onClick={() => save('preference', { preference: 'neither' })}>Neither</button></div>{busy && <span role="status" className="p-fine">Saving preference…</span>}</div>}
      <ErrorNote message={error} />
      {voted && run.expected && <details className="p-case-explanation"><summary>Read the case explanation</summary><p>{run.expected}</p><p className="p-fine">{run.mode === 'authored-fixture' ? 'Based on the stated policy. This practice sample has not been independently validated.' : 'Applies to this case version and its stated requirements.'}</p></details>}
      {run.conclusion && <details className="p-own"><summary>Initial note</summary><p>{run.conclusion}</p></details>}
      {voted && (run.judgment?.rationale || run.judgment?.correction) && <details className="p-own"><summary>Saved review notes</summary><p>{run.judgment.rationale}</p><p>{run.judgment.correction}</p></details>}
      <ImprovementForm key={`feedback-${run.id}`} run={run} position={voted ? position : 'both'} />
      {voted && <RevisionComposer key={`composer-${run.id}`} run={run} position={position} />}
      {voted && <div className="p-after-links"><Link to="/cases">Close examples <ArrowRight size={14} /></Link>{run.mode === 'authored-fixture' && run.case_id && <button onClick={share}><Copy size={14} />{copied ? 'Case link copied' : 'Share this case'}</button>}</div>}
      {voted && me?.participant.identity === 'guest' && <details className="p-own"><summary>Add accounting background (optional)</summary><Profile onReady={() => {}} /></details>}
    </>}
    {!showing && <ErrorNote message={error} />}
    {(run.status === 'failed' || run.status === 'generating') && <div className="p-independent"><h2>{run.status === 'failed' ? 'The responses couldn’t be prepared.' : 'This request did not finish in this view.'}</h2><p>The prompt is saved. Edit it below and try again.</p><RetryComposer run={run} /></div>}
  </div>
}

function RetryComposer({ run }: { run: Run }) {
  const navigate = useNavigate(); const [question, setQuestion] = useState(run.brief); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  return <form className="p-composer" onSubmit={async e => { e.preventDefault(); setBusy(true); setError(''); try { const next = await call<Run>('/runs', { question, task_type: run.task_type || 'accounting-question', ...(run.status === 'failed' ? { retry_of_run_id: run.id } : {}) }); navigate(`/session/${next.id}`) } catch(e) { setError(errorText(e)) } finally { setBusy(false) } }}><label htmlFor="retry-prompt">Prompt</label><textarea id="retry-prompt" value={question} onChange={e => setQuestion(e.target.value)} minLength={run.history?.length ? 1 : 15} maxLength={5000} required /><div className="p-composer-bottom"><span>{busy ? 'Preparing both responses…' : 'Fresh comparison'}</span><button className="p-send" disabled={busy} aria-label="Retry comparison"><ArrowUp size={18} /></button></div><ErrorNote message={error} /></form>
}

function Notebook() {
  const { me } = usePilot()
  return <div className="p-narrow"><Eyebrow>Your notebook · this browser</Eyebrow><h1>{me ? `${me.participant.name}’s review desk.` : 'A place for your judgment.'}</h1><p className="p-lead">Return to a case, revisit your reasoning, or pick up where you left off.</p>
    {!me ? <div className="p-card"><p>Your first question or case starts your notebook. No password or background form needed.</p><Link className="p-button" to="/case/insurance-cutoff">Start a case <ArrowRight size={16} /></Link></div> : <>
      <div className="p-notebook-meta"><span>{me.runs.filter(r => r.status === 'completed').length} completed reviews</span><span>{me.participant.role} · {me.participant.experience}</span><span>{me.participant.identity === 'guest' ? 'Guest · background not yet supplied' : 'Self-reported background'}</span></div>
      {!me.runs.length && <p>No reviews yet. <Link to="/">Choose your first case.</Link></p>}
      {me.runs.map(r => <Link key={r.id} className="p-notebook-row" to={`/session/${r.id}`}><span><span className="p-meta">{r.kind === 'ask' ? 'Question' : r.mode === 'authored-fixture' ? 'Practice example' : 'Close example'} · {date(r.created_at)} · {r.mode === 'local-cli' ? 'Local CLI responses' : r.mode === 'authored-fixture' ? 'Authored fixtures' : r.mode === 'frozen-model-pair' ? 'Frozen model responses' : 'Live model responses'}</span><h3>{r.title}</h3>{r.kind === 'ask' && <p>{r.brief.slice(0, 130)}</p>}</span><span>{r.status === 'completed' ? 'See reveal' : r.status === 'failed' ? 'Request failed' : 'Continue'} <ArrowUpRight size={15} /></span></Link>)}
      <p className="p-fine">Saved on Calibrated and linked to this browser. Clearing browser storage or changing devices starts a new identity; this is not a verified account. Contact the Calibrated team to withdraw or have your data removed.</p>
    </>}
  </div>
}

function Method() {
  const { config } = usePilot()
  return <div className="p-narrow p-method"><Eyebrow>Calibrated · Accounting</Eyebrow><h1>How comparisons work</h1><p className="p-lead">Bring a question, compare two drafts, and decide what you would use.</p>
    <h2>One workspace, two sources of drafts</h2><p>Ask an accounting question in your own words. The editable question suggestions request fresh answers from both models. Close examples use a fixed, approved case and saved model responses so everyone compares the same work. The separate practice library contains authored drafts with a policy-based explanation. Open prompts are never replaced with sample answers.</p><h2>What you do</h2><p>Read the two anonymous responses and choose a preference. One vote reveals the authors and opens the preferred response. Copy it or download a Markdown file with the prompt and author. One feedback box captures improvements, with an optional issue type. Samples use the same simple comparison. Older sessions also let you save an independent note before opening the responses. After voting, ask a follow-up about the selected response. Both models receive the same conversation and selected answer. Follow-ups are recorded separately from first comparisons. New question starts without that history. Earlier sessions labeled prompt revisions sent only the edited prompt.</p>
    <h2>What the checks can tell you</h2><p>Sample cases use explicit policies and frozen, authored drafts. Structured checks compare debit/credit balance and the accounts, dates and amounts in the supplied case. They do not establish overall accounting competence. The explanation applies to the supplied facts and policy; you can flag missing facts or suggest a correction.</p>
    <h2>What your judgment tells us</h2><p>Preference tells us which answer people want to use. Optional issue reports identify possible calculation, timing, treatment, policy, evidence or missing-fact problems. Reports are observations, not verified correctness scores. A preferred response can still be wrong. Independent case validation and assessment of actual outputs are separate work.</p>
    <h2 id="data-use">What is saved—and what stays private</h2><p>The Calibrated team can inspect your self-reported background, submitted questions, conclusions, judgments, notes, optional contact details and interaction timestamps. Your notebook and service activity are stored to provide the service. Optional permission for private research is recorded separately in your profile; submitting a prompt does not mark that permission as granted. Publication and model-training use are not granted. To withdraw or request deletion, contact the person who invited you.</p><p>{config?.inference_backend === 'local-cli' ? 'Questions are sent through the locally installed Codex and Claude Code applications using the host’s signed-in accounts. Responses run on their providers, not on this computer. The applications use different model harnesses and account data settings; OpenRouter routing settings do not apply.' : config?.inference_backend === 'direct' ? 'Questions and selected conversation context are sent directly to OpenAI and Anthropic. Provider retention follows the configured API accounts; API access alone does not guarantee zero retention.' : 'Questions are sent to two configured models through OpenRouter with zero-data-retention routing requested.'} Your question and answers are saved in your private notebook. Never submit confidential client or employer information.</p>
    <h2>Your notebook</h2><p>Your comparisons and judgments are saved for this browser. Use the same browser to return to your work; cross-device sign-in is not available.</p>
    <Link className="p-button" to="/cases">Close examples <ArrowRight size={16} /></Link>
  </div>
}

function NotFound() { return <div className="p-narrow"><h1>Page not found.</h1><p>The practice room has the current cases and your notebook has your saved work.</p><Link className="p-button" to="/">Go to practice</Link></div> }

interface ExportData { schema_version: string; participants: (Me['participant'] & { created_at: string; source: string; dataset?: string; research_consent?: boolean })[]; runs: (Run & { participant_id: string })[]; events: { participant_id: string; run_id?: string; name: string; at: string; data?: { position?: string; category?: string; note?: string; after_reveal?: boolean } }[] }
function Founder() {
  const [key, setKey] = useState(''); const [data, setData] = useState<ExportData | null>(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const load = async (e: FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { setData(await call<ExportData>('/founder/export', undefined, { 'X-Pilot-Admin': key })); setKey('') } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }
  const download = () => { const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `calibrated-private-pilot-${new Date().toISOString().slice(0, 10)}.json`; a.click(); URL.revokeObjectURL(url) }
  return <div className="p-workspace"><Eyebrow>Private · review records</Eyebrow><h1>Comparisons and judgments.</h1><p className="p-lead">Inspect real participation and raw judgments. Authored drafts remain fixtures, even when reviewed by real people.</p>
    <form className="p-card" onSubmit={load}><label>Private founder token<input type="password" value={key} onChange={e => setKey(e.target.value)} required autoComplete="off" /></label><p className="p-fine">Uses PILOT_ADMIN_TOKEN from the server. The token is never persisted in this browser.</p><ErrorNote message={error} /><button className="p-button" disabled={busy}>{busy ? 'Loading…' : 'Open private records'}</button></form>
    {data && <><div className="p-actions"><button className="p-secondary" onClick={download}>Export private raw JSON</button><span className="p-fine">Contains contact details and questions. Do not publish.</span></div>
      <div className="p-founder-summary"><span>{data.participants.length} browser profiles</span><span>{data.runs.filter(r => r.status === 'completed').length} completed judgments</span><span>{data.runs.filter(r => r.status !== 'completed').length} incomplete / failed</span></div>
      {data.participants.map(p => { const runs = data.runs.filter(r => r.participant_id === p.id); const days = new Set(data.events.filter(e => e.participant_id === p.id && ['visit', 'session_started', 'judgment_completed'].includes(e.name)).map(e => e.at.slice(0, 10))); return <section className="p-card" key={p.id}><h2>{p.name}</h2><p>{p.role} · {p.experience} · {p.framework} · source: {p.source} · dataset: {p.dataset || 'preview'}</p><p className="p-fine">{runs.filter(r => r.status === 'completed').length} completed · {days.size} UTC activity days · {p.followup ? `Follow-up permitted: ${p.email}` : 'No follow-up permission'} · Research reuse: {p.research_consent ? 'opted in' : 'not opted in'}</p>
        {runs.map(r => <details className="p-own" key={r.id}><summary>{r.title} · {r.status} · {r.mode} · {date(r.created_at)}</summary><p>{r.brief}</p><p>Independent conclusion: {r.conclusion || 'Not submitted / Ask'}</p>{r.judgment && <><p>Preference: {labels[r.judgment.preference]} · A: {(r.judgment.a ? labels[r.judgment.a] : 'Not collected')} · B: {(r.judgment.b ? labels[r.judgment.b] : 'Not collected')} · Confidence: {r.judgment.confidence || 'Not collected'} · {Math.round((r.judgment.decision_ms ?? 0) / 1000)} seconds</p><p>Reasons: {r.judgment.reasons.join(', ')}</p><p>Explanation: {r.judgment.rationale || 'None'}</p><p>Correction: {r.judgment.correction || 'None'}</p></>}{data.events.filter(e => e.run_id === r.id && e.name === 'issue_reported').map((e, i) => <p key={i}>Reported issue · {e.data?.position?.toUpperCase()} · {e.data?.category} · {e.data?.note || 'No note'} · {e.data?.after_reveal ? 'After reveal' : 'Before reveal'} · unverified</p>)}<p>Usefulness: {r.feedback?.usefulness || 'Not submitted'} · {r.feedback?.note}</p><p className="p-fine">Events: {data.events.filter(e => e.run_id === r.id).map(e => `${e.name} (${new Date(e.at).toLocaleTimeString()})`).join(' → ')}</p></details>)}
      </section> })}</>}
  </div>
}
