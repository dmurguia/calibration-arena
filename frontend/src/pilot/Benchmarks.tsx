import { ReactNode, useEffect, useMemo, useState } from 'react'
import { ArrowUpRight, Search } from 'lucide-react'
import BenchmarkBoards, { Board, ModelRec } from './BenchmarkBoards'
import './benchmarks.css'

type ResultsStatus = 'leaderboard' | 'snapshot' | 'archived' | 'unpublished' | 'unknown'
type Flag = 'review_due' | 'results_stale' | 'undated_results' | 'vendor_published' | 'mirror_source'
interface Results { as_of: string | null; metric: string | null; leader: string | null; leader_score: string | null; models_evaluated: number | null; source_url: string | null; source_type: string; note: string | null }
interface Benchmark {
  id: string; name: string; publisher: string; publisher_type: string; kind: string; domains: string[]; summary: string
  task_format: string; size: string | null; stateful: boolean; grader: string; data_access: string; license: string | null
  relevance: 'core' | 'adjacent' | 'reference'; relevance_note: string; results_status: ResultsStatus; results: Results | null
  links: Partial<Record<'home' | 'leaderboard' | 'paper' | 'data' | 'code', string>>; first_published: string; last_verified: string; notes: string | null; flags: Flag[]
}
interface Product { id: string; name: string; url: string; status: 'published' | 'claim_only' | 'none_found'; claim: string | null; claim_source: string | null; benchmark_ids: string[]; last_verified: string }
interface Catalog { catalog_updated: string; review_after_days: number; results_stale_after_days: number; counts: { benchmarks: number; by_results_status: Record<ResultsStatus, number> }; benchmarks: Benchmark[]; products: Product[]; models?: ModelRec[]; boards?: Board[] }

const DOMAINS: Record<string, string> = { accounting: 'Accounting & close', audit: 'Audit', tax: 'Tax', financial_analysis: 'Financial analysis', modeling_spreadsheets: 'Modeling & spreadsheets', investment_banking: 'Investment banking', financial_nlp: 'Financial NLP', reporting_xbrl: 'Reporting & XBRL', exams_knowledge: 'Exams & knowledge', general_work: 'General work' }
const STATUS: Record<ResultsStatus, string> = { leaderboard: 'Live leaderboard', snapshot: 'One-time results', archived: 'Archived', unpublished: 'No public results', unknown: 'Results unverified' }
const ACCESS: Record<string, string> = { open: 'Open data', partial: 'Partly open', on_request: 'On request', private: 'Private', unknown: 'Unknown' }
const FORMAT: Record<string, string> = { agentic: 'Agentic', document_qa: 'Document QA', qa: 'Q&A', extraction: 'Extraction', classification: 'Classification', generation: 'Generation', preference: 'Preference votes', composite: 'Composite' }
const GRADER: Record<string, string> = { rubric_llm: 'Rubric · LLM judge', rubric: 'Rubric', reference_answer: 'Answer key', programmatic: 'Programmatic', human_expert: 'Human experts', pairwise_votes: 'Pairwise votes', composite: 'Composite', unspecified: 'Not disclosed' }
const RELEVANCE: Record<string, string> = { core: 'Core', adjacent: 'Adjacent', reference: 'Reference' }
const FLAGS: Record<Flag, string> = { review_due: 'Needs re-check', results_stale: 'Results over 6 months old', undated_results: 'Source shows no date', vendor_published: 'Vendor-published', mirror_source: 'Via third-party mirror' }
const SOURCE: Record<string, string> = { first_party: 'Publisher', vendor_report: 'Vendor report', paper: 'Paper', mirror: 'Third-party mirror' }
const LINKS: [keyof Benchmark['links'], string][] = [['leaderboard', 'Leaderboard'], ['home', 'Site'], ['paper', 'Paper'], ['data', 'Data'], ['code', 'Code']]
const CONTACT = 'https://github.com/dmurguia/calibration-arena/issues/new?title=Benchmark%20listing%3A%20'

function monthLabel(value: string | null) {
  if (!value) return 'undated'
  const [y, m, d] = value.split('-').map(Number)
  if (!m) return String(y)
  return new Date(Date.UTC(y, m - 1, d || 1)).toLocaleDateString(undefined, { month: 'short', year: 'numeric', ...(d ? { day: 'numeric' } : {}), timeZone: 'UTC' })
}

function Ext({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href} target="_blank" rel="noreferrer">{children}<ArrowUpRight size={12} aria-hidden /></a>
}

function Row({ b }: { b: Benchmark }) {
  const r = b.results
  return <details className="bm-row" id={b.id}>
    <summary>
      <div className="bm-name"><strong>{b.name}</strong><span>{b.publisher}</span></div>
      <div className="bm-area">{b.domains.map(d => DOMAINS[d]).join(' · ')}<span>{FORMAT[b.task_format]}{b.stateful ? ' · stateful' : ''}</span></div>
      <div><span className={`bm-access bm-access-${b.data_access}`}>{ACCESS[b.data_access]}</span></div>
      <div className="bm-result">
        <span className={`bm-status bm-status-${b.results_status}`}>{STATUS[b.results_status]}</span>
        {r?.leader_score && <span className="bm-leader">{r.leader ? `${r.leader} · ` : 'Top score · '}<b>{r.leader_score}</b></span>}
        {r && <span className="bm-asof">{r.as_of ? `as of ${monthLabel(r.as_of)}` : 'no date on source'}</span>}
      </div>
      <div><span className={`bm-rel bm-rel-${b.relevance}`}>{RELEVANCE[b.relevance]}</span></div>
    </summary>
    <div className="bm-detail">
      <p>{b.summary}</p>
      <dl>
        {b.size && <><dt>Size</dt><dd>{b.size}</dd></>}
        <dt>Grading</dt><dd>{GRADER[b.grader]}</dd>
        <dt>License</dt><dd>{b.license ?? 'Not stated'}</dd>
        {r?.metric && <><dt>Metric</dt><dd>{r.metric}</dd></>}
        {r?.models_evaluated && <><dt>Models</dt><dd>{r.models_evaluated}</dd></>}
        {r && <><dt>Result source</dt><dd>{r.source_url ? <Ext href={r.source_url}>{SOURCE[r.source_type]}</Ext> : SOURCE[r.source_type]}</dd></>}
        <dt>Why it matters</dt><dd>{b.relevance_note}</dd>
        {(r?.note || b.notes) && <><dt>Notes</dt><dd>{[r?.note, b.notes].filter(Boolean).join(' ')}</dd></>}
        <dt>Last checked</dt><dd>{monthLabel(b.last_verified)}</dd>
      </dl>
      {b.flags.length > 0 && <p className="bm-flags">{b.flags.map(f => <span key={f}>{FLAGS[f]}</span>)}</p>}
      <p className="bm-links">{LINKS.filter(([k]) => b.links[k]).map(([k, label]) => <Ext key={k} href={b.links[k]!}>{label}</Ext>)}</p>
    </div>
  </details>
}

export default function Benchmarks() {
  const [data, setData] = useState<Catalog | null>(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [domain, setDomain] = useState('')
  const [status, setStatus] = useState('')
  const [access, setAccess] = useState('')
  const [relevance, setRelevance] = useState('')
  const [agentic, setAgentic] = useState(false)
  useEffect(() => {
    fetch('/benchmarks.json').then(res => { if (!res.ok) throw new Error(); return res.json() }).then(setData).catch(() => setError('The benchmark catalog is unavailable right now.'))
  }, [])
  const rows = useMemo(() => {
    if (!data) return []
    const q = query.trim().toLowerCase()
    return data.benchmarks.filter(b =>
      (!q || [b.name, b.publisher, b.summary, b.results?.leader ?? ''].join(' ').toLowerCase().includes(q)) &&
      (!domain || b.domains.includes(domain)) && (!status || b.results_status === status) &&
      (!access || b.data_access === access) && (!relevance || b.relevance === relevance) &&
      (!agentic || b.task_format === 'agentic' || b.stateful))
  }, [data, query, domain, status, access, relevance, agentic])
  const awaiting = data?.benchmarks.filter(b => b.results_status === 'unpublished' || b.results_status === 'unknown') ?? []
  const quiet = data?.products.filter(p => p.status !== 'published') ?? []
  const filtered = !!(query || domain || status || access || relevance || agentic)
  return <div className="p-workspace bm-page">
    <p className="p-eyebrow">Public benchmarks · Finance &amp; accounting</p>
    <h1>Every public AI benchmark for finance and accounting, in one place.</h1>
    <p className="p-lead">We track who publishes each benchmark, whether its data is open, how it's graded, and when its results were last checked. Every score links to its original source. We don't re-run or re-rank other people's benchmarks.</p>
    {error && <p className="p-error" role="alert">{error}</p>}
    {!data && !error && <p className="p-loading" role="status">Loading the catalog…</p>}
    {data && <>
      <div className="bm-stats">
        <div><b>{data.counts.benchmarks}</b><span>benchmarks &amp; indexes</span></div>
        <div><b>{data.counts.by_results_status.leaderboard}</b><span>live leaderboards</span></div>
        <div><b>{data.counts.by_results_status.snapshot + data.counts.by_results_status.archived}</b><span>one-time or archived results</span></div>
        <div><b>{awaiting.length + quiet.length}</b><span>awaiting public results</span></div>
        <div><b>{monthLabel(data.catalog_updated)}</b><span>catalog updated</span></div>
      </div>
      {!!data.boards?.length && <BenchmarkBoards boards={data.boards} models={data.models ?? []} benchmarks={data.benchmarks} />}

      <div className="bm-directory-head">
        <p className="p-eyebrow">Directory</p>
        <h2>All {data.counts.benchmarks} benchmarks, with or without model results</h2>
      </div>
      <div className="bm-filters" role="search">
        <label className="bm-search"><Search size={15} aria-hidden /><span className="sr-only">Search benchmarks</span><input type="search" placeholder="Search benchmarks, publishers, models" value={query} onChange={e => setQuery(e.target.value)} /></label>
        <label>Area<select value={domain} onChange={e => setDomain(e.target.value)}><option value="">All areas</option>{Object.entries(DOMAINS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Results<select value={status} onChange={e => setStatus(e.target.value)}><option value="">Any results</option>{Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Data<select value={access} onChange={e => setAccess(e.target.value)}><option value="">Any access</option>{Object.entries(ACCESS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Relevance<select value={relevance} onChange={e => setRelevance(e.target.value)}><option value="">Any relevance</option>{Object.entries(RELEVANCE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label className="bm-check"><input type="checkbox" checked={agentic} onChange={e => setAgentic(e.target.checked)} />Agentic or stateful only</label>
      </div>
      <p className="p-fine" aria-live="polite">{filtered ? `${rows.length} of ${data.benchmarks.length} shown` : `${data.benchmarks.length} listed`}. Select a row for methodology, license and sources.</p>
      <div className="bm-table" role="list">
        <div className="bm-head" aria-hidden><span>Benchmark</span><span>Area &amp; format</span><span>Data</span><span>Published results</span><span>Relevance</span></div>
        {rows.map(b => <div role="listitem" key={b.id}><Row b={b} /></div>)}
        {!rows.length && <p className="bm-empty">No benchmarks match these filters.</p>}
      </div>

      <section className="bm-awaiting" aria-labelledby="awaiting">
        <p className="p-eyebrow">Awaiting public results</p>
        <h2 id="awaiting">Built, or claimed, but not yet published.</h2>
        <p>These benchmarks exist, or these products make accuracy claims, but we couldn't find public model results with a method we could check. If you publish results, we'll list them with a link back to you.</p>
        <div className="bm-awaiting-grid">
          {awaiting.map(b => <a key={b.id} href={`#${b.id}`} className="bm-await-card" onClick={() => { const el = document.getElementById(b.id) as HTMLDetailsElement | null; if (el) el.open = true }}>
            <span className="bm-await-kind">Benchmark · {STATUS[b.results_status]}</span><strong>{b.name}</strong><span>{b.publisher}</span></a>)}
          {quiet.map(p => <div key={p.id} className="bm-await-card">
            <span className="bm-await-kind">Product · {p.status === 'claim_only' ? 'Accuracy claim, no public evaluation' : 'No public evaluation found'}</span>
            <strong><Ext href={p.url}>{p.name}</Ext></strong>
            {p.claim && p.claim_source && <span>{p.claim} <Ext href={p.claim_source}>source</Ext></span>}
            <span className="bm-asof">Checked {monthLabel(p.last_verified)}</span>
          </div>)}
        </div>
        <a className="p-secondary" href={CONTACT} target="_blank" rel="noreferrer">Submit results or correct a listing</a>
      </section>

      <section className="bm-method" aria-labelledby="method">
        <h2 id="method">How this list is maintained</h2>
        <ul>
          <li><b>Publishers own their results.</b> We copy the headline figure, metric and date as stated at the linked source, and label where it came from: the publisher, a vendor report, a paper, or a third-party mirror.</li>
          <li><b>Status and data access are separate.</b> A benchmark can have a live leaderboard and private data, or open data and no published results.</li>
          <li><b>Freshness is visible.</b> Every source is re-checked on a schedule. Rows not re-verified within {data.review_after_days} days, or leaderboards whose results are more than {data.results_stale_after_days} days old, are flagged.</li>
          <li><b>Open data.</b> The full catalog is available as <a href="/benchmarks.json">benchmarks.json</a>. Reuse it with attribution to the original publishers.</li>
        </ul>
      </section>
    </>}
  </div>
}
