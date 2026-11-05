import { Link } from 'react-router-dom'
import { Gauge, Plus } from 'lucide-react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { MODELS, RECIPES } from '../lib/data'
import { runProgress, useDemo } from '../lib/store'
import { modelOf, runSeries } from '../lib/runs'
import { pct, usd } from '../lib/sim'
import { Badge, Button, Card, chartColors, Empty, LiveDot, PageHeader, Progress, SectionTitle } from '../components/ui'

const LINE_COLORS = [chartColors.leather, chartColors.good, chartColors.ink, chartColors.warn, chartColors.steel]

export default function Training() {
  const { s, now } = useDemo()
  const claude = MODELS.find((m) => m.id === 'claude')!

  if (!s.runs.length) {
    return (
      <>
        <PageHeader eyebrow="Improve · Training runs" title="Training runs" />
        <Empty icon={<Gauge size={18} />} title="No training runs yet" desc="Pick a base model and a recipe. Studio handles sandboxes, rollouts, checkpoints and validation." action={<Link to="/app/training/new"><Button><Plus size={14} /> New training run</Button></Link>} />
      </>
    )
  }

  const maxSteps = Math.max(...s.runs.map((r) => r.steps))
  const compare = Array.from({ length: Math.floor(maxSteps / 10) + 1 }, (_, k) => {
    const row: Record<string, number | undefined> = { step: k * 10, claude: +(claude.score * 100).toFixed(1) }
    s.runs.forEach((r) => {
      const ser = runSeries(r)
      const cur = Math.floor(runProgress(r, now) * r.steps)
      const pt = ser[k * 10]
      row[r.id] = pt && pt.step <= cur && pt.heldout !== undefined ? +(pt.heldout * 100).toFixed(1) : undefined
    })
    return row
  })

  return (
    <>
      <PageHeader eyebrow="Improve · Training runs" title="Training runs" desc="Held-out score is measured on test tasks the model never trains on. Demo clock: ≈5 h of training → 70 s." actions={<Link to="/app/training/new"><Button><Plus size={14} /> New run</Button></Link>} />
      <Card>
        <SectionTitle>Held-out task success vs. production model</SectionTitle>
        <div className="h-72">
          <ResponsiveContainer>
            <LineChart data={compare} margin={{ left: -14, right: 12, top: 8 }}>
              <CartesianGrid stroke={chartColors.grid} vertical={false} />
              <XAxis dataKey="step" tickLine={false} axisLine={false} type="number" domain={[0, maxSteps]} />
              <YAxis domain={[20, 90]} unit="%" tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line dataKey="claude" name="Claude Sonnet 4.6 (prod)" stroke={chartColors.ink} strokeDasharray="5 4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              {s.runs.map((r, i) => <Line key={r.id} dataKey={r.id} name={`${r.id} · ${modelOf(r).name}`} stroke={LINE_COLORS[i % LINE_COLORS.length]} strokeWidth={2.2} dot={false} connectNulls isAnimationActive={false} />)}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card pad={false} className="mt-6">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-hairline text-left text-[11px] uppercase tracking-wider text-graphite">
              <th className="px-4 py-2.5 font-medium">Run</th>
              <th className="px-4 py-2.5 font-medium">Recipe</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 text-right font-medium">Held-out</th>
              <th className="px-4 py-2.5 text-right font-medium">vs prod</th>
              <th className="px-4 py-2.5 text-right font-medium">Spend</th>
            </tr>
          </thead>
          <tbody>
            {s.runs.map((r) => {
              const p = runProgress(r, now)
              const ser = runSeries(r)
              const cur = Math.floor(p * r.steps)
              const last = [...ser.slice(0, cur + 1)].reverse().find((x) => x.heldout !== undefined)?.heldout ?? r.startScore
              return (
                <tr key={r.id} className="border-b border-hairline last:border-0 hover:bg-paper">
                  <td className="px-4 py-3">
                    <Link to={`/app/training/${r.id}`} className="font-medium hover:underline">{r.name}</Link>
                    <div className="font-mono text-[11.5px] text-graphite">{r.id} · {modelOf(r).name}</div>
                  </td>
                  <td className="px-4 py-3">{RECIPES.find((x) => x.id === r.recipe)!.name}{r.warmStart && r.recipe !== 'sft' && <span className="text-graphite"> + warm start</span>}</td>
                  <td className="w-52 px-4 py-3">
                    {p >= 1 ? <Badge tone="good">succeeded</Badge> : (
                      <div>
                        <div className="mb-1 flex items-center gap-1.5 text-[12px]"><LiveDot tone="leather" /> step {cur}/{r.steps}</div>
                        <Progress value={p} tone="leather" />
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{pct(last)}</td>
                  <td className={`px-4 py-3 text-right font-mono ${last > claude.score ? 'text-good' : 'text-bad'}`}>{last > claude.score ? '+' : ''}{((last - claude.score) * 100).toFixed(1)}</td>
                  <td className="px-4 py-3 text-right font-mono">{usd(r.estCost * p)}<span className="text-steel"> / {usd(r.budget)}</span></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </Card>
    </>
  )
}
