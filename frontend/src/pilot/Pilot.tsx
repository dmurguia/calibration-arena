import { createContext, FormEvent, ReactNode, useContext, useEffect, useRef, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, Copy, ChevronLeft, BookOpen, CheckCircle2, ArrowUp, Plus, FileText, PanelLeft, X, Info } from 'lucide-react'
import { DialMark } from '../components/brand/DialMark'
import { CalibrationLens } from '../components/brand/CalibrationLens'
import { Resolve } from '../components/brand/Resolve'
import { call, Case, Config, Draft, Judgment, Me, Run, saveToken, token } from './api'
import './pilot.css'

const Context = createContext<{ me: Me | null; config: Config | null; cases: Case[]; refresh: () => Promise<void> }>({ me: null, config: null, cases: [], refresh: async () => {} })
const usePilot = () => useContext(Context)
const errorText = (e: unknown) => e instanceof Error ? e.message : 'Something went wrong. Please try again.'
const date = (s: string) => new Date(s).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
const labels: Record<string, string> = { a: 'Draft A', b: 'Draft B', tie: 'Equivalent', neither: 'Neither is ready', unsure: 'Insufficient evidence', ready: 'Ready to approve', revise: 'Needs revision' }

function Eyebrow({ children }: { children: ReactNode }) { return <p className="p-eyebrow">{children}</p> }
function ErrorNote({ message }: { message: string }) { return message ? <p className="p-error" role="alert">{message}</p> : null }
function Choices({ label, value, options, onChange }: { label: string; value: string; options: [string, string][]; onChange: (s: string) => void }) {
  return <fieldset className="p-field"><legend>{label}</legend><div className="p-choices">{options.map(([key, text]) => <button type="button" key={key} aria-pressed={value === key} className={value === key ? 'selected' : ''} onClick={() => onChange(key)}>{text}</button>)}</div></fieldset>
}

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
        <NavLink to="/cases"><FileText size={16} />Sample cases</NavLink>
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
  const { cases, me } = usePilot()
  return <div className="p-workspace"><Eyebrow>Accounting · sample cases</Eyebrow><h1>Start with a shared example.</h1><p className="p-lead">These cases come with fixed drafts and a stated policy. Everyone reviews the same material. Your own prompts request fresh responses from two models.</p>
    <div className="p-case-list">{cases.map((c, i) => <Link className="p-case-row" to={`/case/${c.id}`} key={c.id}><span className="p-case-number">0{i + 1}</span><div><span className="p-meta">{c.topic}</span><h3>{c.title}</h3></div><span className="p-case-time">{me?.runs.some(r => r.case_id === c.id && r.status === 'completed') ? 'Reviewed' : '3 min'}</span><ArrowUpRight size={20} /></Link>)}</div>
    <p className="p-fine">Authored sample drafts, with explanations based on each case’s stated policy.</p></div>
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
  const start = async (e: FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { if (!me) await beginGuest(invite, refresh); const run = await call<Run>('/runs', { case_id: caseId }); navigate(`/session/${run.id}`) } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }
  if (!c) return <NotFound />
  return <div className="p-narrow"><Link className="p-back" to="/"><ChevronLeft size={15} /> Arena</Link><Eyebrow>{c.topic} · {c.minutes} minutes</Eyebrow><h1>{c.title}</h1><p className="p-lead">Make your own call, compare two drafts, then see the explanation.</p><div className="p-brief"><Eyebrow>Case facts · synthetic company</Eyebrow><p>{c.brief}</p></div>
    <form onSubmit={start}><InviteField invite={invite} setInvite={setInvite} /><ErrorNote message={error} /><button className="p-button" disabled={busy}>{busy ? 'Opening case…' : 'Make your call'} <ArrowRight size={16} /></button></form>
    <p className="p-fine">Authored sample case. Your work is saved for this browser. <Link to="/method">How it works</Link>.</p>
  </div>
}

function Ask({ embedded = false }: { embedded?: boolean }) {
  const { config, me, refresh, cases } = usePilot(); const navigate = useNavigate()
  const [question, setQuestion] = useState(''); const [invite, setInvite] = useState('')
  const [taskType, setTaskType] = useState('journal-entry'); const [sampleId, setSampleId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const task = config?.task_types.find(t => t.id === taskType)
  const samples = cases.filter(c => c.task_type === taskType)
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError('')
    if (!sampleId && config?.ask_mode !== 'live') { setError('Live models are not connected yet. Choose a sample below to try the review flow. Your prompt stays here.'); return }
    setBusy(true)
    try {
      if (!me) await beginGuest(invite, refresh)
      const run = await call<Run>('/runs', sampleId ? { case_id: sampleId, question, task_type: taskType } : { question, task_type: taskType })
      navigate(`/session/${run.id}`)
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <div className={embedded ? 'p-prompt-first' : 'p-narrow p-prompt-first'}>
    <Eyebrow>Accounting</Eyebrow><Resolve as="h1">What are you working on?</Resolve><p className="p-prompt-sub">Two drafts. Your judgment.</p>
    <div className="p-work-types" role="group" aria-label="Type of accounting work">{config?.task_types.map(t => <button key={t.id} type="button" aria-pressed={t.id === taskType} onClick={() => { setTaskType(t.id); setSampleId(null); setError('') }}><FileText size={14} />{t.label}</button>)}</div>
    <form className="p-composer" onSubmit={submit}>
      <label htmlFor="open-prompt" className="sr-only">Your accounting prompt</label>
      <textarea id="open-prompt" required minLength={15} maxLength={5000} rows={4} value={question} onChange={e => { setQuestion(e.target.value); setSampleId(null); setError('') }} placeholder={task?.placeholder || 'Describe the accounting work…'} />
      <div className="p-composer-bottom"><span>{sampleId ? 'Sample case · fixed authored drafts' : config?.ask_mode === 'live' ? 'Two models · blind comparison' : 'Live models not connected'}</span><button className="p-send" aria-label={sampleId ? 'Review this sample' : 'Compare answers'} disabled={busy}><ArrowUp size={19} /></button></div>
      <InviteField invite={invite} setInvite={setInvite} /><ErrorNote message={error} />{busy && <p className="p-composer-status" role="status">{sampleId ? 'Opening the sample…' : 'Preparing both drafts…'}</p>}
    </form>
    <div className="p-type-samples"><span>Try a sample</span>{samples.map(c => <button key={c.id} type="button" onClick={() => { setQuestion(c.brief); setSampleId(c.id); setError('') }}>{c.title}<ArrowUpRight size={12} /></button>)}{!samples.length && <span className="p-meta">No fixed samples for this type yet. Enter your own prompt for a live comparison.</span>}</div>
    {sampleId && <p className="p-sample-note">This sample has a fixed brief and drafts. Editing it switches to a fresh model comparison.</p>}
  </div>
}

function DraftPanel({ draft, approval, onChange, reveal }: { draft: Draft; approval: string; onChange?: (v: string) => void; reveal?: boolean }) {
  return <article className="p-draft"><header><span>Draft {draft.position.toUpperCase()}</span><span className="p-meta">{reveal ? draft.author : 'Author hidden'}</span></header><div className="p-draft-text">{draft.text}</div>
    {onChange && <div className="p-draft-review"><Choices label={`Would you approve draft ${draft.position.toUpperCase()} as written?`} value={approval} options={[["ready", "Ready"], ["revise", "Needs revision"], ["unsure", "Can’t tell"]]} onChange={onChange} /></div>}
    {reveal && <div className="p-draft-review"><span className="p-meta">Your review: {labels[approval]}</span>{draft.checks?.map(check => <p className={`p-check ${check.passed ? 'pass' : 'fail'}`} key={check.label}>{check.passed ? '✓' : '↳'} {check.label}: {check.passed ? 'pass' : 'needs correction'}</p>)}<p>{draft.review_note}</p></div>}
  </article>
}

function Session() {
  const { runId } = useParams(); const { refresh } = usePilot(); const [run, setRun] = useState<Run | null>(null)
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [conclusion, setConclusion] = useState('')
  const [judgment, setJudgment] = useState<Judgment>({ a: '', b: '', preference: '', reasons: [], confidence: '', rationale: '', correction: '' })
  useEffect(() => { setRun(null); setConclusion(''); setJudgment({ a: '', b: '', preference: '', reasons: [], confidence: '', rationale: '', correction: '' }); setError(''); call<Run>(`/runs/${runId}`).then(setRun).catch(e => setError(errorText(e))) }, [runId])
  const latestRun = useRef<Run | null>(null)
  latestRun.current = run
  useEffect(() => () => { const r = latestRun.current; if (r && !['completed', 'failed'].includes(r.status)) call('/events', { name: 'left_session', run_id: r.id }).catch(() => {}) }, [runId])
  const save = async (path: string, data: unknown) => { setBusy(true); setError(''); try { setRun(await call<Run>(`/runs/${runId}/${path}`, data)); await refresh() } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }
  const set = (key: keyof Judgment, value: string | string[]) => setJudgment(j => ({ ...j, [key]: value }))
  const valid = judgment.a && judgment.b && judgment.preference && judgment.reasons.length && judgment.confidence && (!judgment.reasons.includes('Other') || judgment.rationale.trim().length >= 5)
  if (!run) return <div className="p-narrow"><ErrorNote message={error} />{!error && <p role="status">Opening your saved case…</p>}</div>
  if (run.status === 'completed') return <Reveal run={run} save={save} busy={busy} error={error} />
  return <div className="p-workspace"><Link className="p-back" to="/record"><ChevronLeft size={15} /> Your notebook</Link>
    <div className="p-stepper"><span className={run.status === 'conclusion' ? 'current' : ''}>01 {run.kind === 'ask' ? 'Your question' : 'Your call'}</span><span className={run.status === 'review' ? 'current' : ''}>02 Review</span><span>03 Reveal</span></div>
    <Eyebrow>{run.kind === 'ask' ? 'Your question · exploratory' : 'Sample case · authored drafts'}</Eyebrow><h1>{run.title}</h1>
    <div className="p-brief"><Eyebrow>{run.kind === 'ask' ? 'Your question' : 'The facts and policy'}</Eyebrow><p>{run.brief}</p></div>
    {run.status === 'conclusion' && <form className="p-card p-conclusion" onSubmit={e => { e.preventDefault(); save('conclusion', { conclusion }) }}><h2>Before you see the drafts,<br />what would you do?</h2><p>A sentence or a rough entry is enough. If the facts are insufficient, tell us what you would need. Your first read is saved before the reveal.</p><label>Your independent conclusion<textarea value={conclusion} onChange={e => setConclusion(e.target.value)} minLength={10} maxLength={3000} required rows={4} placeholder="I would recognize… because…" /></label><ErrorNote message={error} /><button className="p-button" disabled={busy}>{busy ? 'Saving…' : 'Save my call and see drafts'} <ArrowRight size={16} /></button></form>}
    {run.status === 'review' && <>
      {run.conclusion && <details className="p-own"><summary>Your independent conclusion</summary><p>{run.conclusion}</p></details>}
      {run.mode === 'ask-fixture' && <p className="p-notice">Walkthrough drafts only. These were not generated in response to your question.</p>}
      <p className="p-review-intro">Review each draft on its own merits. Then choose the more useful starting point—even if it still needs work.</p>
      <div className="p-drafts">{run.drafts.map(d => <DraftPanel key={d.position} draft={d} approval={judgment[d.position as 'a' | 'b']} onChange={v => set(d.position as 'a' | 'b', v)} />)}</div>
      <form className="p-card p-judgment" onSubmit={e => { e.preventDefault(); save('judgment', judgment) }}>
        <Eyebrow>Your judgment</Eyebrow><h2>Which would you build on?</h2><Choices label="Your preference" value={judgment.preference} options={[["a", "Draft A"], ["b", "Draft B"], ["tie", "Equivalent"], ["neither", "Neither is ready"], ["unsure", "Insufficient evidence"]]} onChange={v => set('preference', v)} />
        <fieldset className="p-field"><legend>What drove your call? Choose at least one.</legend><div className="p-choices">{['Amounts', 'Timing', 'Account treatment', 'Policy', 'Evidence', 'Clarity', 'Missing facts', 'Other'].map(r => <button type="button" key={r} aria-pressed={judgment.reasons.includes(r)} className={judgment.reasons.includes(r) ? 'selected' : ''} onClick={() => set('reasons', judgment.reasons.includes(r) ? judgment.reasons.filter(x => x !== r) : [...judgment.reasons, r])}>{r}</button>)}</div></fieldset>
        <Choices label="How confident are you in this judgment?" value={judgment.confidence} options={[["low", "Still uncertain"], ["medium", "Fairly confident"], ["high", "Very confident"]]} onChange={v => set('confidence', v)} />
        <label>What should the author understand? {judgment.reasons.includes('Other') ? '(Required for Other)' : '(Optional)'}<textarea rows={2} maxLength={3000} value={judgment.rationale} onChange={e => set('rationale', e.target.value)} placeholder="The specific detail that changed my decision was…" /></label>
        <details className="p-own"><summary>Add a correction or challenge the case itself</summary><label>Your correction (optional)<textarea rows={3} maxLength={5000} value={judgment.correction} onChange={e => set('correction', e.target.value)} placeholder="I would change this entry or assumption to…" /></label></details>
        <ErrorNote message={error} /><div className="p-actions"><button className="p-button" disabled={busy || !valid}>{busy ? 'Saving your judgment…' : 'Save judgment & reveal'} <ArrowRight size={16} /></button><span className="p-fine">Review both drafts, choose a preference,<br />a reason and your confidence to continue.</span></div>
      </form></>}
    {(run.status === 'failed' || run.status === 'generating') && <div className="p-card"><h2>{run.status === 'failed' ? 'We couldn’t prepare both responses.' : 'This request did not finish in this view.'}</h2><p>Your question has been saved in your notebook. Try a fresh request later, or practice with a supplied case.</p><Link className="p-button" to="/ask">Return to Ask</Link></div>}
  </div>
}

function Reveal({ run, save, busy, error }: { run: Run; save: (path: string, data: unknown) => void; busy: boolean; error: string }) {
  const { cases, me } = usePilot(); const [shared, setShared] = useState(''); const [usefulness, setUseful] = useState(run.feedback?.usefulness ?? ''); const [note, setNote] = useState(run.feedback?.note ?? '')
  const next = cases.find(c => !me?.runs.some(r => r.case_id === c.id && r.status === 'completed'))
  const share = async () => { try { await navigator.clipboard.writeText(`${location.origin}/case/${run.case_id}?source=peer-share`); setShared('Case link copied. Your judgment stays private.'); call('/events', { name: 'share_intent', run_id: run.id }).catch(() => {}) } catch { setShared('Copy the case URL from the link below.') } }
  return <div className="p-workspace"><div className="p-reveal-banner"><Eyebrow><CheckCircle2 size={15} /> Judgment saved</Eyebrow><h1>{run.takeaway || 'Your question. Two perspectives. Your call.'}</h1><p>You chose <strong>{labels[run.judgment!.preference]}</strong>. {['openrouter', 'local-cli'].includes(run.mode) ? 'Model identities are now visible. Preference is not proof of correctness.' : 'These are authored practice drafts, not measured model outputs.'}</p></div>
    {run.expected && <div className="p-explanation"><BookOpen size={22} /><div><Eyebrow>The case explanation</Eyebrow><p>{run.expected}</p><span className="p-fine">Checks compare structured postings with this case’s stated policy. They do not certify the whole answer.</span></div></div>}
    {run.conclusion && <details className="p-own"><summary>Revisit your independent conclusion</summary><p>{run.conclusion}</p></details>}
    <div className="p-drafts">{run.drafts.map(d => <DraftPanel key={d.position} draft={d} approval={run.judgment![d.position as 'a' | 'b']} reveal />)}</div>
    <div className="p-card p-saved"><Eyebrow>What your review contributed</Eyebrow><h2>A decision with a reason behind it.</h2><p>Your approval calls, <strong>{run.judgment!.reasons.join(', ').toLowerCase()}</strong> reasons and {run.judgment!.confidence} confidence are saved together. Your notes stay with the drafts so you can revisit your reasoning.</p>{run.judgment?.rationale && <blockquote>{run.judgment.rationale}</blockquote>}{run.judgment?.correction && <p><strong>Your correction:</strong> {run.judgment.correction}</p>}<p className="p-fine">Saved in your notebook. Research permission is managed separately in your profile.</p></div>
    <form className="p-card" onSubmit={e => { e.preventDefault(); save('feedback', { usefulness, note }) }}><Choices label="Was this worth your time?" value={usefulness} options={[["useful", "Yes, useful"], ["somewhat", "Somewhat"], ["not-useful", "Not yet"]]} onChange={setUseful} /><label>What would make you come back? (Optional)<input value={note} onChange={e => setNote(e.target.value)} maxLength={1000} /></label><ErrorNote message={error} /><button className="p-secondary" disabled={!usefulness || busy}>{run.feedback ? 'Update feedback' : 'Save feedback'}</button>{run.feedback && <span className="p-feedback-saved" role="status">Feedback saved. Thank you.</span>}</form>
    {me?.participant.identity === 'guest' && <details className="p-context-invite"><summary>Add your accounting background to put this review in context <span>Optional · 30 seconds</span></summary><Profile onReady={() => {}} /></details>}
    <div className="p-next"><div><Eyebrow>Keep the useful part</Eyebrow><h2>{next ? 'Another case, or your own question?' : 'You’ve explored all five cases.'}</h2><div className="p-actions">{next && <Link className="p-button" to={`/case/${next.id}`}>Try another case <ArrowRight size={16} /></Link>}<Link className="p-secondary" to="/ask">Ask your own question</Link><Link className="p-text-link" to="/record">Your notebook</Link></div></div>
      {run.case_id && <div className="p-share"><button className="p-text-link" onClick={share}><Copy size={15} /> Send a colleague the case</button><p className="p-fine" role="status">{shared || 'Just the case. No personal result or client question.'}</p>{shared.startsWith('Copy the') && <Link to={`/case/${run.case_id}?source=peer-share`}>Open shareable case</Link>}</div>}</div>
  </div>
}

function Notebook() {
  const { me } = usePilot()
  return <div className="p-narrow"><Eyebrow>Your notebook · this browser</Eyebrow><h1>{me ? `${me.participant.name}’s review desk.` : 'A place for your judgment.'}</h1><p className="p-lead">Return to a case, revisit your reasoning, or pick up where you left off.</p>
    {!me ? <div className="p-card"><p>Your first question or case starts your notebook. No password or background form needed.</p><Link className="p-button" to="/case/insurance-cutoff">Start a case <ArrowRight size={16} /></Link></div> : <>
      <div className="p-notebook-meta"><span>{me.runs.filter(r => r.status === 'completed').length} completed reviews</span><span>{me.participant.role} · {me.participant.experience}</span><span>{me.participant.identity === 'guest' ? 'Guest · background not yet supplied' : 'Self-reported background'}</span></div>
      {!me.runs.length && <p>No reviews yet. <Link to="/">Choose your first case.</Link></p>}
      {me.runs.map(r => <Link key={r.id} className="p-notebook-row" to={`/session/${r.id}`}><span><span className="p-meta">{r.kind === 'ask' ? 'Your question' : 'Sample case'} · {date(r.created_at)} · {r.mode === 'local-cli' ? 'Local CLI responses' : r.mode === 'openrouter' ? 'Live model responses' : 'Authored fixtures'}</span><h3>{r.title}</h3>{r.kind === 'ask' && <p>{r.brief.slice(0, 130)}</p>}</span><span>{r.status === 'completed' ? 'See reveal' : r.status === 'failed' ? 'Request failed' : 'Continue'} <ArrowUpRight size={15} /></span></Link>)}
      <p className="p-fine">Saved on Calibrated and linked to this browser. Clearing browser storage or changing devices starts a new identity; this is not a verified account. Contact the Calibrated team to withdraw or have your data removed.</p>
    </>}
  </div>
}

function Method() {
  const { config } = usePilot()
  return <div className="p-narrow p-method"><Eyebrow>Calibrated · Accounting</Eyebrow><h1>How comparisons work</h1><p className="p-lead">Bring a question, compare two drafts, and decide what you would use.</p>
    <h2>One workspace, two sources of drafts</h2><p>Choose Journal entry, Treatment memo or Workpaper review. Your prompt and selected type go to both models with the same accounting instructions. Fixed sample cases are authored ahead of time and have a policy-based explanation. Selecting a sample loads its exact brief; editing that brief switches back to a new model comparison. Open prompts are never mapped to sample answers.</p><h2>What you do</h2><p>For your own prompt, go straight to the two anonymous drafts. Sample cases first ask for your independent conclusion. Review each draft, choose which you would build on, and give a reason. Saving your judgment reveals the authors and any available case explanation.</p>
    <h2>What the checks can tell you</h2><p>Sample cases use explicit policies and frozen, authored drafts. Structured checks compare debit/credit balance and the accounts, dates and amounts in the supplied case. They do not establish overall accounting competence. The explanation applies to the supplied facts and policy; you can flag missing facts or suggest a correction.</p>
    <h2>What your judgment tells us</h2><p>Approval, preference, confidence and corrections answer different questions. Two acceptable drafts may serve different reviewers. A preferred draft may still need correction. Your saved review keeps those distinctions.</p>
    <h2 id="data-use">What is saved—and what stays private</h2><p>The Calibrated team can inspect your self-reported background, submitted questions, conclusions, judgments, notes, optional contact details and interaction timestamps. Your notebook and service activity are stored to provide the service. Optional permission for private research is recorded separately in your profile; submitting a prompt does not mark that permission as granted. Publication and model-training use are not granted. To withdraw or request deletion, contact the person who invited you.</p><p>{config?.inference_backend === 'local-cli' ? 'Questions are sent through the locally installed Codex and Claude Code applications using the host’s signed-in accounts. Responses run on their providers, not on this computer. The applications use different model harnesses and account data settings; OpenRouter routing settings do not apply.' : 'Questions are sent to two configured models through OpenRouter with zero-data-retention routing requested.'} Your question and answers are saved in your private notebook. Never submit confidential client or employer information.</p>
    <h2>Your notebook</h2><p>Your comparisons and judgments are saved for this browser. Use the same browser to return to your work; cross-device sign-in is not available.</p>
    <Link className="p-button" to="/case/insurance-cutoff">Try a case <ArrowRight size={16} /></Link>
  </div>
}

function NotFound() { return <div className="p-narrow"><h1>Page not found.</h1><p>The practice room has the current cases and your notebook has your saved work.</p><Link className="p-button" to="/">Go to practice</Link></div> }

interface ExportData { schema_version: string; participants: (Me['participant'] & { created_at: string; source: string; dataset?: string; research_consent?: boolean })[]; runs: (Run & { participant_id: string })[]; events: { participant_id: string; run_id?: string; name: string; at: string }[] }
function Founder() {
  const [key, setKey] = useState(''); const [data, setData] = useState<ExportData | null>(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const load = async (e: FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { setData(await call<ExportData>('/founder/export', undefined, { 'X-Pilot-Admin': key })); setKey('') } catch (e) { setError(errorText(e)) } finally { setBusy(false) } }
  const download = () => { const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `calibrated-private-pilot-${new Date().toISOString().slice(0, 10)}.json`; a.click(); URL.revokeObjectURL(url) }
  return <div className="p-workspace"><Eyebrow>Private · review records</Eyebrow><h1>Comparisons and judgments.</h1><p className="p-lead">Inspect real participation and raw judgments. Authored drafts remain fixtures, even when reviewed by real people.</p>
    <form className="p-card" onSubmit={load}><label>Private founder token<input type="password" value={key} onChange={e => setKey(e.target.value)} required autoComplete="off" /></label><p className="p-fine">Uses PILOT_ADMIN_TOKEN from the server. The token is never persisted in this browser.</p><ErrorNote message={error} /><button className="p-button" disabled={busy}>{busy ? 'Loading…' : 'Open private records'}</button></form>
    {data && <><div className="p-actions"><button className="p-secondary" onClick={download}>Export private raw JSON</button><span className="p-fine">Contains contact details and questions. Do not publish.</span></div>
      <div className="p-founder-summary"><span>{data.participants.length} browser profiles</span><span>{data.runs.filter(r => r.status === 'completed').length} completed judgments</span><span>{data.runs.filter(r => r.status !== 'completed').length} incomplete / failed</span></div>
      {data.participants.map(p => { const runs = data.runs.filter(r => r.participant_id === p.id); const days = new Set(data.events.filter(e => e.participant_id === p.id && ['visit', 'session_started', 'judgment_completed'].includes(e.name)).map(e => e.at.slice(0, 10))); return <section className="p-card" key={p.id}><h2>{p.name}</h2><p>{p.role} · {p.experience} · {p.framework} · source: {p.source} · dataset: {p.dataset || 'preview'}</p><p className="p-fine">{runs.filter(r => r.status === 'completed').length} completed · {days.size} UTC activity days · {p.followup ? `Follow-up permitted: ${p.email}` : 'No follow-up permission'} · Research reuse: {p.research_consent ? 'opted in' : 'not opted in'}</p>
        {runs.map(r => <details className="p-own" key={r.id}><summary>{r.title} · {r.status} · {r.mode} · {date(r.created_at)}</summary><p>{r.brief}</p><p>Independent conclusion: {r.conclusion || 'Not submitted / Ask'}</p>{r.judgment && <><p>Preference: {labels[r.judgment.preference]} · A: {labels[r.judgment.a]} · B: {labels[r.judgment.b]} · Confidence: {r.judgment.confidence} · {Math.round((r.judgment.decision_ms ?? 0) / 1000)} seconds</p><p>Reasons: {r.judgment.reasons.join(', ')}</p><p>Explanation: {r.judgment.rationale || 'None'}</p><p>Correction: {r.judgment.correction || 'None'}</p></>}<p>Usefulness: {r.feedback?.usefulness || 'Not submitted'} · {r.feedback?.note}</p><p className="p-fine">Events: {data.events.filter(e => e.run_id === r.id).map(e => `${e.name} (${new Date(e.at).toLocaleTimeString()})`).join(' → ')}</p></details>)}
      </section> })}</>}
  </div>
}
