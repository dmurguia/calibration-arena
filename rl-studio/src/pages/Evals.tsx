import { Link } from 'react-router-dom'
import { ArrowRight, Loader2, Play } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis, LabelList } from 'recharts'
import { BASELINE_STEPS, EVAL_CATEGORIES, HERO_CLAIM, MODELS, TRAINED_STEPS } from '../lib/data'
import { DEMO_SPEED, progressOf, runProgress, taskCounts, useDemo } from '../lib/store'
import { modelOf, runLeak } from '../lib/runs'
import { pct, rng } from '../lib/sim'
import { Badge, Button, Card, chartColors, cx, PageHeader, Progress, SectionTitle } from '../components/ui'
import { StepList } from './Traces'

function catScores(base: number, seed: number) {
  const r = rng(seed)
  return EVAL_CATEGORIES.map((c, i) => ({ cat: c.label, v: Math.min(0.98, Math.max(0.05, base + [0.12, -0.1, -0.08, 0.05, 0.08][i] + (r() - 0.5) * 0.06)) }))
}

export default function Evals() {
  const { s, set, now } = useDemo()
  const p = progressOf(s.baselineStartedAt, DEMO_SPEED.baselineMs, now)
  const done = p >= 1
  const trained = s.runs.filter((r) => runProgress(r, now) >= 1)
  const best = [...trained].sort((a, b) => b.finalScore - a.finalScore)[0]

  const rows = [
    ...MODELS.map((m) => ({ id: m.id, name: m.name, vendor: m.vendor, kind: m.kind as string, score: m.score, leak: m.leak, cost: m.costPerClaim, p50: m.p50, current: m.current })),
    ...trained.map((r) => {
      const m = modelOf(r)
      return { id: r.id, name: `${m.name} · ${r.id}`, vendor: 'Ford-owned checkpoint', kind: 'trained', score: r.finalScore, leak: runLeak(r), cost: m.costPerClaim * 1.25, p50: m.p50 + 1, current: false }
    }),
  ].sort((a, b) => b.score - a.score)

  const scatter = rows.map((r) => ({ x: r.cost, y: +(r.score * 100).toFixed(1), name: r.name.split(' · ')[0] + (r.kind === 'trained' ? ' (trained)' : ''), kind: r.kind }))
  const claudeCats = catScores(0.612, 3)
  const bestCats = best ? catScores(best.finalScore, 9) : null
  const catData = claudeCats.map((c, i) => ({ cat: c.cat, claude: +(c.v * 100).toFixed(1), trained: bestCats ? +(bestCats[i].v * 100).toFixed(1) : undefined }))

  return (
    <>
      <PageHeader
        eyebrow="Improve · Evaluations"
        title="Score every model on your environment"
        desc={`Held-out test split · ${taskCounts(s).test} claims · same tools, same grader. This is the number that decides what goes to production.`}
        actions={
          !s.baselineStartedAt ? <Button onClick={() => set({ baselineStartedAt: Date.now() })}><Play size={14} /> Run baseline on 6 models</Button>
            : done ? <Link to="/app/training/new"><Button>{trained.length ? 'Train another model' : 'Next: train a model'} <ArrowRight size={14} /></Button></Link>
            : <Button disabled><Loader2 size={14} className="animate-spin" /> Running…</Button>
        }
      />

      {!s.baselineStartedAt && (
        <Card className="grid-bg py-12 text-center">
          <div className="text-[17px] font-semibold">No evaluations yet</div>
          <div className="mx-auto mt-1 max-w-lg text-sm text-graphite">Run your current production model next to other frontier APIs and trainable open-weight models. It takes ~20 minutes and about $40 in credits (demo: 14 s).</div>
          <Button className="mt-5" onClick={() => set({ baselineStartedAt: Date.now() })}><Play size={14} /> Run baseline</Button>
        </Card>
      )}

      {s.baselineStartedAt && (
        <>
          <Card pad={false}>
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-hairline text-left text-[11px] uppercase tracking-wider text-graphite">
                  <th className="px-4 py-2.5 font-medium">#</th>
                  <th className="px-4 py-2.5 font-medium">Model</th>
                  <th className="px-4 py-2.5 font-medium">Task success</th>
                  <th className="px-4 py-2.5 text-right font-medium">Wrong approvals</th>
                  <th className="px-4 py-2.5 text-right font-medium">Cost / claim</th>
                  <th className="px-4 py-2.5 text-right font-medium">p50 latency</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const rp = Math.min(1, p * (1.6 - (i % 6) * 0.1))
                  const show = rp >= 1
                  return (
                    <tr key={r.id} className={cx('border-b border-hairline last:border-0', r.kind === 'trained' && 'bg-good-tint/40')}>
                      <td className="px-4 py-3 font-mono text-[12px] text-steel">{show ? i + 1 : '–'}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 font-medium">{r.name}{r.current && <Badge tone="leather">in production</Badge>}{r.kind === 'trained' && <Badge tone="good">yours</Badge>}{r.kind === 'open' && <Badge>trainable</Badge>}</div>
                        <div className="text-[12px] text-graphite">{r.vendor}</div>
                      </td>
                      <td className="w-[280px] px-4 py-3">
                        {show ? (
                          <div className="flex items-center gap-3">
                            <div className="h-2 flex-1 rounded-full bg-ink/10"><div className={cx('h-2 rounded-full', r.kind === 'trained' ? 'bg-good' : r.kind === 'open' ? 'bg-steel' : 'bg-ink')} style={{ width: `${r.score * 100}%` }} /></div>
                            <span className="w-12 text-right font-mono">{pct(r.score)}</span>
                          </div>
                        ) : <Progress value={rp} tone="leather" />}
                      </td>
                      <td className={cx('px-4 py-3 text-right font-mono', show && r.leak > 0.1 && 'text-bad')}>{show ? pct(r.leak) : '…'}</td>
                      <td className="px-4 py-3 text-right font-mono">{show ? `$${r.cost.toFixed(3)}` : '…'}</td>
                      <td className="px-4 py-3 text-right font-mono">{show ? `${r.p50}s` : '…'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Card>

          {done && (
            <div className="mt-6 grid grid-cols-2 gap-6">
              <Card>
                <SectionTitle>Quality vs cost</SectionTitle>
                <div className="h-64">
                  <ResponsiveContainer>
                    <ScatterChart margin={{ left: -10, right: 20, top: 10, bottom: 10 }}>
                      <CartesianGrid stroke={chartColors.grid} />
                      <XAxis type="number" dataKey="x" scale="log" domain={[0.01, 1]} ticks={[0.01, 0.03, 0.1, 0.3, 1]} tickFormatter={(v) => `$${v}`} name="cost / claim" tickLine={false} />
                      <YAxis type="number" dataKey="y" domain={[20, 90]} unit="%" tickLine={false} axisLine={false} />
                      <ZAxis range={[90, 90]} />
                      <Tooltip formatter={(v: number, n: string) => (n === 'cost / claim' ? `$${v}` : `${v}%`)} />
                      <Scatter data={scatter} isAnimationActive={false}>
                        {scatter.map((d) => <Cell key={d.name} fill={d.kind === 'trained' ? chartColors.good : d.kind === 'open' ? chartColors.steel : chartColors.ink} />)}
                        <LabelList dataKey="name" position="right" style={{ fontSize: 10.5, fill: '#656460' }} />
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
                <div className="text-[12.5px] text-graphite">{best ? 'Your trained checkpoint sits up and to the left: better than frontier, at a fraction of the cost.' : 'Open-weight models are 10–20× cheaper but start far behind. Training closes that gap on your task.'}</div>
              </Card>
              <Card>
                <SectionTitle>By skill</SectionTitle>
                <div className="h-64">
                  <ResponsiveContainer>
                    <BarChart data={catData} margin={{ left: -18, right: 8, top: 10 }}>
                      <CartesianGrid stroke={chartColors.grid} vertical={false} />
                      <XAxis dataKey="cat" tickLine={false} axisLine={false} />
                      <YAxis domain={[0, 100]} tickLine={false} axisLine={false} unit="%" />
                      <Tooltip />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="claude" name="Claude Sonnet 4.6 (prod)" fill={chartColors.ink} radius={[3, 3, 0, 0]} isAnimationActive={false} />
                      {best && <Bar dataKey="trained" name={`${best.id} (trained)`} fill={chartColors.good} radius={[3, 3, 0, 0]} isAnimationActive={false} />}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="text-[12.5px] text-graphite">Claude is weakest on labor ops and TSB citations — Ford-specific knowledge it can’t have.</div>
              </Card>
            </div>
          )}

          {done && best && (
            <div className="mt-6">
              <SectionTitle>Same claim, before and after · {HERO_CLAIM.id}</SectionTitle>
              <div className="grid grid-cols-2 gap-6">
                <Card><div className="mb-3 flex items-center justify-between text-[13px] font-medium">Claude Sonnet 4.6 (production) <Badge tone="bad">0.31</Badge></div><StepList steps={BASELINE_STEPS} /></Card>
                <Card className="border-good/40"><div className="mb-3 flex items-center justify-between text-[13px] font-medium">{modelOf(best).name} · {best.id} <Badge tone="good">0.94</Badge></div><StepList steps={TRAINED_STEPS} /></Card>
              </div>
            </div>
          )}
        </>
      )}
    </>
  )
}
