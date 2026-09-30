import { ReactNode, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'

export type Weights = 'open' | 'closed' | 'unknown'
export interface ModelRec { id: string; name: string; org: string | null; weights: Weights; weights_basis: 'publisher' | 'family' | 'conflict' | 'none'; weights_reported: Record<string, 'open' | 'closed'> }
export interface BoardEntry { model: string; label: string; config: string | null; scores: Record<string, number>; ci?: Record<string, [number, number]>; cost: number | null }
export interface Board { benchmark_id: string; source_url: string; adapter: string; as_of: string | null; retrieved: string; metrics: { key: string; label: string; unit: string }[]; cost_label: string | null; entries: BoardEntry[] }
export interface BoardBenchmark { id: string; name: string; publisher: string; domains: string[]; results_status: string; relevance: string; results: { source_type: string; note: string | null } | null }

type Filter = 'all' | 'open' | 'closed'
interface Row { e: BoardEntry; m: ModelRec | undefined; score: number; rank: number; weights: Weights }

const AREAS: [string, string][] = [['accounting', 'Accounting'], ['tax', 'Tax'], ['financial_analysis', 'Financial analysis'], ['investment_banking', 'Investment banking']]
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

function Ext({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href} target="_blank" rel="noreferrer">{children}<ArrowUpRight size={12} aria-hidden /></a>
}

function ranked(board: Board, metric: string, models: Map<string, ModelRec>): Row[] {
  const rows = board.entries.filter(e => typeof e.scores[metric] === 'number')
    .map(e => ({ e, m: models.get(e.model), score: e.scores[metric], rank: 0, weights: (models.get(e.model)?.weights ?? 'unknown') as Weights }))
    .sort((a, b) => b.score - a.score || a.e.label.localeCompare(b.e.label))
  rows.forEach((r, i) => { r.rank = i > 0 && rows[i - 1].score === r.score ? rows[i - 1].rank : i + 1 })
  return rows
}

function frontier(points: Row[]) {
  const sorted = [...points].sort((a, b) => a.e.cost! - b.e.cost! || b.score - a.score)
  const out: Row[] = []
  for (const p of sorted) if (!out.length || p.score > out[out.length - 1].score) out.push(p)
  return out
}

function Weight({ w }: { w: Weights }) {
  return <span className={`bd-w bd-w-${w}`}>{WEIGHTS[w]}</span>
}

function Bars({ rows, metric, showAll }: { rows: Row[]; metric: string; showAll: boolean }) {
  const shown = showAll ? rows : rows.slice(0, TOP)
  return <ol className="bd-bars" aria-label="Ranked scores">
    {shown.map(r => {
      const ci = r.e.ci?.[metric]
      return <li key={`${r.e.label}|${r.e.config}`}>
        <span className="bd-rank">{r.rank}</span>
        <span className="bd-model" title={entryName(r.e)}>{r.m?.name ?? r.e.label}{r.e.config && <em>{r.e.config}</em>}</span>
        <span className="bd-track">
          <span className={`bd-fill bd-fill-${r.weights}`} style={{ width: `${Math.min(r.score, 100)}%` }} />
          {ci && <span className="bd-ci" style={{ left: `${ci[0]}%`, width: `${Math.max(ci[1] - ci[0], 0.3)}%` }} title={`95% interval ${pct(ci[0])}–${pct(ci[1])}`} />}
        </span>
        <span className="bd-score">{pct(r.score)}</span>
      </li>
    })}
  </ol>
}

function Scatter({ rows, costLabel, metricLabel }: { rows: Row[]; costLabel: string; metricLabel: string }) {
  const [hover, setHover] = useState<Row | null>(null)
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
    const text = p.m?.name ?? p.e.label, w = text.length * 6 + 12, cx = sx(p.e.cost!), cy = sy(p.score)
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
  return <figure className="bd-scatter">
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${metricLabel} versus ${costLabel}, with the cost-performance frontier`}>
      <rect x={L} y={T} width={(W - L - R) / 2} height={(H - T - B) / 2} className="bd-quad" />
      <text x={L + 8} y={T + 16} className="bd-quad-label">Higher score, lower cost</text>
      {yticks.map(t => <g key={t}><line x1={L} x2={W - R} y1={sy(t)} y2={sy(t)} className="bd-grid" /><text x={L - 8} y={sy(t) + 4} textAnchor="end" className="bd-tick">{t}%</text></g>)}
      {xticks.map(t => <g key={t}><line x1={sx(t)} x2={sx(t)} y1={T} y2={H - B} className="bd-grid" /><text x={sx(t)} y={H - B + 18} textAnchor="middle" className="bd-tick">${t}</text></g>)}
      <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="bd-axis">{costLabel} (log scale)</text>
      <text x={14} y={(T + H - B) / 2} textAnchor="middle" transform={`rotate(-90 14 ${(T + H - B) / 2})`} className="bd-axis">{metricLabel}</text>
      <polyline points={front.map(p => `${sx(p.e.cost!)},${sy(p.score)}`).join(' ')} className="bd-front" />
      {pts.filter(p => !onFront.has(p)).map(p => <circle key={`${p.e.label}|${p.e.config}`} cx={sx(p.e.cost!)} cy={sy(p.score)} r={4.5}
        className={`bd-dot bd-fill-${p.weights}`} tabIndex={0}
        onMouseEnter={() => setHover(p)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(p)} onBlur={() => setHover(null)}>
        <title>{`${entryName(p.e)}: ${pct(p.score)} at ${money(p.e.cost!)}`}</title>
      </circle>)}
      {front.map(p => {
        const cx = sx(p.e.cost!), cy = sy(p.score), org = p.m?.org
        return <g key={`m${p.e.label}|${p.e.config}`} className="bd-mark" tabIndex={0}
          onMouseEnter={() => setHover(p)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(p)} onBlur={() => setHover(null)}>
          <title>{`${entryName(p.e)}: ${pct(p.score)} at ${money(p.e.cost!)}`}</title>
          <circle cx={cx} cy={cy} r={MR} className={`bd-mark-ring bd-ring-${p.weights}`} />
          {org && LOGOS.has(orgSlug(org))
            ? <image href={`/logos/${orgSlug(org)}.svg`} x={cx - 8} y={cy - 8} width={16} height={16} />
            : <text x={cx} y={cy + 3.5} textAnchor="middle" className="bd-mark-initials">{initials(org ?? p.e.label)}</text>}
        </g>
      })}
      {labels.map(l => <g key={`l${l.p.e.label}|${l.p.e.config}`} className="bd-pill">
        <rect x={l.x} y={l.y} width={l.w} height={l.h} rx={3} />
        <text x={l.x + l.w / 2} y={l.y + 12} textAnchor="middle">{l.text}</text>
      </g>)}
      {hover && !labels.some(l => l.p === hover) && <text x={sx(hover.e.cost!) + (onFront.has(hover) ? MR + 4 : 9)} y={sy(hover.score) - 8} className="bd-dot-label bd-dot-label-hover">{entryName(hover.e)}</text>}
    </svg>
    <figcaption>{hover ? <><b>{entryName(hover.e)}</b> · {pct(hover.score)} · {money(hover.e.cost!)}</> : <>The line joins models no other model beats on both score and cost. {pts.length} of {rows.length} models have a published cost.</>}</figcaption>
  </figure>
}

function Table({ rows, metric, costLabel, showAll }: { rows: Row[]; metric: string; costLabel: string | null; showAll: boolean }) {
  const shown = showAll ? rows : rows.slice(0, TOP)
  return <div className="bd-table-wrap"><table className="bd-table">
    <thead><tr><th>Rank</th><th>Model</th><th className="num">Score</th>{costLabel && <th className="num">Cost</th>}<th>Organization</th><th>Weights</th></tr></thead>
    <tbody>{shown.map(r => {
      const ci = r.e.ci?.[metric]
      return <tr key={`${r.e.label}|${r.e.config}`}>
        <td className="bd-rank">{r.rank}</td>
        <td><b>{r.m?.name ?? r.e.label}</b>{r.e.config && <span className="bd-config">{r.e.config}</span>}</td>
        <td className="num">{pct(r.score)}{ci && <span className="bd-pm">{pct(ci[0])}–{pct(ci[1])}</span>}</td>
        {costLabel && <td className="num">{r.e.cost !== null ? money(r.e.cost) : '—'}</td>}
        <td>{r.m?.org ?? '—'}</td>
        <td><span title={r.m ? `${WEIGHTS[r.weights]}: ${BASIS[r.m.weights_basis]}` : undefined}><Weight w={r.weights} /></span></td>
      </tr>
    })}</tbody>
  </table></div>
}

function Coverage({ boards, benchmarks, models, filter, onPick }: { boards: Board[]; benchmarks: Map<string, BoardBenchmark>; models: Map<string, ModelRec>; filter: Filter; onPick: (id: string) => void }) {
  const [showAll, setShowAll] = useState(false)
  const cols = boards.map(b => {
    const rows = ranked(b, b.metrics[0].key, models)
    const best = new Map<string, Row>()
    for (const r of rows) if (!best.has(r.e.model)) best.set(r.e.model, r)
    return { b, best, n: rows.length }
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
    <p className="p-fine">Each cell is the model's rank on that publisher's board, using its best listed configuration. We don't combine these into one score: the boards use different tasks, graders and metrics. Models listed on at least two boards.</p>
    <div className="bd-table-wrap"><table className="bd-table bd-matrix">
      <thead><tr><th>Model</th>{cols.map(c => <th key={c.b.benchmark_id} className="num"><button type="button" onClick={() => onPick(c.b.benchmark_id)}>{benchmarks.get(c.b.benchmark_id)?.name}</button><span>of {c.n}</span></th>)}</tr></thead>
      <tbody>{shown.map(r => <tr key={r.id}>
        <td><i className={`bd-swatch bd-fill-${models.get(r.id)?.weights ?? 'unknown'}`} title={WEIGHTS[models.get(r.id)?.weights ?? 'unknown']} /><b>{models.get(r.id)?.name ?? r.id}</b></td>
        {cols.map(c => {
          const hit = c.best.get(r.id)
          return <td key={c.b.benchmark_id} className="num">{hit ? <span className={hit.rank <= 3 ? 'bd-podium' : undefined} title={`${entryName(hit.e)}: ${pct(hit.score)}`}>#{hit.rank}</span> : <span className="bd-none">—</span>}</td>
        })}
      </tr>)}</tbody>
    </table></div>
    {ids.length > 20 && <button type="button" className="bd-more" onClick={() => setShowAll(v => !v)}>{showAll ? 'Show fewer' : `Show all ${ids.length} models`}</button>}
  </section>
}

export default function BenchmarkBoards({ boards, models: modelList, benchmarks: benchmarkList }: { boards: Board[]; models: ModelRec[]; benchmarks: BoardBenchmark[] }) {
  const [params, setParams] = useSearchParams()
  const [showAll, setShowAll] = useState(false)
  const models = useMemo(() => new Map(modelList.map(m => [m.id, m])), [modelList])
  const benchmarks = useMemo(() => new Map(benchmarkList.map(b => [b.id, b])), [benchmarkList])
  const areas = AREAS.filter(([key]) => boards.some(b => benchmarks.get(b.benchmark_id)?.domains.includes(key)))
  const area = params.get('area') ?? ''
  const inArea = boards.filter(b => !area || benchmarks.get(b.benchmark_id)?.domains.includes(area))
  const board = inArea.find(b => b.benchmark_id === params.get('board')) ?? inArea[0]
  const filter = (['open', 'closed'].includes(params.get('models') ?? '') ? params.get('models') : 'all') as Filter
  const metric = board?.metrics.find(m => m.key === params.get('metric')) ?? board?.metrics[0]
  const all = useMemo(() => board && metric ? ranked(board, metric.key, models) : [], [board, metric, models])
  const rows = all.filter(r => filter === 'all' || r.weights === filter)
  const costPoints = rows.filter(r => r.e.cost !== null && r.e.cost > 0).length
  const canScatter = !!board?.cost_label && costPoints >= MIN_COST_POINTS
  const view = params.get('view') === 'cost' && canScatter ? 'cost' : 'rank'
  const set = (next: Record<string, string | null>) => {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(next)) { if (v) p.set(k, v); else p.delete(k) }
    setParams(p, { replace: true })
    setShowAll(false)
  }
  if (!board || !metric) return null
  const bm = benchmarks.get(board.benchmark_id)
  const counts = { all: all.length, open: all.filter(r => r.weights === 'open').length, closed: all.filter(r => r.weights === 'closed').length }
  const unstated = all.filter(r => r.weights === 'unknown').length
  return <section className="bd" aria-labelledby="boards">
    <div className="bd-heading">
      <p className="p-eyebrow">Model leaderboards</p>
      <h2 id="boards">How models score on each benchmark</h2>
      <p>Each board shows the publisher's own results for that benchmark, in their metric. Scores are copied from the source and not re-run by us. Boards can't be compared with each other directly.</p>
    </div>
    <nav className="bd-areas" aria-label="Area">
      <button type="button" aria-pressed={!area} onClick={() => set({ area: null, board: null, metric: null, view: null })}>All <span>{boards.length}</span></button>
      {areas.map(([key, label]) => <button type="button" key={key} aria-pressed={area === key} onClick={() => set({ area: key, board: null, metric: null, view: null })}>{label} <span>{boards.filter(b => benchmarks.get(b.benchmark_id)?.domains.includes(key)).length}</span></button>)}
    </nav>
    <div className="bd-layout">
      <ul className="bd-picker" aria-label="Benchmark">
        {inArea.map(b => {
          const info = benchmarks.get(b.benchmark_id)
          const top = ranked(b, b.metrics[0].key, models)[0]
          return <li key={b.benchmark_id}><button type="button" aria-pressed={b === board} onClick={() => set({ board: b.benchmark_id, metric: null, view: null })}>
            <strong>{info?.name}</strong><span>{info?.publisher}</span>
            <small>{top && `#1 ${top.e.label} · ${pct(top.score)}`}{info?.results_status === 'archived' ? ' · archived' : ''}</small>
          </button></li>
        })}
      </ul>
      <div className="bd-panel">
        <header className="bd-panel-head">
          <div>
            <h3>{bm?.name}</h3>
            <p>{bm?.publisher} · {new Set(all.map(r => r.e.model)).size} models · {board.as_of ? `updated ${dateLabel(board.as_of)}` : `no date on source; retrieved ${dateLabel(board.retrieved)}`}{bm?.results_status === 'archived' ? ' · archived by publisher' : ''}</p>
          </div>
          <Ext href={board.source_url}>{SOURCE[bm?.results?.source_type ?? 'first_party']} source</Ext>
        </header>
        <div className="bd-controls">
          <div className="bd-seg" role="group" aria-label="Model weights">
            {(['all', 'open', 'closed'] as Filter[]).map(f => <button type="button" key={f} aria-pressed={filter === f} disabled={f !== 'all' && !counts[f]} onClick={() => set({ models: f === 'all' ? null : f })}>{f === 'all' ? 'All models' : WEIGHTS[f]} <span>{counts[f]}</span></button>)}
          </div>
          {board.metrics.length > 1 && <div className="bd-seg" role="group" aria-label="Metric">
            {board.metrics.map(m => <button type="button" key={m.key} aria-pressed={m === metric} onClick={() => set({ metric: m.key === board.metrics[0].key ? null : m.key })}>{m.label}</button>)}
          </div>}
          <div className="bd-seg" role="group" aria-label="View">
            <button type="button" aria-pressed={view === 'rank'} onClick={() => set({ view: null })}>Ranking</button>
            <button type="button" aria-pressed={view === 'cost'} disabled={!canScatter} title={canScatter ? undefined : board.cost_label ? 'Too few models with a published cost' : 'The publisher does not report cost'} onClick={() => set({ view: 'cost' })}>Score vs cost</button>
          </div>
        </div>
        {view === 'cost' && board.cost_label ? <Scatter rows={rows} costLabel={board.cost_label} metricLabel={metric.label} /> : <Bars rows={rows} metric={metric.key} showAll={showAll} />}
        <p className="bd-legend"><span><i className="bd-fill-closed" />Closed</span><span><i className="bd-fill-open" />Open weights</span><span><i className="bd-fill-unknown" />Weights not stated</span>{filter === 'all' && unstated > 0 && <span>{unstated} models with unstated weights appear only under All models.</span>}</p>
        <Table rows={rows} metric={metric.key} costLabel={board.cost_label} showAll={showAll} />
        {rows.length > TOP && <button type="button" className="bd-more" onClick={() => setShowAll(v => !v)}>{showAll ? 'Show top 15' : `Show all ${rows.length} rows`}</button>}
        {bm?.results?.note && <p className="p-fine bd-note">{bm.results.note}</p>}
      </div>
    </div>
    <Coverage boards={inArea} benchmarks={benchmarks} models={models} filter={filter} onPick={id => set({ board: id, metric: null, view: null })} />
  </section>
}
