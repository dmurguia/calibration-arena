import { Link } from 'react-router-dom'
import { ArrowRight, Check, Circle, Rocket } from 'lucide-react'
import { AGENT, MODELS } from '../lib/data'
import { runProgress, useDemo, type DeployStage } from '../lib/store'
import { modelOf, runLeak } from '../lib/runs'
import { pct } from '../lib/sim'
import { Badge, Button, Card, Code, cx, Empty, LiveDot, PageHeader, SectionTitle } from '../components/ui'

const STAGES: { id: DeployStage; title: string; desc: string }[] = [
  { id: 'test', title: 'Test endpoint', desc: 'Private slug for smoke tests. No production traffic.' },
  { id: 'shadow', title: 'Shadow', desc: 'Receives a copy of 100% of claims; answers are graded but never used.' },
  { id: 'canary', title: 'Canary 10%', desc: '10% of claims are decided by the new model; online grader watches both.' },
  { id: 'full', title: 'Promote 100%', desc: 'Production slug points at this checkpoint. One-click rollback.' },
]

export default function Deploy() {
  const { s, set, now } = useDemo()
  const done = s.runs.filter((r) => runProgress(r, now) >= 1).sort((a, b) => b.finalScore - a.finalScore)
  const claude = MODELS.find((m) => m.id === 'claude')!

  if (!done.length) {
    return (
      <>
        <PageHeader eyebrow="Ship · Deployments" title="Deployments" />
        <Empty icon={<Rocket size={18} />} title="Nothing to deploy yet" desc="Finish a training run first. Its best checkpoint will appear here with a deployment gate." action={<Link to={s.runs.length ? '/app/training' : '/app/training/new'}><Button>{s.runs.length ? 'View runs' : 'New training run'}</Button></Link>} />
      </>
    )
  }

  const dep = s.deployment
  const run = done.find((r) => r.id === dep?.runId) ?? done[0]
  const model = modelOf(run)
  const stageIdx = dep ? STAGES.findIndex((x) => x.id === dep.stage) : -1
  const gates = [
    ['Held-out task success ≥ production', `${pct(run.finalScore)} vs ${pct(claude.score)}`, run.finalScore >= claude.score],
    ['Wrong approvals ≤ production', `${pct(runLeak(run))} vs ${pct(claude.leak)}`, runLeak(run) <= claude.leak],
    ['p95 latency ≤ 60 s', `${model.p50 * 2 + 3}s`, true],
    ['Regression suite (42 golden claims)', '42 / 42 pass', true],
    ['Approved by rubric owner', 'Anita Kumar · Warranty Policy', stageIdx >= 1],
  ] as const
  const advance = (stage: DeployStage) => set({ deployment: { runId: run.id, stage, updatedAt: Date.now() } })

  return (
    <>
      <PageHeader
        eyebrow="Ship · Deployments"
        title="Roll it out safely"
        desc="Every step is gated by the same eval suite you trained against. The agent code doesn’t change — only the model it calls."
        actions={dep && stageIdx >= 2 ? <Link to="/app/monitor"><Button>Open online evals <ArrowRight size={14} /></Button></Link> : undefined}
      />

      <div className="grid grid-cols-[1fr_380px] gap-6">
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[12px] text-graphite">Candidate</div>
                <div className="text-[16px] font-semibold">{model.name} · {run.id}</div>
                <div className="text-[12.5px] text-graphite">{run.name} · best checkpoint · held-out {pct(run.finalScore)}</div>
              </div>
              <div className="text-right">
                <div className="text-[12px] text-graphite">Incumbent</div>
                <div className="text-[14px] font-medium">{claude.name}</div>
                <div className="text-[12.5px] text-graphite">held-out {pct(claude.score)}</div>
              </div>
            </div>
          </Card>

          <div>
            <SectionTitle>Rollout</SectionTitle>
            <Card pad={false}>
              {STAGES.map((st, i) => {
                const reached = i <= stageIdx
                const next = i === stageIdx + 1
                return (
                  <div key={st.id} className={cx('flex items-center gap-4 px-5 py-4', i > 0 && 'border-t border-hairline', next && 'bg-leather-tint/50')}>
                    <div className={cx('flex h-7 w-7 items-center justify-center rounded-full border', reached ? 'border-good bg-good text-paper' : 'border-hairline text-steel')}>{reached ? <Check size={14} /> : <Circle size={8} />}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-[14.5px] font-medium">{st.title} {i === stageIdx && (st.id === 'canary' || st.id === 'full') && <LiveDot />}</div>
                      <div className="text-[12.5px] text-graphite">{st.desc}</div>
                    </div>
                    {next && <Button size="sm" onClick={() => advance(st.id)}>{['Create deployment', 'Start shadow', 'Start canary', 'Promote to 100%'][i]}</Button>}
                    {i === stageIdx && i > 0 && <Button size="sm" variant="ghost" onClick={() => advance(STAGES[i - 1].id)}>Roll back</Button>}
                  </div>
                )
              })}
            </Card>
          </div>

          {dep && (
            <Code
              title="warranty_agent.py — production (no code change after promotion)"
              code={`client = anthropic.Anthropic(base_url=capture.proxy("${AGENT.name}"))
# Studio's proxy now routes ${stageIdx >= 3 ? '100%' : stageIdx === 2 ? '10%' : '0%'} of calls to ford/warranty-triage@${run.id}
# OpenAI-compatible endpoint, if you prefer to call it directly:
#   POST https://api.calibrated.studio/v1/deploy/ford-warranty-triage/chat/completions
#   model="ford/warranty-triage"   # production slug → ${run.id}`}
            />
          )}
        </div>

        <div>
          <SectionTitle>Deployment gate</SectionTitle>
          <Card className="space-y-3">
            {gates.map(([t, v, ok]) => (
              <div key={t} className="flex items-start gap-2.5">
                {ok ? <Check size={15} className="mt-0.5 text-good" /> : <Circle size={15} className="mt-0.5 text-steel" />}
                <div>
                  <div className="text-[13px] font-medium">{t}</div>
                  <div className="font-mono text-[12px] text-graphite">{v}</div>
                </div>
              </div>
            ))}
          </Card>
          <Card className="mt-4">
            <div className="text-[12.5px] font-medium text-graphite">If promoted to 100%</div>
            <div className="mt-2 space-y-1.5 text-[13px]">
              {[['Model spend', '$2.8M → $0.27M / yr'], ['Leakage avoided', '≈ $800k / yr'], ['Analyst hours freed', '≈ 1,900 / yr'], ['Weights', 'Ford-owned, exportable']].map(([k, v]) => (
                <div key={k} className="flex justify-between"><span className="text-graphite">{k}</span><span className="font-mono">{v}</span></div>
              ))}
            </div>
            <Badge tone="neutral" className="mt-3">Projection at 18,400 claims/day</Badge>
          </Card>
        </div>
      </div>
    </>
  )
}
