import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, Bot, Flag, Wrench, X } from 'lucide-react'
import { AGENT, BASELINE_STEPS, FAILURE_CLUSTERS, HERO_CLAIM, TRACES, type TraceStep } from '../lib/data'
import { pct } from '../lib/sim'
import { Badge, Button, Card, cx, LiveDot, PageHeader, SectionTitle } from '../components/ui'

export function StepList({ steps }: { steps: TraceStep[] }) {
  return (
    <ol className="relative space-y-3 border-l border-hairline pl-5">
      {steps.map((st, i) => (
        <li key={i} className="relative">
          <span className={cx('absolute -left-[26px] top-1 flex h-3 w-3 items-center justify-center rounded-full border-2 border-card', st.verdict === 'bad' ? 'bg-bad' : st.verdict === 'warn' ? 'bg-warn' : st.verdict === 'ok' ? 'bg-good' : 'bg-steel')} />
          <div className="flex items-center gap-2 text-[12.5px]">
            <span className={cx('font-mono', st.kind === 'tool' ? 'text-leather' : 'text-ink')}>{st.title}</span>
            {st.kind === 'output' && <Badge tone={st.verdict === 'bad' ? 'bad' : 'good'}>{st.verdict === 'bad' ? 'graded 0.31' : 'graded 0.94'}</Badge>}
          </div>
          <div className="mt-0.5 text-[13px] leading-snug text-graphite">{st.body}</div>
        </li>
      ))}
    </ol>
  )
}

export default function Traces() {
  const [cluster, setCluster] = useState<string | null>(null)
  const [open, setOpen] = useState<string | null>(null)
  const sel = TRACES.find((t) => t.id === open)
  const isHero = sel?.claim === HERO_CLAIM.id
  const selCluster = FAILURE_CLUSTERS.find((x) => x.id === sel?.cluster)
  const rows = cluster ? TRACES.filter((t) => t.cluster === cluster) : TRACES

  return (
    <>
      <PageHeader
        eyebrow="Learn · Production traces"
        title="Where the agent fails today"
        desc={<>Studio grouped 1,842 traces from <span className="font-mono text-ink">{AGENT.name}</span> into failure modes, using analyst overrides and dealer disputes as signal. Each cluster becomes tasks in your environment.</>}
        actions={<Link to="/app/environment"><Button>Build environment from these <ArrowRight size={14} /></Button></Link>}
      />

      <SectionTitle right={<span className="text-[12px] text-graphite">share of traces · estimated annual impact</span>}>Failure clusters</SectionTitle>
      <div className="grid grid-cols-5 gap-3">
        {FAILURE_CLUSTERS.map((c) => (
          <button key={c.id} onClick={() => setCluster(cluster === c.id ? null : c.id)} className={cx('rounded-lg border bg-card p-3.5 text-left transition-colors', cluster === c.id ? 'border-ink ring-1 ring-ink' : 'border-hairline hover:border-ink/40')}>
            <div className="flex items-center justify-between">
              <span className="font-mono text-[20px] font-medium">{pct(c.share, 0)}</span>
              <Badge tone={c.severity === 'high' ? 'bad' : 'warn'}>{c.severity}</Badge>
            </div>
            <div className="mt-1.5 text-[13px] font-medium leading-snug">{c.label}</div>
            <div className="mt-1.5 text-[12px] text-leather">{c.impact}</div>
          </button>
        ))}
      </div>

      <div className="mt-8">
        <SectionTitle right={<span className="flex items-center gap-2 text-[12px] text-graphite"><LiveDot /> streaming from production</span>}>
          Recent traces {cluster && <button onClick={() => setCluster(null)} className="ml-2 normal-case text-leather">clear filter</button>}
        </SectionTitle>
        <Card pad={false}>
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-hairline text-left text-[11px] uppercase tracking-wider text-graphite">
                <th className="px-4 py-2.5 font-medium">Claim</th>
                <th className="px-4 py-2.5 font-medium">Vehicle</th>
                <th className="px-4 py-2.5 font-medium">Concern</th>
                <th className="px-4 py-2.5 font-medium">Agent decision</th>
                <th className="px-4 py-2.5 font-medium">Issue</th>
                <th className="px-4 py-2.5 text-right font-medium">Latency</th>
                <th className="px-4 py-2.5 text-right font-medium">Cost</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => {
                const c = FAILURE_CLUSTERS.find((x) => x.id === t.cluster)
                return (
                  <tr key={t.id} onClick={() => setOpen(t.id)} className="cursor-pointer border-b border-hairline last:border-0 hover:bg-paper">
                    <td className="px-4 py-2.5 font-mono text-[12px]">{t.claim}</td>
                    <td className="px-4 py-2.5">{t.vehicle}</td>
                    <td className="px-4 py-2.5 text-graphite">{t.concern}</td>
                    <td className="px-4 py-2.5">{t.decision}</td>
                    <td className="px-4 py-2.5">{c ? <span className="flex items-center gap-1 text-bad"><Flag size={12} /> {c.label.split(' ').slice(0, 4).join(' ')}…</span> : <span className="text-steel">—</span>}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">{t.latency}s</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px]">${t.cost.toFixed(2)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Card>
      </div>

      {open && (
        <div className="fixed inset-0 z-40 flex justify-end bg-ink/30" onClick={() => setOpen(null)}>
          <div className="h-full w-[560px] animate-fadein overflow-y-auto bg-card p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-[11px] uppercase tracking-wider text-leather">Trace · {open}</div>
                <div className="mt-1 text-[19px] font-semibold">{sel?.claim}</div>
                <div className="text-[13px] text-graphite">{isHero ? `${HERO_CLAIM.vehicle} · ${HERO_CLAIM.mileage} · in service ${HERO_CLAIM.inService}` : sel?.vehicle}</div>
              </div>
              <button onClick={() => setOpen(null)} className="text-graphite hover:text-ink"><X size={18} /></button>
            </div>
            {!isHero && sel && (
              <>
                <Card className="mt-4 bg-paper text-[13px]">
                  <div className="grid grid-cols-[110px_1fr] gap-y-1.5">
                    <span className="text-graphite">Concern</span><span>{sel.concern}</span>
                    <span className="text-graphite">Agent decision</span><span>{sel.decision}</span>
                    <span className="text-graphite">Latency · cost</span><span className="font-mono">{sel.latency}s · ${sel.cost.toFixed(2)}</span>
                    <span className="text-graphite">Failure mode</span><span className={selCluster ? 'text-bad' : 'text-steel'}>{selCluster ? selCluster.label : 'None detected — decision matched analyst review'}</span>
                  </div>
                </Card>
                {selCluster && (
                  <Card className="mt-3">
                    <div className="flex items-center gap-2 text-[13px] font-medium"><Wrench size={14} className="text-leather" /> Studio will turn this into</div>
                    <ul className="mt-1.5 list-disc pl-5 text-[13px] text-graphite">
                      <li>A replayable task with the analyst’s decision as the answer key</li>
                      <li>Example of this failure: {selCluster.example}</li>
                    </ul>
                  </Card>
                )}
                <div className="mt-4 text-[12px] text-steel">Step-by-step replay is included for {HERO_CLAIM.id} in this demo.</div>
              </>
            )}
            {isHero && (<>
            <Card className="mt-4 bg-paper text-[13px]">
              <div className="grid grid-cols-[90px_1fr] gap-y-1.5">
                <span className="text-graphite">Concern</span><span>{HERO_CLAIM.concern}</span>
                <span className="text-graphite">Cause</span><span>{HERO_CLAIM.cause}</span>
                <span className="text-graphite">Correction</span><span>{HERO_CLAIM.correction}</span>
                <span className="text-graphite">Labor</span><span className="font-mono">{HERO_CLAIM.laborOp}</span>
                <span className="text-graphite">Parts</span><span className="font-mono text-[12px]">{HERO_CLAIM.parts}</span>
              </div>
            </Card>
            <div className="mt-5 mb-2 flex items-center gap-2 text-[13px] font-medium"><Bot size={15} /> What the agent did ({AGENT.model})</div>
            <StepList steps={BASELINE_STEPS} />
            <Card className="mt-5 border-bad/30 bg-bad-tint/50">
              <div className="flex items-center gap-2 text-[13px] font-medium text-bad"><AlertTriangle size={14} /> Analyst override (Anita K., 2 days later)</div>
              <div className="mt-1 text-[13px] text-ink">“This is TSB 26-2141. Pay 12-6500-B at 8.4 h and require the PCM reflash. We overpaid 1.4 h and the customer will be back.”</div>
            </Card>
            <Card className="mt-3">
              <div className="flex items-center gap-2 text-[13px] font-medium"><Wrench size={14} className="text-leather" /> Studio will turn this into</div>
              <ul className="mt-1.5 list-disc pl-5 text-[13px] text-graphite">
                <li>A replayable task with the analyst’s decision as the answer key</li>
                <li>A reward check: “labor op matches the applicable TSB”</li>
                <li>12 synthetic variants across 3.5L / 2.7L EcoBoost model years</li>
              </ul>
            </Card>
            </>)}
          </div>
        </div>
      )}
    </>
  )
}
