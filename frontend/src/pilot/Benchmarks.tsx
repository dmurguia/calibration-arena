import { ReactNode, useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { ArrowUpRight, Ban, Building2, Columns3, LayoutGrid, Quote, RefreshCw, Search, ShieldCheck } from 'lucide-react'
import BenchmarkBoards, { Board, ModelRec } from './BenchmarkBoards'
import { currentFlags, useFreshnessClock } from './benchmarkFreshness'
import './benchmarks.css'

type ResultsStatus = 'leaderboard' | 'snapshot' | 'archived' | 'unpublished' | 'unknown'
type Flag = 'review_due' | 'results_stale' | 'undated_results' | 'vendor_published' | 'mirror_source'
interface Results { as_of: string | null; metric: string | null; leader: string | null; leader_score: string | null; models_evaluated: number | null; source_url: string | null; source_type: string; note: string | null }
interface Benchmark {
  id: string; name: string; publisher: string; publisher_type: string; kind: string; domains: string[]; summary: string; metric_definitions?: Record<string, string>
  task_format: string; size: string | null; stateful: boolean; grader: string; data_access: string; license: string | null
  relevance: 'core' | 'adjacent' | 'reference'; relevance_note: string; results_status: ResultsStatus; results: Results | null
  links: Partial<Record<'home' | 'leaderboard' | 'paper' | 'data' | 'code', string>>; first_published: string; last_verified: string; notes: string | null; flags: Flag[]
}
interface Product { id: string; name: string; url: string; status: 'published' | 'claim_only' | 'none_found'; claim: string | null; claim_source: string | null; benchmark_ids: string[]; last_verified: string }
interface Catalog { catalog_updated: string; review_after_days: number; results_stale_after_days: number; counts: { benchmarks: number; by_results_status: Record<ResultsStatus, number> }; benchmarks: Benchmark[]; products: Product[]; models?: ModelRec[]; boards?: Board[]; refresh?: { cadence: string; checked_at: string; snapshot_id: string; sources: Record<string, { status: string }> } }

function isCatalog(value: Catalog): boolean {
  return !!value && typeof value.catalog_updated === 'string' && !!value.counts?.by_results_status
    && Array.isArray(value.benchmarks) && value.benchmarks.length > 0 && Array.isArray(value.products)
    && Array.isArray(value.models) && Array.isArray(value.boards) && value.boards.length > 0
    && value.boards.every(b => Array.isArray(b.entries) && b.entries.length > 0 && Array.isArray(b.metrics) && b.metrics.length > 0)
}

const DOMAINS: Record<string, string> = { accounting: 'Accounting & close', audit: 'Audit', tax: 'Tax', financial_analysis: 'Financial analysis', modeling_spreadsheets: 'Modeling & spreadsheets', investment_banking: 'Investment banking', financial_nlp: 'Financial NLP', reporting_xbrl: 'Reporting & XBRL', exams_knowledge: 'Exams & knowledge', general_work: 'General work' }
const STATUS: Record<ResultsStatus, string> = { leaderboard: 'Live leaderboard', snapshot: 'One-time results', archived: 'Archived', unpublished: 'No public results', unknown: 'Results unverified' }
const ACCESS: Record<string, string> = { open: 'Open data', partial: 'Partly open', on_request: 'On request', private: 'Private', unknown: 'Unknown' }
const FORMAT: Record<string, string> = { agentic: 'Agentic', document_qa: 'Document QA', qa: 'Q&A', extraction: 'Extraction', classification: 'Classification', generation: 'Generation', preference: 'Preference votes', composite: 'Composite' }
const GRADER: Record<string, string> = { rubric_llm: 'Rubric · LLM judge', rubric: 'Rubric', reference_answer: 'Answer key', programmatic: 'Programmatic', human_expert: 'Human experts', pairwise_votes: 'Pairwise votes', composite: 'Composite', unspecified: 'Not disclosed' }
const RELEVANCE: Record<string, string> = { core: 'Core', adjacent: 'Adjacent', reference: 'Reference' }
const FLAGS: Record<Flag, string> = { review_due: 'Needs re-check', results_stale: 'Results over 6 months old', undated_results: 'Source shows no date', vendor_published: 'Vendor-published', mirror_source: 'Via third-party mirror' }
const SOURCE: Record<string, string> = { first_party: 'Publisher', vendor_report: 'Vendor report', paper: 'Paper', mirror: 'Third-party mirror' }
const STATUS_HELP: Record<ResultsStatus, string> = { leaderboard: 'The publisher keeps a public ranking and updates it as new models ship.', snapshot: 'Results were published once, in a paper, post or report, and are not kept up to date.', archived: 'There was a leaderboard, but the publisher has stopped updating it or taken it down.', unpublished: 'The benchmark exists, but no model results have been published.', unknown: "We haven't been able to confirm whether public results exist." }
const ACCESS_HELP: Record<string, string> = { open: 'The tasks and answers can be downloaded.', partial: 'Some data is public, such as a sample or dev split; the rest is held back.', on_request: 'The publisher shares the data on request.', private: 'The data has not been released.', unknown: "We couldn't determine whether the data is available." }
const RELEVANCE_HELP: Record<string, string> = { core: 'Closest to the accounting and close work Calibration Arena studies.', adjacent: 'A related finance or accounting skill, but narrower or less like day-to-day work.', reference: 'Background context, such as knowledge tests or earlier research.' }
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
      <div><span className={`bm-access bm-access-${b.data_access}`} title={ACCESS_HELP[b.data_access]}>{ACCESS[b.data_access]}</span></div>
      <div className="bm-result">
        <span className={`bm-status bm-status-${b.results_status}`} title={STATUS_HELP[b.results_status]}>{STATUS[b.results_status]}</span>
        {r?.leader_score && <span className="bm-leader">{r.leader ? `${r.leader} · ` : 'Top score · '}<b>{r.leader_score}</b>{r.metric && <span className="bm-metric"> {r.metric}</span>}</span>}
        {r && <span className="bm-asof" title={r.as_of ? undefined : `The source shows no date. We last checked it on ${monthLabel(b.last_verified)}.`}>{r.as_of ? `As of ${monthLabel(r.as_of)}` : `Undated · checked ${monthLabel(b.last_verified)}`}</span>}
      </div>
      <div><span className={`bm-rel bm-rel-${b.relevance}`} title={RELEVANCE_HELP[b.relevance]}>{RELEVANCE[b.relevance]}</span></div>
    </summary>
    <Details b={b} />
  </details>
}

function Details({ b, page = false }: { b: Benchmark; page?: boolean }) {
  const r = b.results
  return <div className="bm-detail">
    {!page && <p>{b.summary}</p>}
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
    <p className="bm-links">{!page && <Link to={`/benchmarks/${b.id}`}>Benchmark page</Link>}{LINKS.filter(([k]) => b.links[k]).map(([k, label]) => <Ext key={k} href={b.links[k]!}>{label}</Ext>)}</p>
  </div>
}

type Section = 'leaderboards' | 'all' | 'awaiting' | 'method' | 'detail'
const SECTIONS: Record<string, Section> = { '': 'leaderboards', all: 'all', awaiting: 'awaiting', method: 'method' }

const PUBLISHER: Record<string, string> = { academic: 'Academic', eval_lab: 'Eval lab', vendor: 'Vendor', aggregator: 'Aggregator', community: 'Community', consortium: 'Consortium', other: 'Other' }
const PIPELINE: [ReactNode, string, string][] = [
  [<Building2 size={18} aria-hidden />, 'Publisher runs it', 'Tasks, grading and scores stay with the publisher.'],
  [<RefreshCw size={18} aria-hidden />, 'Checked daily', 'Each model board is fetched from its source every day.'],
  [<ShieldCheck size={18} aria-hidden />, 'Validated', 'A failed check keeps the last verified board.'],
  [<LayoutGrid size={18} aria-hidden />, 'Shown here', 'One board per benchmark, linked to its source.'],
]
const PRINCIPLES: [ReactNode, string][] = [
  [<Quote size={16} aria-hidden />, "The publisher's own score"],
  [<Columns3 size={16} aria-hidden />, 'One board per benchmark'],
  [<Ban size={16} aria-hidden />, 'Never re-run, rescaled or combined'],
]

function tally<T extends string>(items: T[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, k) => ({ ...acc, [k]: (acc[k] ?? 0) + 1 }), {})
}

function Split({ title, labels, counts, help, total }: { title: string; labels: Record<string, string>; counts: Record<string, number>; help?: Record<string, string>; total: number }) {
  const keys = Object.keys(labels).filter(k => counts[k])
  return <figure className="bm-split">
    <figcaption>{title}</figcaption>
    <div className="bm-split-bar" role="img" aria-label={keys.map(k => `${labels[k]} ${counts[k]}`).join(', ')}>
      {keys.map((k, i) => <span key={k} className={`bm-tone-${i}`} style={{ flexGrow: counts[k] }} title={`${labels[k]}: ${counts[k]}`} />)}
    </div>
    <ul>{keys.map((k, i) => <li key={k} title={help?.[k]}><i className={`bm-tone-${i}`} aria-hidden /><b>{counts[k]}</b> {labels[k]}<span className="sr-only"> of {total}</span></li>)}</ul>
  </figure>
}

function Overview({ data, benchmarks }: { data: Catalog; benchmarks: Benchmark[] }) {
  const areas = tally(benchmarks.flatMap(b => b.domains))
  const maxArea = Math.max(...Object.values(areas))
  const boardIds = new Set(data.boards?.map(b => b.benchmark_id))
  const n = benchmarks.length
  return <section className="bm-overview" aria-labelledby="method">
    <h2 id="method" className="bm-section-title">Overview</h2>
    <ul className="bm-principles">{PRINCIPLES.map(([icon, text]) => <li key={text}>{icon}{text}</li>)}</ul>

    <h3>How a score gets here</h3>
    <ol className="bm-flow">{PIPELINE.map(([icon, title, text]) => <li key={title}>{icon}<b>{title}</b><span>{text}</span></li>)}</ol>
    <p className="bm-fine">{data.boards?.length ?? 0} model boards are checked daily; a check older than 36 hours is marked overdue on that board. The rest of the directory is reviewed every {data.review_after_days} days.</p>

    <h3>What exists</h3>
    <div className="bm-areas-chart" role="list">
      {Object.entries(DOMAINS).filter(([k]) => areas[k]).sort((a, b) => areas[b[0]] - areas[a[0]]).map(([k, label]) => {
        const withBoard = benchmarks.filter(b => b.domains.includes(k) && boardIds.has(b.id)).length
        return <div role="listitem" key={k} className="bm-area-row">
          <span>{label}</span>
          <span className="bm-area-track" title={`${areas[k]} benchmarks, ${withBoard} with a daily model board`}>
            <span className="bm-area-fill" style={{ width: `${(areas[k] / maxArea) * 100}%` }}><span className="bm-area-board" style={{ width: `${(withBoard / areas[k]) * 100}%` }} /></span>
          </span>
          <b>{areas[k]}</b>
        </div>
      })}
      <p className="bm-legend"><i className="bm-area-board" aria-hidden /> With a daily model board <i className="bm-area-fill" aria-hidden /> Listed</p>
    </div>

    <div className="bm-splits" id="labels">
      <Split title="Published results" labels={STATUS} help={STATUS_HELP} counts={tally(benchmarks.map(b => b.results_status))} total={n} />
      <Split title="Data access" labels={ACCESS} help={ACCESS_HELP} counts={tally(benchmarks.map(b => b.data_access))} total={n} />
      <Split title="Relevance to accounting work" labels={RELEVANCE} help={RELEVANCE_HELP} counts={tally(benchmarks.map(b => b.relevance))} total={n} />
      <Split title="Who publishes" labels={PUBLISHER} counts={tally(benchmarks.map(b => b.publisher_type))} total={n} />
    </div>

    <p className="bm-fine">Catalog metadata is open as <a href="/benchmarks.json">benchmarks.json</a> (CC BY 4.0). Scores stay under each publisher's terms. <a href={CONTACT} target="_blank" rel="noreferrer">Submit results or correct a listing</a></p>
  </section>
}

const AREA_WORD: Record<string, string> = { accounting: 'accounting', audit: 'audit', tax: 'tax', financial_analysis: 'finance', modeling_spreadsheets: 'financial modeling', investment_banking: 'investment banking', financial_nlp: 'financial NLP', reporting_xbrl: 'financial reporting', exams_knowledge: 'accounting exam', general_work: 'professional work' }
const SITE = 'Calibration Arena'
const SECTION_TITLES: Record<Exclude<Section, 'detail'>, string> = {
  leaderboards: `Finance & Accounting AI Benchmark Leaderboards | ${SITE}`,
  all: `All Finance & Accounting AI Benchmarks | ${SITE}`,
  awaiting: `Finance AI Benchmarks Awaiting Public Results | ${SITE}`,
  method: `How the Benchmark Directory Works | ${SITE}`,
}
const SECTION_DESCRIPTIONS: Record<Exclude<Section, 'detail'>, string> = {
  leaderboards: 'Which AI models lead each public accounting and finance benchmark: Vals AI, APEX-Accounting, DualEntry, TaxBench and more, in each publisher\'s own metric, checked daily.',
  all: 'Directory of public accounting, tax, audit and finance AI benchmarks, with data access, grading method, license and the latest published results.',
  awaiting: 'Accounting and finance AI benchmarks and products that have no public model results yet.',
  method: 'How Calibration Arena tracks publisher-owned accounting and finance AI benchmarks: checked daily, never re-run, rescaled or combined.',
}
// Keep in sync with scripts/prerender-benchmarks.mjs, which writes the same tags into static HTML.
export function benchmarkTitle(b: Pick<Benchmark, 'name' | 'publisher' | 'domains'>) {
  return `${b.name} Leaderboard · ${b.publisher} ${AREA_WORD[b.domains[0]] ?? 'finance'} benchmark | ${SITE}`
}
export function benchmarkDescription(b: Pick<Benchmark, 'summary' | 'publisher' | 'results'>) {
  const r = b.results
  const lead = r?.leader && r.leader_score ? ` Top model: ${r.leader} (${r.leader_score}${r.metric ? ` ${r.metric.toLowerCase()}` : ''}${r.as_of ? `, ${r.as_of}` : ''}).` : ''
  return `${b.summary}${lead} Results from ${b.publisher}, linked to the source.`.slice(0, 300)
}

function setHeadTag(selector: string, create: () => HTMLElement, attr: string, value: string) {
  let el = document.head.querySelector<HTMLElement>(selector)
  if (!el) { el = create(); document.head.appendChild(el) }
  const previous = el.getAttribute(attr)
  el.setAttribute(attr, value)
  return () => { if (previous === null) el!.remove(); else el!.setAttribute(attr, previous) }
}

function usePageMeta(title: string | null, description: string | null, path: string) {
  useEffect(() => {
    if (!title) return
    const previousTitle = document.title
    document.title = title
    const restore = [
      description && setHeadTag('meta[name="description"]', () => Object.assign(document.createElement('meta'), { name: 'description' }), 'content', description),
      setHeadTag('link[rel="canonical"]', () => Object.assign(document.createElement('link'), { rel: 'canonical' }), 'href', `https://calibrationarena.ai${path}`),
    ]
    return () => { document.title = previousTitle; restore.forEach(undo => undo && undo()) }
  }, [title, description, path])
}

function TryIt() {
  return <Link className="p-button bm-try" to="/ask">Try it on your own task<ArrowUpRight size={14} aria-hidden /></Link>
}

export default function Benchmarks() {
  const location = useLocation()
  const slug = location.pathname.replace(/^\/benchmarks\/?/, '').replace(/\/$/, '')
  const section: Section | undefined = SECTIONS[slug] ?? (/^[a-z0-9-]+$/.test(slug) ? 'detail' : undefined)
  const [data, setData] = useState<Catalog | null>(null)
  const [usingFallback, setUsingFallback] = useState(false)
  const now = useFreshnessClock()
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [domain, setDomain] = useState('')
  const [status, setStatus] = useState('')
  const [access, setAccess] = useState('')
  const [relevance, setRelevance] = useState('')
  const [agentic, setAgentic] = useState(false)
  useEffect(() => {
    let active = true
    const load = async (url: string, feed: boolean) => {
      const res = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(8000) })
      if (!res.ok) throw new Error('Catalog unavailable')
      const value: Catalog = await res.json()
      if (!isCatalog(value) || (feed && (!value.refresh?.snapshot_id || !value.refresh.checked_at))) throw new Error('Invalid catalog')
      return value
    }
    load('/benchmark-feed/benchmarks.json', true).then(value => {
      if (active) setData(value)
    }).catch(() => load('/benchmarks.json', false).then(value => {
      if (active) { setData(value); setUsingFallback(true) }
    })).catch(() => { if (active) setError('The benchmark catalog is unavailable right now.') })
    return () => { active = false }
  }, [])
  useEffect(() => {
    const id = decodeURIComponent(location.hash.slice(1))
    if (!data || !id) return
    const el = document.getElementById(id)
    if (el instanceof HTMLDetailsElement) el.open = true
    const frame = requestAnimationFrame(() => el?.scrollIntoView({ block: 'start' }))
    return () => cancelAnimationFrame(frame)
  }, [data, location.hash, section])
  const rows = useMemo(() => {
    if (!data) return []
    const q = query.trim().toLowerCase()
    return data.benchmarks.map(b => currentFlags(b, now, data.review_after_days, data.results_stale_after_days)).filter(b =>
      (!q || [b.name, b.publisher, b.summary, b.results?.leader ?? ''].join(' ').toLowerCase().includes(q)) &&
      (!domain || b.domains.includes(domain)) && (!status || b.results_status === status) &&
      (!access || b.data_access === access) && (!relevance || b.relevance === relevance) &&
      (!agentic || b.task_format === 'agentic' || b.stateful))
  }, [data, now, query, domain, status, access, relevance, agentic])
  const awaiting = data?.benchmarks.filter(b => b.results_status === 'unpublished' || b.results_status === 'unknown') ?? []
  const quiet = data?.products.filter(p => p.status !== 'published') ?? []
  const filtered = !!(query || domain || status || access || relevance || agentic)
  const page = section === 'detail' ? data?.benchmarks.find(b => b.id === slug) : undefined
  const pageBoard = page && data?.boards?.find(b => b.benchmark_id === page.id)
  usePageMeta(section === 'detail' ? (page ? benchmarkTitle(page) : null) : section ? SECTION_TITLES[section] : null,
    page ? benchmarkDescription(page) : section && section !== 'detail' ? SECTION_DESCRIPTIONS[section] : null,
    `/benchmarks${slug ? `/${slug}` : ''}`)
  if (!section || (section === 'detail' && data && !page)) return <div className="p-workspace bm-page"><h1 className="bm-title">Page not found</h1><p><Link to="/benchmarks">Back to the leaderboards</Link></p></div>
  return <div className="p-workspace bm-page" data-snapshot-id={data?.refresh?.snapshot_id ?? 'bundled'}>
    <header className="bm-intro">
      {page ? <>
        <p className="bm-crumb"><Link to="/benchmarks">Industry Benchmarks</Link> / <Link to="/benchmarks/all">All benchmarks</Link></p>
        <h1 className="bm-title">{page.name}</h1>
        <p className="bm-tagline">{page.publisher} · {page.domains.map(d => DOMAINS[d]).join(' · ')} · {STATUS[page.results_status]}</p>
      </> : <>
        <h1 className="bm-title">Industry Benchmarks</h1>
        <p className="bm-tagline">Calibration Arena's pulse on accounting and financial AI benchmarks.</p>
      </>}
      <TryIt />
      {data && section !== 'detail' && <p className="bm-tally">
        <span><b>{data.counts.benchmarks}</b> benchmarks tracked</span>
        <span><b>{data.counts.by_results_status.leaderboard}</b> live leaderboards</span>
        <Link to="/benchmarks/awaiting"><b>{awaiting.length + quiet.length}</b> awaiting public results</Link>
        {data.refresh?.cadence === 'daily' && !usingFallback
          ? <span>Checked daily · {data.boards?.length} model boards</span>
          : <span>Snapshot {monthLabel(data.catalog_updated)}</span>}
      </p>}
      {usingFallback && <p className="bm-freshness-notice" role="status">Daily feed unavailable. Showing the saved catalog; check each board’s date.</p>}
    </header>
    {section !== 'detail' && <nav className="bm-tabs" aria-label="Benchmark sections">
      <NavLink to="/benchmarks" end>Leaderboards</NavLink>
      <NavLink to="/benchmarks/all">All benchmarks{data && <span>{data.counts.benchmarks}</span>}</NavLink>
      <NavLink to="/benchmarks/awaiting">Awaiting results{data && <span>{awaiting.length + quiet.length}</span>}</NavLink>
      <NavLink to="/benchmarks/method">Overview</NavLink>
    </nav>}
    {error && <p className="p-error" role="alert">{error}</p>}
    {!data && !error && <p className="p-loading" role="status">Loading the catalog…</p>}
    {data && section === 'leaderboards' && (data.boards?.length
      ? <BenchmarkBoards boards={data.boards} models={data.models ?? []} benchmarks={data.benchmarks} />
      : <p className="bm-empty">No model boards are published yet. <Link to="/benchmarks/all">Browse all benchmarks</Link>.</p>)}

    {data && section === 'all' && <section aria-labelledby="directory">
      <h2 id="directory" className="bm-section-title">All {data.counts.benchmarks} benchmarks, with or without model results</h2>
      <div className="bm-filters" role="search">
        <label className="bm-search"><Search size={15} aria-hidden /><span className="sr-only">Search benchmarks</span><input type="search" placeholder="Search benchmarks, publishers, models" value={query} onChange={e => setQuery(e.target.value)} /></label>
        <label>Area<select value={domain} onChange={e => setDomain(e.target.value)}><option value="">All areas</option>{Object.entries(DOMAINS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Results<select value={status} onChange={e => setStatus(e.target.value)}><option value="">Any results</option>{Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Data<select value={access} onChange={e => setAccess(e.target.value)}><option value="">Any access</option>{Object.entries(ACCESS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Relevance<select value={relevance} onChange={e => setRelevance(e.target.value)}><option value="">Any relevance</option>{Object.entries(RELEVANCE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label className="bm-check"><input type="checkbox" checked={agentic} onChange={e => setAgentic(e.target.checked)} />Agentic or stateful only</label>
      </div>
      <p className="bm-count" aria-live="polite">{filtered ? `${rows.length} of ${data.benchmarks.length} shown` : `${data.benchmarks.length} listed`}. Select a row for methodology, license and sources. <Link to="/benchmarks/method#labels">What the labels mean</Link></p>
      <div className="bm-table" role="list">
        <div className="bm-head" aria-hidden><span>Benchmark</span><span>Area &amp; format</span><span>Data</span><span>Published results</span><span>Relevance</span></div>
        {rows.map(b => <div role="listitem" key={b.id}><Row b={b} /></div>)}
        {!rows.length && <p className="bm-empty">No benchmarks match these filters.</p>}
      </div>
    </section>}

    {data && section === 'awaiting' && <section className="bm-awaiting" aria-labelledby="awaiting">
      <h2 id="awaiting" className="bm-section-title">Built, or claimed, but not yet published</h2>
      <p>These benchmarks exist, or these products make accuracy claims, but we couldn't find public model results with a method we could check. If you publish results, we'll list them with a link back to you.</p>
      <h3>Benchmarks without public results <span>{awaiting.length}</span></h3>
      <div className="bm-awaiting-grid">
        {awaiting.map(b => <Link key={b.id} to={{ pathname: '/benchmarks/all', hash: b.id }} className="bm-await-card">
          <span className="bm-await-kind" title={STATUS_HELP[b.results_status]}>{STATUS[b.results_status]}</span><strong>{b.name}</strong><span>{b.publisher}</span></Link>)}
      </div>
      <h3>Products with no public evaluation <span>{quiet.length}</span></h3>
      <div className="bm-awaiting-grid">
        {quiet.map(p => <div key={p.id} className="bm-await-card">
          <span className="bm-await-kind">{p.status === 'claim_only' ? 'Accuracy claim, no public evaluation' : 'No public evaluation found'}</span>
          <strong><Ext href={p.url}>{p.name}</Ext></strong>
          {p.claim && p.claim_source && <span>{p.claim} <Ext href={p.claim_source}>source</Ext></span>}
          <span className="bm-asof">Checked {monthLabel(p.last_verified)}</span>
        </div>)}
      </div>
      <a className="p-secondary" href={CONTACT} target="_blank" rel="noreferrer">Submit results or correct a listing</a>
    </section>}

    {data && section === 'method' && <Overview data={data} benchmarks={data.benchmarks} />}

    {page && data && <section className="bm-bench-page" aria-label={`${page.name} details`}>
      {pageBoard
        ? <BenchmarkBoards boards={[pageBoard]} models={data.models ?? []} benchmarks={data.benchmarks} single />
        : <p className="bm-empty">{page.results?.leader_score ? `Published top score: ${page.results.leader ?? 'not named'} · ${page.results.leader_score}${page.results.metric ? ` ${page.results.metric}` : ''}.` : 'No model-by-model board is published for this benchmark.'}</p>}
      {!pageBoard && <p className="bd-what">{page.summary}</p>}
      <div className="bm-detail-card"><Details b={page} page /></div>
      <aside className="bm-try-panel">
        <h2>How do models handle your own work?</h2>
        <p>{page.name} tests the tasks its publisher chose. Bring a task from your own close, reconciliation or reporting work and compare two models' answers side by side.</p>
        <TryIt />
      </aside>
    </section>}
  </div>
}
