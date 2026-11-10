import { Link } from 'react-router-dom'
import { ArrowRight, Check, Circle, Loader2 } from 'lucide-react'
import { AGENT, MODELS } from '../lib/data'
import { runProgress, useDemo, useMilestones } from '../lib/store'
import { modelOf, runLeak } from '../lib/runs'
import { num, pct, usd } from '../lib/sim'
import { Badge, Button, Card, cx, PageHeader, SectionTitle, Stat } from '../components/ui'

export default function Overview() {
  const { s, now } = useDemo()
  const m = useMilestones()
  const live = s.runs.find((r) => r.id === s.deployment?.runId && runProgress(r, now) >= 1)
  const bestRun = m.live ? live : undefined
  const stageLabel = s.deployment?.stage === 'full' ? 'at 100%' : 'on canary'
  const claude = MODELS.find((x) => x.id === 'claude')!

  const steps = [
    { done: m.connected, title: 'Connect your agent', desc: '1,842 traces from warranty-triage-agent', to: '/app/traces', cta: 'View traces' },
    { done: m.envReady, active: s.builderStep > 0 && !m.envReady, title: 'Build the RL environment', desc: 'Tools, tasks and a reward that encode what “good” means at Ford', to: '/app/environment', cta: 'Open builder' },
    { done: m.expertsDone, active: m.expertsOrdered && !m.expertsDone, title: 'Add expert data', desc: 'Hard cases, demonstrations and grades from master techs and warranty admins', to: '/app/experts', cta: 'Choose experts' },
    { done: m.baselineDone, title: 'Run a baseline', desc: 'Score Claude, GPT, Gemini and open-weight models on the same environment', to: '/app/evals', cta: 'Run baseline' },
    { done: m.anyRunDone, active: m.anyRun && !m.anyRunDone, title: 'Train a model', desc: 'RL on an open-weight model you own', to: m.anyRun ? '/app/training' : '/app/training/new', cta: m.anyRun ? 'View runs' : 'New run' },
    { done: m.live, active: m.deployed && !m.live, title: 'Deploy behind a canary', desc: 'Shadow → 10% → 100%, gated by your eval suite', to: '/app/deploy', cta: 'Deploy' },
    { done: m.live && !!s.driftSentAt, active: m.live && !s.driftSentAt, title: 'Watch online evals', desc: 'Every production claim graded in real time; drift feeds the next run', to: '/app/monitor', cta: 'Open monitor' },
  ]
  const nextIdx = steps.findIndex((x) => !x.done)

  return (
    <>
      <PageHeader eyebrow="Overview" title={AGENT.display} desc={AGENT.description} actions={<Badge tone="neutral">{AGENT.harness} · {AGENT.model}</Badge>} />

      <div className="grid grid-cols-4 gap-4">
        <Stat label="Production traces (30d)" value="1,842" sub={`~${num(AGENT.claimsPerDay)} claims/day at full rollout`} />
        <Stat label="Task success today" value={pct(bestRun && m.live ? bestRun.finalScore : claude.score)} sub={bestRun && m.live ? `${bestRun.id} ${stageLabel}` : 'Claude Sonnet 4.6 baseline'} delta={bestRun && m.live ? `+${((bestRun.finalScore - claude.score) * 100).toFixed(1)} pts` : undefined} />
        <Stat label="Cost per claim" value={bestRun ? `$${(modelOf(bestRun).costPerClaim * 1.25).toFixed(3)}` : usd(claude.costPerClaim, 2)} sub={bestRun ? `self-owned ${modelOf(bestRun).name}` : 'frontier API'} delta={bestRun ? `−${Math.round((1 - (modelOf(bestRun).costPerClaim * 1.25) / claude.costPerClaim) * 100)}%` : undefined} />
        <Stat label="Leakage (wrong approvals)" value={pct(bestRun ? runLeak(bestRun) : claude.leak)} sub={bestRun ? `was ${pct(claude.leak)} on Claude` : '$1.1M / yr at current rate'} delta={bestRun ? `−${((claude.leak - runLeak(bestRun)) * 100).toFixed(1)} pts` : undefined} />
      </div>

      <div className="mt-8 grid grid-cols-[1.5fr_1fr] gap-6">
        <div>
          <SectionTitle>The learning loop</SectionTitle>
          <Card pad={false}>
            {steps.map((st, i) => (
              <div key={st.title} className={cx('flex items-center gap-4 px-5 py-4', i > 0 && 'border-t border-hairline', i === nextIdx && 'bg-leather-tint/50')}>
                <div className={cx('flex h-7 w-7 shrink-0 items-center justify-center rounded-full border', st.done ? 'border-good bg-good text-paper' : st.active ? 'border-leather text-leather' : 'border-hairline text-steel')}>
                  {st.done ? <Check size={14} /> : st.active ? <Loader2 size={14} className="animate-spin" /> : <Circle size={8} />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[14.5px] font-medium">{i + 1}. {st.title}</div>
                  <div className="text-[12.5px] text-graphite">{st.desc}</div>
                </div>
                <Link to={st.to}>
                  <Button size="sm" variant={i === nextIdx ? 'primary' : 'secondary'}>{st.cta} <ArrowRight size={13} /></Button>
                </Link>
              </div>
            ))}
          </Card>
        </div>
        <div>
          <SectionTitle>Why this matters</SectionTitle>
          <Card>
            <div className="text-[13.5px] leading-relaxed text-graphite">
              The Claude prototype resolves <span className="font-medium text-ink">61%</span> of claims the way Ford’s best analysts would. The misses are specific and repeatable — wrong labor ops, missed TSBs, out-of-coverage approvals — which is exactly what an environment + RL fixes.
            </div>
            <div className="mt-4 space-y-2 text-[13px]">
              {[['Labor overpayment', '$412k / yr'], ['Coverage leakage', '$1.1M / yr'], ['Unneeded escalations', '2,900 analyst h / yr'], ['Frontier API spend', '$2.8M / yr at full volume']].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-hairline pb-2 last:border-0">
                  <span className="text-graphite">{k}</span>
                  <span className="font-mono">{v}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card className="mt-4">
            <div className="text-[12.5px] font-medium text-graphite">Team</div>
            <div className="mt-2 space-y-2 text-[13px]">
              {[['MP', 'Maya Patel', 'Owner · Warranty Analytics'], ['JR', 'Jordan Reyes', 'Engineer · built the Claude prototype'], ['AK', 'Anita Kumar', 'Warranty Policy lead · rubric approver']].map(([i, n, r]) => (
                <div key={n} className="flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-ink/10 text-[10px] font-semibold">{i}</div>
                  <div><span className="font-medium">{n}</span> <span className="text-graphite">· {r}</span></div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
