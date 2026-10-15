import { ReactNode, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowUpRight, Search } from 'lucide-react'

export type Weights = 'open' | 'closed' | 'unknown'
export interface ModelRec { id: string; name: string; org: string | null; weights: Weights; weights_basis: 'publisher' | 'family' | 'conflict' | 'none'; weights_reported: Record<string, 'open' | 'closed'> }
export interface BoardEntry { model: string; label: string; config: string | null; scores: Record<string, number>; ci?: Record<string, [number, number]>; cost: number | null }
export interface Board { benchmark_id: string; source_url: string; adapter: string; as_of: string | null; retrieved: string; metrics: { key: string; label: string; unit: string }[]; cost_label: string | null; entries: BoardEntry[] }
export interface BoardBenchmark { id: string; name: string; publisher: string; domains: string[]; summary: string; metric_definitions?: Record<string, string>; results_status: string; relevance: string; results: { source_type: string; note: string | null } | null }

type Filter = 'all' | 'open' | 'closed'
interface Row { e: BoardEntry; m: ModelRec | undefined; score: number; rank: number; weights: Weights }

export const AREAS: [string, string][] = [['accounting', 'Accounting'], ['tax', 'Tax'], ['financial_analysis', 'Financial analysis'], ['investment_banking', 'Investment banking']]
const WEIGHTS: Record<Weights, string> = { open: 'Open weights', closed: 'Closed', unknown: 'Not stated' }
const BASIS: Record<ModelRec['weights_basis'], string> = { publisher: 'as reported by a benchmark publisher', family: 'from the model family\'s published license', conflict: 'publishers disagree', none: 'no public statement found' }
const SOURCE: Record<string, string> = { first_party: 'Publisher', vendor_report: 'Vendor report', paper: 'Paper', mirror: 'Third-party mirror' }
const TOP = 15
const MIN_COST_POINTS = 5
const LOGOS = new Set(['openai', 'google', 'anthropic', 'xai', 'meta', 'alibaba', 'deepseek', 'zhipu-ai', 'mistral', 'moonshot-ai', 'ai21-labs', 'nvidia', 'xiaomi', 'minimax', 'cohere', 'poolside', 'ant-group', 'tencent', 'inception', 'arcee-ai'])
const orgSlug = (org: string) => org.toLowerCase().replace(/[^a-z0-9]+/g, '-')
const initials = (org: string) => org.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase()

function dateLabel(value: string) {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
}
const pct = (v: number) => `${Number(v.toFixed(1))}%`
function money(v: number) { return v >= 1 ? `$${v.toFixed(2)}` : v >= 0.01 ? `$${v.toFixed(3)}` : `$${v.toPrecision(2)}` }
const entryName = (e: BoardEntry) => e.config ? `${e.label} (${e.config})` : e.label
const rowName = (r: Row) => r.m?.name ?? r.e.label
const rowKey = (r: Row) => `${r.e.label}|${r.e.config}`

function Ext({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href} target="_blank" rel="noreferrer">{children}<ArrowUpRight size={12} aria-hidden /></a>
}

function Logo({ org, size = 18 }: { org: string | null | undefined; size?: number }) {
  const slug = org ? orgSlug(org) : ''
  return LOGOS.has(slug)
    ? <img className="bd-logo" src={`/logos/${slug}.svg`} alt="" title={org ?? undefined} width={size} height={size} />
    : <span className="bd-logo bd-logo-initials" title={org ?? undefined} style={{ width: size, height: size, fontSize: Math.round(size * 0.45) }} aria-hidden>{initials(org ?? '?')}</span>
}

function ranked(board: Board, metric: string, models: Map<string, ModelRec>, bestOnly: boolean): Row[] {
  const seen = new Set<string>()
  const rows = board.entries.filter(e => typeof e.scores[metric] === 'number')
    .map(e => ({ e, m: models.get(e.model), score: e.scores[metric], rank: 0, weights: (models.get(e.model)?.weights ?? 'unknown') as Weights }))
    .sort((a, b) => b.score - a.score || a.e.label.localeCompare(b.e.label))
    .filter(r => !bestOnly || (!seen.has(r.e.model) && !!seen.add(r.e.model)))
  rows.forEach((r, i) => { r.rank = i > 0 && rows[i - 1].score === r.score ? rows[i - 1].rank : i + 1 })
  return rows
}

function frontier(points: Row[]) {
  const sorted = [...points].sort((a, b) => a.e.cost! - b.e.cost! || b.score - a.score)
  const out: Row[] = []
  for (const p of sorted) if (!out.length || p.score > out[out.length - 1].score) out.push(p)
  return out
}

function Weight({ r }: { r: Row }) {
  return <span className={`bd-w bd-w-${r.weights}`} title={r.m ? `${WEIGHTS[r.weights]}: ${BASIS[r.m.weights_basis]}` : undefined}>{WEIGHTS[r.weights]}</span>
}

function Leaders({ boards, selected, benchmarks, models, onPick }: { boards: Board[]; selected: Board; benchmarks: Map<string, BoardBenchmark>; models: Map<string, ModelRec>; onPick: (id: string) => void }) {
  return <ul className="bd-leaders" aria-label="Leader on each benchmark">
    {boards.map(b => {
      const info = benchmarks.get(b.benchmark_id)
      const top = ranked(b, b.metrics[0].key, models, true)[0]
      return <li key={b.benchmark_id}><button type="button" aria-pressed={b === selected} onClick={() => onPick(b.benchmark_id)}>
        <span className="bd-leader-board">{info?.name}{info?.results_status === 'archived' ? ' · archived' : ''}</span>
        {top && <>
          <span className="bd-leader-model"><Logo org={top.m?.org} size={20} /><b>{rowName(top)}</b></span>
          <span className="bd-leader-score"><strong>{pct(top.score)}</strong><span>{b.metrics[0].label}</span></span>
        </>}
      </button></li>
    })}
  </ul>
}

function RankList({ rows, metric, showAll, showCost }: { rows: Row[]; metric: string; showAll: boolean; showCost: boolean }) {
  const shown = showAll ? rows : rows.slice(0, TOP)
  if (!shown.length) return <p className="bd-empty">No models match this filter.</p>
  const values = shown.flatMap(r => [r.score, ...(r.e.ci?.[metric] ?? [])])
  const lo = Math.max(0, Math.floor((Math.min(...values) - 5) / 10) * 10)
  const hi = Math.min(100, Math.ceil((Math.max(...values) + 1) / 10) * 10)
  const at = (v: number) => `${Math.max(0, Math.min(100, (v - lo) / (hi - lo) * 100))}%`
  const mid = (lo + hi) / 2
  return <div className={`bd-rank-list${showCost ? ' has-cost' : ''}`}>
    <div className="bd-rank-head" aria-hidden>
      <span>#</span><span>Model</span>
      <span className="bd-axis-ticks"><i style={{ left: 0 }}>{lo}%</i><i style={{ left: '50%' }}>{Number(mid.toFixed(1))}%</i><i style={{ left: '100%' }}>{hi}%</i></span>
      <span className="num">Score</span>{showCost && <span className="num">Cost</span>}<span>Weights</span>
    </div>
    <ol aria-label="Ranked scores">
      {shown.map(r => {
        const ci = r.e.ci?.[metric]
        return <li key={rowKey(r)} className={r.rank <= 3 ? `bd-top bd-top-${r.rank}` : undefined}>
          <span className="bd-rank">{r.rank}</span>
          <span className="bd-model" title={`${entryName(r.e)}${r.m?.org ? ` · ${r.m.org}` : ''}`}><Logo org={r.m?.org} /><b>{rowName(r)}</b>{r.e.config && <em>{r.e.config}</em>}</span>
          <span className="bd-track">
            <span className="bd-fill" style={{ width: at(r.score) }} />
            {ci && <span className="bd-ci" style={{ left: at(ci[0]), width: `calc(${at(ci[1])} - ${at(ci[0])})` }} title={`95% interval ${pct(ci[0])}–${pct(ci[1])}`} />}
          </span>
          <span className="bd-score num">{pct(r.score)}{ci && <small>{pct(ci[0])}–{pct(ci[1])}</small>}</span>
          {showCost && <span className="num bd-cost">{r.e.cost !== null && r.e.cost > 0 ? money(r.e.cost) : '—'}</span>}
          <Weight r={r} />
        </li>
      })}
    </ol>
    {lo > 0 && <p className="bd-axis-note">Bars start at {lo}% so close scores are easier to tell apart.</p>}
  </div>
}

function Scatter({ rows, costLabel, metricLabel, hover, setHover }: { rows: Row[]; costLabel: string; metricLabel: string; hover: Row | null; setHover: (r: Row | null) => void }) {
  const pts = rows.filter(r => r.e.cost !== null && r.e.cost > 0)
  const front = frontier(pts)
  const W = 760, H = 440, L = 56, R = 24, T = 22, B = 48
  const costs = pts.map(p => p.e.cost!)
  const x0 = Math.log10(Math.min(...costs) / 1.4), x1 = Math.log10(Math.max(...costs) * 1.4)
  const scores = pts.map(p => p.score)
  const y0 = Math.max(0, Math.floor((Math.min(...scores) - 2) / 10) * 10), y1 = Math.min(100, Math.ceil((Math.max(...scores) + 2) / 10) * 10)
  const sx = (c: number) => L + (Math.log10(c) - x0) / (x1 - x0) * (W - L - R)
  const sy = (s: number) => T + (1 - (s - y0) / (y1 - y0)) * (H - T - B)
  const xticks = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100].filter(t => Math.log10(t) >= x0 && Math.log10(t) <= x1)
  const yticks = Array.from({ length: (y1 - y0) / 10 + 1 }, (_, i) => y0 + i * 10)
  const onFront = new Set(front)
  const MR = 13, LH = 17
  const placed = front.map(p => ({ x: sx(p.e.cost!) - MR, y: sy(p.score) - MR, w: MR * 2, h: MR * 2 }))
  const free = (b: { x: number; y: number; w: number; h: number }) => b.x >= L && b.x + b.w <= W - R && b.y >= 0 &&
    placed.every(q => b.x >= q.x + q.w || q.x >= b.x + b.w || b.y >= q.y + q.h || q.y >= b.y + b.h)
  const labels = [...front].sort((a, b) => b.score - a.score).flatMap(p => {
    const text = rowName(p), w = text.length * 6 + 12, cx = sx(p.e.cost!), cy = sy(p.score)
    const spots = [
      { x: cx - w / 2, y: cy - MR - LH - 3 }, { x: cx - w / 2, y: cy + MR + 3 },
      { x: cx + MR + 4, y: cy - LH / 2 }, { x: cx - MR - 4 - w, y: cy - LH / 2 },
    ]
    for (const b of spots.map(s => ({ ...s, w, h: LH }))) {
      if (free(b)) {
        placed.push(b)
        return [{ p, text, ...b }]
      }
    }
    return []
  })
  const hoverProps = (p: Row) => ({ onMouseEnter: () => setHover(p), onMouseLeave: () => setHover(null), onFocus: () => setHover(p), onBlur: () => setHover(null) })
  return <figure className="bd-scatter">
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${metricLabel} versus ${costLabel}, with the cost-performance frontier`}>
      <rect x={L} y={T} width={(W - L - R) / 2} height={(H - T - B) / 2} className="bd-quad" />
      <text x={L + 8} y={T + 16} className="bd-quad-label">Higher score, lower cost</text>
      {yticks.map(t => <g key={t}><line x1={L} x2={W - R} y1={sy(t)} y2={sy(t)} className="bd-grid" /><text x={L - 8} y={sy(t) + 4} textAnchor="end" className="bd-tick">{t}%</text></g>)}
      {xticks.map(t => <g key={t}><line x1={sx(t)} x2={sx(t)} y1={T} y2={H - B} className="bd-grid" /><text x={sx(t)} y={H - B + 18} textAnchor="middle" className="bd-tick">${t}</text></g>)}
      <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="bd-axis">{costLabel} (log scale)</text>
      <text x={14} y={(T + H - B) / 2} textAnchor="middle" transform={`rotate(-90 14 ${(T + H - B) / 2})`} className="bd-axis">{metricLabel}</text>
      <polyline points={front.map(p => `${sx(p.e.cost!)},${sy(p.score)}`).join(' ')} className="bd-front" />
      {pts.filter(p => !onFront.has(p)).map(p => <circle key={rowKey(p)} cx={sx(p.e.cost!)} cy={sy(p.score)} r={p === hover ? 6.5 : 4.5}
        className={`bd-dot bd-fill-${p.weights}${p === hover ? ' is-hover' : ''}`} tabIndex={0} {...hoverProps(p)}>
        <title>{`${entryName(p.e)}: ${pct(p.score)} at ${money(p.e.cost!)}`}</title>
      </circle>)}
      {front.map(p => {
        const cx = sx(p.e.cost!), cy = sy(p.score), org = p.m?.org
        return <g key={`m${rowKey(p)}`} className={`bd-mark${p === hover ? ' is-hover' : ''}`} tabIndex={0} {...hoverProps(p)}>
          <title>{`${entryName(p.e)}: ${pct(p.score)} at ${money(p.e.cost!)}`}</title>
          <circle cx={cx} cy={cy} r={MR} className={`bd-mark-ring bd-ring-${p.weights}`} />
          {org && LOGOS.has(orgSlug(org))
            ? <image href={`/logos/${orgSlug(org)}.svg`} x={cx - 8} y={cy - 8} width={16} height={16} />
            : <text x={cx} y={cy + 3.5} textAnchor="middle" className="bd-mark-initials">{initials(org ?? p.e.label)}</text>}
        </g>
      })}
      {labels.map(l => <g key={`l${rowKey(l.p)}`} className="bd-pill">
        <rect x={l.x} y={l.y} width={l.w} height={l.h} rx={3} />
        <text x={l.x + l.w / 2} y={l.y + 12} textAnchor="middle">{l.text}</text>
      </g>)}
      {hover && pts.includes(hover) && !labels.some(l => l.p === hover) && <text x={sx(hover.e.cost!) + (onFront.has(hover) ? MR + 4 : 9)} y={sy(hover.score) - 8} className="bd-dot-label bd-dot-label-hover">{rowName(hover)}</text>}
    </svg>
    <figcaption>
      <span className="bd-key"><i className="bd-ring-closed" />Closed</span><span className="bd-key"><i className="bd-ring-open" />Open weights</span><span className="bd-key"><i className="bd-ring-unknown" />Weights not stated</span>
      <span>Logos mark the frontier. {pts.length} of {rows.length} models have a published cost.</span>
    </figcaption>
  </figure>
}

function CostList({ rows, hover, setHover }: { rows: Row[]; hover: Row | null; setHover: (r: Row | null) => void }) {
  const [q, setQ] = useState('')
  const pts = rows.filter(r => r.e.cost !== null && r.e.cost > 0)
  const front = new Set(frontier(pts))
  const shown = pts.filter(r => !q || `${entryName(r.e)} ${r.m?.org ?? ''}`.toLowerCase().includes(q.toLowerCase()))
  return <div className="bd-cost-list">
    <label className="bd-cost-search"><Search size={14} aria-hidden /><span className="sr-only">Find a model on the chart</span><input type="search" placeholder="Find a model" value={q} onChange={e => setQ(e.target.value)} /></label>
    <ul>
      {shown.map(r => <li key={rowKey(r)}><button type="button" className={r === hover ? 'is-hover' : undefined} onMouseEnter={() => setHover(r)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(r)} onBlur={() => setHover(null)}>
        <Logo org={r.m?.org} size={16} /><span className="bd-cost-name">{rowName(r)}{r.e.config && <em>{r.e.config}</em>}{front.has(r) && <span className="bd-front-tag" title="On the frontier: no model scores higher for less">Frontier</span>}</span>
        <span className="num">{pct(r.score)}<small>{money(r.e.cost!)}</small></span>
      </button></li>)}
      {!shown.length && <li className="bd-empty">No match.</li>}
    </ul>
  </div>
}

function heat(rank: number, n: number) {
  const p = rank / n
  return p <= 0.1 ? 1 : p <= 0.25 ? 2 : p <= 0.5 ? 3 : 4
}

function Coverage({ boards, benchmarks, models, filter, onPick }: { boards: Board[]; benchmarks: Map<string, BoardBenchmark>; models: Map<string, ModelRec>; filter: Filter; onPick: (id: string) => void }) {
  const [showAll, setShowAll] = useState(false)
  const cols = boards.map(b => {
    const rows = ranked(b, b.metrics[0].key, models, true)
    return { b, best: new Map(rows.map(r => [r.e.model, r])), n: rows.length }
  })
  const ids = [...new Set(cols.flatMap(c => [...c.best.keys()]))]
    .filter(id => filter === 'all' || models.get(id)?.weights === filter)
    .map(id => ({ id, hits: cols.filter(c => c.best.has(id)).length, top: Math.min(...cols.map(c => c.best.get(id)?.rank ?? Infinity)) }))
    .filter(r => r.hits >= 2)
    .sort((a, b) => b.hits - a.hits || a.top - b.top || a.id.localeCompare(b.id))
  const shown = showAll ? ids : ids.slice(0, 20)
  if (cols.length < 2) return null
  return <section className="bd-coverage" aria-labelledby="coverage">
    <h3 id="coverage">Where each model places</h3>
    <p className="bd-explain">Each cell is the model's rank among the models on that board, using its best configuration. Darker means nearer the top. We don't add these up into one score: the boards use different tasks, graders and metrics. Showing models listed on at least two boards.</p>
    <p className="bd-heat-legend" aria-hidden><span><i className="bd-heat-1" />Top 10%</span><span><i className="bd-heat-2" />Top 25%</span><span><i className="bd-heat-3" />Top half</span><span><i className="bd-heat-4" />Lower half</span><span><i className="bd-heat-none" />Not on board</span></p>
    <div className="bd-table-wrap"><table className="bd-table bd-matrix">
      <thead><tr><th>Model</th>{cols.map(c => <th key={c.b.benchmark_id} className="num"><button type="button" onClick={() => onPick(c.b.benchmark_id)}>{benchmarks.get(c.b.benchmark_id)?.name}</button><span>{c.n} models</span></th>)}</tr></thead>
      <tbody>{shown.map(r => {
        const m = models.get(r.id)
        return <tr key={r.id}>
          <td><span className="bd-matrix-model"><Logo org={m?.org} size={16} /><b>{m?.name ?? r.id}</b></span></td>
          {cols.map(c => {
            const hit = c.best.get(r.id)
            return <td key={c.b.benchmark_id} className={`num bd-heat-${hit ? heat(hit.rank, c.n) : 'none'}`} title={hit ? `${entryName(hit.e)}: ${pct(hit.score)}, #${hit.rank} of ${c.n}` : 'Not on this board'}>{hit ? `#${hit.rank}` : '—'}</td>
          })}
        </tr>
      })}</tbody>
    </table></div>
    {ids.length > 20 && <button type="button" className="bd-more" onClick={() => setShowAll(v => !v)}>{showAll ? 'Show fewer' : `Show all ${ids.length} models`}</button>}
  </section>
}

export default function BenchmarkBoards({ boards, models: modelList, benchmarks: benchmarkList }: { boards: Board[]; models: ModelRec[]; benchmarks: BoardBenchmark[] }) {
  const [params, setParams] = useSearchParams()
  const [showAll, setShowAll] = useState(false)
  const [hover, setHover] = useState<Row | null>(null)
  const models = useMemo(() => new Map(modelList.map(m => [m.id, m])), [modelList])
  const benchmarks = useMemo(() => new Map(benchmarkList.map(b => [b.id, b])), [benchmarkList])
  const areas = AREAS.filter(([key]) => boards.some(b => benchmarks.get(b.benchmark_id)?.domains.includes(key)))
  const area = params.get('area') ?? ''
  const inArea = boards.filter(b => !area || benchmarks.get(b.benchmark_id)?.domains.includes(area))
  const board = inArea.find(b => b.benchmark_id === params.get('board')) ?? inArea[0]
  const filter = (['open', 'closed'].includes(params.get('models') ?? '') ? params.get('models') : 'all') as Filter
  const allConfigs = params.get('configs') === 'all'
  const metric = board?.metrics.find(m => m.key === params.get('metric')) ?? board?.metrics[0]
  const all = useMemo(() => board && metric ? ranked(board, metric.key, models, !allConfigs) : [], [board, metric, models, allConfigs])
  const rows = all.filter(r => filter === 'all' || r.weights === filter)
  const costPoints = rows.filter(r => r.e.cost !== null && r.e.cost > 0).length
  const costCoverage = !!board?.cost_label && rows.length > 0 && costPoints * 2 >= rows.length
  const set = (next: Record<string, string | null>) => {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(next)) { if (v) p.set(k, v); else p.delete(k) }
    setParams(p, { replace: true })
    setShowAll(false)
    setHover(null)
  }
  if (!board || !metric) return null
  const bm = benchmarks.get(board.benchmark_id)
  const modelCount = new Set(board.entries.map(e => e.model)).size
  const configCount = board.entries.length
  const unit = allConfigs ? 'configurations' : 'models'
  const counts = { all: all.length, open: all.filter(r => r.weights === 'open').length, closed: all.filter(r => r.weights === 'closed').length }
  const unstated = all.filter(r => r.weights === 'unknown').length
  const definition = bm?.metric_definitions?.[metric.key]
  const fresh = board.as_of ? `Updated ${dateLabel(board.as_of)}` : `Checked ${dateLabel(board.retrieved)}`
  const freshTitle = board.as_of ? `Date shown by the publisher. We retrieved the page on ${dateLabel(board.retrieved)}.` : `The source shows no date. We retrieved it on ${dateLabel(board.retrieved)}.`
  return <section className="bd" aria-labelledby="boards">
    <nav className="bd-areas" aria-label="Area">
      <button type="button" aria-pressed={!area} onClick={() => set({ area: null, board: null, metric: null })}>All areas <span>{boards.length}</span></button>
      {areas.map(([key, label]) => <button type="button" key={key} aria-pressed={area === key} onClick={() => set({ area: key, board: null, metric: null })}>{label} <span>{boards.filter(b => benchmarks.get(b.benchmark_id)?.domains.includes(key)).length}</span></button>)}
    </nav>
    <h2 id="boards" className="sr-only">Model leaderboards</h2>
    <p className="bd-explain">The top model on each benchmark, in that publisher's own metric. Pick one to see its full ranking. Boards can't be compared with each other.</p>
    <Leaders boards={inArea} selected={board} benchmarks={benchmarks} models={models} onPick={id => set({ board: id, metric: null })} />

    <article className="bd-panel" aria-labelledby="board-title">
      <header className="bd-panel-head">
        <div>
          <h3 id="board-title">{bm?.name}</h3>
          <p className="bd-sub">{bm?.publisher} · {modelCount} models{configCount > modelCount ? ` (${configCount} configurations)` : ''} · <span title={freshTitle}>{fresh}</span>{bm?.results_status === 'archived' ? ' · archived by publisher' : ''}</p>
        </div>
        <Ext href={board.source_url}>{SOURCE[bm?.results?.source_type ?? 'first_party']} source</Ext>
      </header>
      {bm?.summary && <p className="bd-what">{bm.summary}</p>}
      <p className="bd-metric-def"><b>{metric.label}</b>{definition ? `: ${definition}` : '.'} Higher is better.</p>
      <div className="bd-controls">
        <div className="bd-seg" role="group" aria-label="Model weights">
          {(['all', 'open', 'closed'] as Filter[]).map(f => <button type="button" key={f} aria-pressed={filter === f} disabled={f !== 'all' && !counts[f]} onClick={() => set({ models: f === 'all' ? null : f })}>{f === 'all' ? `All ${unit}` : WEIGHTS[f]} <span>{counts[f]}</span></button>)}
        </div>
        {board.metrics.length > 1 && <div className="bd-seg" role="group" aria-label="Metric">
          {board.metrics.map(m => <button type="button" key={m.key} aria-pressed={m === metric} onClick={() => set({ metric: m.key === board.metrics[0].key ? null : m.key })}>{m.label}</button>)}
        </div>}
        {configCount > modelCount && <div className="bd-seg" role="group" aria-label="Configurations">
          <button type="button" aria-pressed={!allConfigs} onClick={() => set({ configs: null })} title="Each model appears once, at its best-scoring configuration">Best per model</button>
          <button type="button" aria-pressed={allConfigs} onClick={() => set({ configs: 'all' })} title="List every configuration the publisher ranked, such as reasoning-effort settings">All configurations</button>
        </div>}
      </div>
      <RankList rows={rows} metric={metric.key} showAll={showAll} showCost={costCoverage} />
      <div className="bd-after-list">
        {rows.length > TOP && <button type="button" className="bd-more" onClick={() => setShowAll(v => !v)}>{showAll ? `Show top ${TOP}` : `Show all ${rows.length} ${unit}`}</button>}
        {filter === 'all' && unstated > 0 && <span className="p-fine">{unstated} {unit} with unstated weights appear only under All.</span>}
      </div>
      {bm?.results?.note && <p className="p-fine bd-note">{bm.results.note}</p>}
    </article>

    {costCoverage && costPoints >= MIN_COST_POINTS && <article className="bd-panel bd-tradeoff" aria-labelledby="tradeoff">
      <h3 id="tradeoff">{metric.label} vs {board.cost_label}</h3>
      <p className="bd-explain">Top left is best: a higher score for less money. The line joins models that no other model beats on both score and cost.</p>
      <div className="bd-tradeoff-grid">
        <Scatter rows={rows} costLabel={board.cost_label!} metricLabel={metric.label} hover={hover} setHover={setHover} />
        <CostList rows={rows} hover={hover} setHover={setHover} />
      </div>
    </article>}

    <Coverage boards={inArea} benchmarks={benchmarks} models={models} filter={filter} onPick={id => set({ board: id, metric: null })} />
  </section>
}
