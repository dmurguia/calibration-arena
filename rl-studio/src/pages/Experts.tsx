import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, Star, UserPlus } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { DATA_JOBS, EXPERTS } from '../lib/data'
import { progressOf, useDemo } from '../lib/store'
import { DEMO_SPEED } from '../lib/store'
import { num, usd } from '../lib/sim'
import { Badge, Button, Card, chartColors, cx, LiveDot, PageHeader, Progress, SectionTitle } from '../components/ui'

const MARKUP = 1.45

export default function Experts() {
  const { s, set, now } = useDemo()
  const [picked, setPicked] = useState<string[]>(['e1', 'e2', 'e3', 'e6'])
  const [counts, setCounts] = useState<Record<string, number>>(Object.fromEntries(DATA_JOBS.map((j) => [j.id, j.default])))
  const paid = EXPERTS.filter((e) => picked.includes(e.id) && !e.internal)
  const avgRate = paid.length ? paid.reduce((a, e) => a + e.rate, 0) / paid.length : 0
  const hours = DATA_JOBS.reduce((a, j) => a + counts[j.id] / j.perHour, 0)
  const cost = Math.round(hours * avgRate * MARKUP)
  const order = s.expertOrder
  const p = order ? progressOf(order.startedAt, order.durationMs, now) : 0
  const calib = Array.from({ length: 11 }, (_, i) => ({ labels: i * 120, agreement: +(0.58 + 0.28 * (1 - Math.exp(-i / 3.2))).toFixed(3) }))
  const shownCalib = calib.slice(0, Math.max(1, Math.round(p * 10) + 1))

  return (
    <>
      <PageHeader
        eyebrow="Learn · Experts & data"
        title="Bring in people who know what good looks like"
        desc="Vetted specialists from the Calibrated Expert Network — or your own analysts — author the hard cases, demonstrate the job and grade attempts. Their grades calibrate the automatic grader so it scales to every claim."
        actions={p >= 1 ? <Link to="/app/evals"><Button>Next: run a baseline <ArrowRight size={14} /></Button></Link> : undefined}
      />

      {!order && (
        <div className="grid grid-cols-[1fr_360px] gap-6">
          <div>
            <SectionTitle right={<span className="text-[12px] text-graphite">matched to: EcoBoost · warranty policy · EV · diesel</span>}>Recommended experts</SectionTitle>
            <div className="grid grid-cols-2 gap-3">
              {EXPERTS.map((e) => {
                const on = picked.includes(e.id)
                return (
                  <button key={e.id} onClick={() => setPicked(on ? picked.filter((x) => x !== e.id) : [...picked, e.id])} className={cx('rounded-lg border bg-card p-4 text-left transition-colors', on ? 'border-ink ring-1 ring-ink' : 'border-hairline hover:border-ink/40')}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className={cx('flex h-9 w-9 items-center justify-center rounded-full text-[12px] font-semibold', e.internal ? 'bg-[#1B3A6B] text-white' : 'bg-leather-tint text-leather')}>
                          {e.internal ? <UserPlus size={15} /> : e.name.split(' ').map((x) => x[0]).join('')}
                        </div>
                        <div>
                          <div className="text-[14px] font-medium">{e.name}</div>
                          <div className="text-[12px] leading-snug text-graphite">{e.role}</div>
                        </div>
                      </div>
                      <div className={cx('flex h-5 w-5 items-center justify-center rounded border', on ? 'border-ink bg-ink text-paper' : 'border-hairline')}>{on && <Check size={12} />}</div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1">{e.focus.map((f) => <Badge key={f}>{f}</Badge>)}</div>
                    <div className="mt-3 flex items-center justify-between text-[12px] text-graphite">
                      {e.internal ? <span>Internal reviewers · approve rubric changes</span> : <span className="flex items-center gap-1"><Star size={11} className="fill-leather text-leather" /> {e.rating} · {num(e.tasksDone)} tasks · {e.years} yrs</span>}
                      <span className="font-mono text-ink">{e.internal ? 'no charge' : `$${e.rate}/h`}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <SectionTitle>What should they produce?</SectionTitle>
            <Card className="space-y-4">
              {DATA_JOBS.map((j) => (
                <div key={j.id}>
                  <div className="flex items-center justify-between">
                    <div className="text-[13.5px] font-medium">{j.label}</div>
                    <input type="number" value={counts[j.id]} onChange={(e) => setCounts({ ...counts, [j.id]: Math.max(0, +e.target.value) })} className="h-7 w-20 rounded border border-hairline bg-paper px-2 text-right font-mono text-[12.5px] outline-none focus:border-ink" />
                  </div>
                  <div className="mt-0.5 text-[12px] leading-snug text-graphite">{j.desc}</div>
                </div>
              ))}
              <div className="border-t border-hairline pt-3 text-[13px]">
                <div className="flex justify-between"><span className="text-graphite">Expert hours</span><span className="font-mono">{Math.round(hours)} h</span></div>
                <div className="flex justify-between"><span className="text-graphite">Turnaround</span><span className="font-mono">~3 business days</span></div>
                <div className="flex justify-between"><span className="text-graphite">QA</span><span>2nd-expert review on 20%</span></div>
                <div className="mt-2 flex justify-between text-[15px] font-semibold"><span>Estimate</span><span className="font-mono">{usd(cost)}</span></div>
              </div>
              <Button className="w-full" size="lg" disabled={!paid.length} onClick={() => set({ expertOrder: { startedAt: Date.now(), durationMs: DEMO_SPEED.expertJobMs, experts: picked, counts, cost } })}>
                Start data job
              </Button>
              <div className="text-center text-[11.5px] text-steel">Experts sign Ford’s NDA · work happens inside Studio · no data leaves the tenancy</div>
            </Card>
          </div>
        </div>
      )}

      {order && (
        <div className="space-y-6">
          <Card className="flex items-center gap-5">
            <div className="flex -space-x-2">
              {EXPERTS.filter((e) => order.experts.includes(e.id)).map((e) => (
                <div key={e.id} className={cx('flex h-9 w-9 items-center justify-center rounded-full border-2 border-card text-[11px] font-semibold', e.internal ? 'bg-[#1B3A6B] text-white' : 'bg-leather-tint text-leather')}>{e.internal ? 'F' : e.name.split(' ').map((x) => x[0]).join('')}</div>
              ))}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 text-[14.5px] font-medium">{p >= 1 ? <><Check size={15} className="text-good" /> Data job complete</> : <><LiveDot tone="leather" /> Experts are working</>}</div>
              <div className="text-[12.5px] text-graphite">{order.experts.length} experts · {usd(order.cost)} · demo clock: 3 days → 45 s</div>
            </div>
            <div className="w-56"><Progress value={p} tone={p >= 1 ? 'good' : 'leather'} /></div>
          </Card>
          <div className="grid grid-cols-4 gap-4">
            {DATA_JOBS.map((j, i) => {
              const jp = Math.min(1, p * (1.25 - i * 0.08))
              return (
                <Card key={j.id}>
                  <div className="text-[12px] text-graphite">{j.label}</div>
                  <div className="mt-1 font-mono text-[22px]">{num(Math.round(order.counts[j.id] * jp))}<span className="text-[13px] text-steel"> / {num(order.counts[j.id])}</span></div>
                  <Progress value={jp} className="mt-2" tone={jp >= 1 ? 'good' : 'ink'} />
                </Card>
              )
            })}
          </div>
          <div className="grid grid-cols-[1.3fr_1fr] gap-6">
            <Card>
              <SectionTitle right={<Badge tone={p >= 1 ? 'good' : 'leather'}>κ {shownCalib[shownCalib.length - 1].agreement.toFixed(2)}</Badge>}>Grader ↔ expert agreement</SectionTitle>
              <div className="h-56">
                <ResponsiveContainer>
                  <LineChart data={shownCalib} margin={{ left: -18, right: 8, top: 8 }}>
                    <CartesianGrid stroke={chartColors.grid} vertical={false} />
                    <XAxis dataKey="labels" tickLine={false} axisLine={false} type="number" domain={[0, 1200]} />
                    <YAxis domain={[0.5, 0.9]} tickLine={false} axisLine={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="agreement" stroke={chartColors.leather} strokeWidth={2.2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[12.5px] text-graphite">Each expert grade teaches the grader Ford’s standard. After ~1,200 labels it agrees with experts as often as two experts agree with each other (κ ≈ 0.86), so it can grade the other 18,000 claims a day.</div>
            </Card>
            <Card>
              <SectionTitle>Latest from experts</SectionTitle>
              <div className="space-y-3 text-[13px]">
                {[
                  ['RD', 'Ray D.', 'New task: 2.7L EcoBoost oil-cooler leak where the RO lists the 3.5L part. Answer key: request info.', 0.15],
                  ['DO', 'Denise O.', 'Rubric: dealer note must state the exact labor op and hours paid, not “adjusted per policy”.', 0.35],
                  ['TK', 'Tom K.', 'Red-team: agent scored 0.71 by citing every TSB returned. Patched: extra bulletins now cost −0.05 each.', 0.55],
                  ['AK', 'Anita K. (Ford)', 'Approved rubric v2 for dealer notes.', 0.8],
                ].filter((x) => p >= (x[3] as number)).map(([i, n, t]) => (
                  <div key={n as string} className="flex gap-2.5 animate-fadein">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-leather-tint text-[10px] font-semibold text-leather">{i}</div>
                    <div><span className="font-medium">{n}</span> <span className="text-graphite">{t}</span></div>
                  </div>
                ))}
                {p < 0.15 && <div className="text-graphite">Waiting for first submissions…</div>}
              </div>
            </Card>
          </div>
        </div>
      )}
    </>
  )
}
