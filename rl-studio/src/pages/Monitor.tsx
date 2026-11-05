import { Link } from 'react-router-dom'
import { Activity, AlertTriangle, Check, Repeat, Send } from 'lucide-react'
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { DRIFT_ALERT, MODELS, TRACES } from '../lib/data'
import { runProgress, useDemo } from '../lib/store'
import { modelOf } from '../lib/runs'
import { ago, rng } from '../lib/sim'
import { Badge, Button, Card, chartColors, cx, Empty, LiveDot, PageHeader, SectionTitle, Stat } from '../components/ui'

export default function Monitor() {
  const { s, set, now } = useDemo()
  const dep = s.deployment
  const live = dep && (dep.stage === 'canary' || dep.stage === 'full')
  const run = s.runs.find((r) => r.id === dep?.runId)
  const claude = MODELS.find((m) => m.id === 'claude')!

  if (!live || !run || runProgress(run, now) < 1) {
    return (
      <>
        <PageHeader eyebrow="Ship · Online evals" title="Online evals" />
        <Empty icon={<Activity size={18} />} title="Nothing in production yet" desc="Promote a checkpoint to canary to start grading live traffic. The incumbent is already being graded so you have a baseline." action={<Link to="/app/deploy"><Button>Go to deployments</Button></Link>} />
      </>
    )
  }

  const model = modelOf(run)
  const r = rng(5)
  const sent = !!s.driftSentAt
  const days = Array.from({ length: 14 }, (_, i) => {
    const drift = i >= 10 && i <= 11 && !sent ? 0.09 : i >= 10 && i <= 11 ? 0.06 : 0
    const recovered = sent && i >= 12 ? 0.01 : 0
    return {
      day: `Oct ${23 + i > 31 ? '' : ''}${23 + i > 31 ? `Nov ${23 + i - 31}` : 23 + i}`.replace('Oct Nov', 'Nov'),
      incumbent: +((claude.score + (r() - 0.5) * 0.03 - (i >= 10 ? 0.03 : 0)) * 100).toFixed(1),
      candidate: i < 6 ? undefined : +((run.finalScore + (r() - 0.5) * 0.02 - drift + recovered) * 100).toFixed(1),
      volume: Math.round(16000 + r() * 4000),
    }
  })

  const tick = Math.floor(now / 2500)
  const feed = Array.from({ length: 9 }, (_, k) => {
    const n = tick - k
    const rr = rng(n * 13 + 7)
    const t = TRACES[Math.abs(n) % TRACES.length]
    const isNew = rr() < (dep.stage === 'full' ? 1 : 0.1)
    const score = isNew ? 0.7 + rr() * 0.28 : 0.35 + rr() * 0.55
    return { key: n, claim: `WC-26-04${(19000 + (n % 999)).toString()}`, vehicle: t.vehicle, by: isNew ? run.id : 'claude-sonnet-4.6', score, ageMs: k * 2500 + (now % 2500), low: score < 0.5 }
  })

  return (
    <>
      <PageHeader
        eyebrow="Ship · Online evals"
        title="Quality in production, graded in real time"
        desc="Every live claim is scored by the expert-calibrated grader — the same reward used in training — so you see quality, not just latency and errors."
        actions={<Badge tone="good"><LiveDot /> {dep.stage === 'full' ? '100% on ' : '10% canary · '}{run.id}</Badge>}
      />
      <div className="grid grid-cols-4 gap-4">
        <Stat label="Graded today" value="17,982" sub="99.7% of claims · grader cost $0.002 / claim" />
        <Stat label={`Online score · ${run.id}`} value={`${(run.finalScore * 100 - (sent ? 0.4 : 1.2)).toFixed(1)}`} delta={`+${((run.finalScore - claude.score) * 100 - 1).toFixed(1)} vs incumbent`} sub="7-day mean" />
        <Stat label="Analyst agreement (spot-check)" value="91%" sub="212 claims double-checked by Ford analysts" />
        <Stat label="Cost per claim" value={`$${(model.costPerClaim * 1.25).toFixed(3)}`} delta="−90%" sub={`incumbent $${claude.costPerClaim.toFixed(2)}`} />
      </div>

      <div className="mt-6 grid grid-cols-[1.5fr_1fr] gap-6">
        <Card>
          <SectionTitle right={<span className="text-[12px] text-graphite">online grader score · daily</span>}>Incumbent vs candidate</SectionTitle>
          <div className="h-72">
            <ResponsiveContainer>
              <ComposedChart data={days} margin={{ left: -14, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="day" tickLine={false} axisLine={false} interval={1} />
                <YAxis yAxisId="s" domain={[40, 90]} tickLine={false} axisLine={false} />
                <YAxis yAxisId="v" orientation="right" hide domain={[0, 60000]} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area yAxisId="v" dataKey="volume" name="claims / day" fill="#4646430F" stroke="none" isAnimationActive={false} />
                <Line yAxisId="s" dataKey="incumbent" name="Claude Sonnet 4.6" stroke={chartColors.ink} strokeDasharray="5 4" dot={false} strokeWidth={1.6} isAnimationActive={false} />
                <Line yAxisId="s" dataKey="candidate" name={`${run.id} (canary from Oct 29)`} stroke={chartColors.good} strokeWidth={2.4} dot={{ r: 2.5 }} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card pad={false} className="flex flex-col">
          <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
            <div className="text-[13px] font-semibold uppercase tracking-wider text-graphite">Live graded claims</div>
            <LiveDot />
          </div>
          <div className="flex-1 divide-y divide-hairline overflow-hidden">
            {feed.map((f, i) => (
              <div key={f.key} className={cx('flex items-center gap-3 px-4 py-2 text-[12.5px]', i === 0 && 'animate-fadein')}>
                <div className="min-w-0 flex-1">
                  <div className="truncate"><span className="font-mono">{f.claim}</span> <span className="text-graphite">· {f.vehicle}</span></div>
                  <div className="font-mono text-[11px] text-steel">{f.by} · {ago(f.ageMs)}</div>
                </div>
                <span className={cx('rounded px-1.5 py-0.5 font-mono text-[11.5px]', f.low ? 'bg-bad-tint text-bad' : f.score > 0.8 ? 'bg-good-tint text-good' : 'bg-ink/5')}>{f.score.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-6">
        <SectionTitle>Alerts & the learning flywheel</SectionTitle>
        <Card className={cx(sent ? 'border-good/40' : 'border-warn/50 bg-warn-tint/30')}>
          <div className="flex items-start gap-3">
            {sent ? <Check size={18} className="mt-0.5 text-good" /> : <AlertTriangle size={18} className="mt-0.5 text-warn" />}
            <div className="flex-1">
              <div className="text-[14.5px] font-semibold">{DRIFT_ALERT.title}</div>
              <div className="mt-0.5 text-[13px] text-graphite">{DRIFT_ALERT.detail}</div>
              {sent && (
                <div className="mt-3 grid grid-cols-3 gap-3 text-[12.5px]">
                  {[['38 traces reviewed', 'Ray D. + Denise O. · 2 h'], ['44 tasks added', 'ford-warranty-triage v5'], [s.retrainScheduled ? 'Retrain scheduled' : 'Retrain ready', s.retrainScheduled ? 'nightly · auto-canary if gate passes' : 'GS1 on last 7 days of traces']].map(([k, v]) => (
                    <div key={k} className="rounded-md bg-paper p-2.5"><div className="font-medium">{k}</div><div className="text-graphite">{v}</div></div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex flex-col gap-2">
              {!sent && <Button size="sm" onClick={() => set({ driftSentAt: Date.now() })}><Send size={13} /> Send 38 traces to experts</Button>}
              {sent && !s.retrainScheduled && <Button size="sm" onClick={() => set({ retrainScheduled: true })}><Repeat size={13} /> Schedule nightly retrain</Button>}
              {sent && s.retrainScheduled && <Badge tone="good">Flywheel on</Badge>}
            </div>
          </div>
        </Card>
        <div className="mt-4 grid grid-cols-5 gap-2 text-center text-[12px]">
          {['Production traces', 'Online grader flags', 'Experts review', 'Environment v+1', 'Retrain → canary'].map((x, i) => (
            <div key={x} className={cx('rounded-md border px-2 py-2.5', sent && (i < 4 || s.retrainScheduled) ? 'border-good/40 bg-good-tint/40' : 'border-hairline bg-card')}>
              <div className="font-mono text-[10px] text-steel">0{i + 1}</div>
              {x}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
