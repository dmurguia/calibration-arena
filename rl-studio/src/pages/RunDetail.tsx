import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowRight, Check, Rocket } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from 'recharts'
import { BASELINE_STEPS, MODELS, RECIPES, TRAINED_STEPS } from '../lib/data'
import { runProgress, useDemo } from '../lib/store'
import { modelOf, runLeak, runSeries } from '../lib/runs'
import { pct, usd } from '../lib/sim'
import { Badge, Button, Card, chartColors, cx, LiveDot, PageHeader, Progress, SectionTitle, Stat } from '../components/ui'
import { StepList } from './Traces'

export default function RunDetail() {
  const { id } = useParams()
  const { s, set, now } = useDemo()
  const run = s.runs.find((r) => r.id === id)
  const [ckpt, setCkpt] = useState<number | null>(null)
  if (!run) return <div>Run not found. <Link to="/app/training" className="underline">Back</Link></div>
  const p = runProgress(run, now)
  const cur = Math.floor(p * run.steps)
  const ser = runSeries(run).slice(0, cur + 1)
  const model = modelOf(run)
  const claude = MODELS.find((m) => m.id === 'claude')!
  const held = [...ser].reverse().find((x) => x.heldout !== undefined)?.heldout ?? run.startScore
  const ckpts = ser.filter((x) => x.heldout !== undefined && x.step > 0)
  const bestCk = ckpts.reduce((b, x) => ((x.heldout ?? 0) > (b?.heldout ?? 0) ? x : b), ckpts[0])
  const sel = ckpt ?? bestCk?.step ?? 0
  const selScore = ser.find((x) => x.step === sel)?.heldout ?? run.startScore
  const done = p >= 1

  return (
    <>
      <PageHeader
        eyebrow={`Improve · Training run · ${run.id}`}
        title={run.name}
        desc={<>{model.name} · {RECIPES.find((r) => r.id === run.recipe)!.name}{run.warmStart && run.recipe !== 'sft' ? ' + warm start' : ''} · ford-warranty-triage v4</>}
        actions={done ? (
          <Link to="/app/deploy" onClick={() => { if (s.deployment?.runId !== run.id) set({ deployment: { runId: run.id, stage: 'test', updatedAt: Date.now() } }) }}>
            <Button><Rocket size={14} /> {s.deployment?.runId === run.id ? 'View deployment' : 'Deploy best checkpoint'}</Button>
          </Link>
        ) : <Badge tone="leather"><LiveDot tone="leather" /> training · step {cur}/{run.steps}</Badge>}
      />

      <div className="grid grid-cols-4 gap-4">
        <Stat label="Held-out task success" value={pct(held)} delta={`${held > claude.score ? '+' : ''}${((held - claude.score) * 100).toFixed(1)} vs Claude`} deltaTone={held > claude.score ? 'good' : 'bad'} sub={`started at ${pct(run.startScore)}`} />
        <Stat label="Wrong approvals" value={pct(done ? runLeak(run) : model.leak - (model.leak - runLeak(run)) * p)} sub={`Claude: ${pct(claude.leak)}`} />
        <Stat label="Spend" value={usd(run.estCost * p)} sub={`cap ${usd(run.budget)}`} />
        <Stat label="Rollouts graded" value={(cur * 512).toLocaleString()} sub="8 attempts × 64 tasks per step" />
      </div>

      {!done && <Progress value={p} tone="leather" className="mt-4" />}

      <div className="mt-6 grid grid-cols-[1.4fr_1fr] gap-6">
        <Card>
          <SectionTitle right={<span className="text-[12px] text-graphite">dashed = Claude Sonnet 4.6</span>}>Reward & held-out score</SectionTitle>
          <div className="h-72">
            <ResponsiveContainer>
              <LineChart data={ser} margin={{ left: -14, right: 8, top: 8 }}>
                <CartesianGrid stroke={chartColors.grid} vertical={false} />
                <XAxis dataKey="step" type="number" domain={[0, run.steps]} tickLine={false} axisLine={false} />
                <YAxis domain={[0.1, 0.9]} tickLine={false} axisLine={false} />
                <Tooltip />
                <ReferenceLine y={claude.score} stroke={chartColors.ink} strokeDasharray="5 4" />
                <Line dataKey="reward" name="train reward" stroke={chartColors.steel} strokeWidth={1.2} dot={false} isAnimationActive={false} />
                <Line dataKey="heldout" name="held-out" stroke={chartColors.leather} strokeWidth={2.4} dot={{ r: 2.5 }} connectNulls isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <div className="space-y-6">
          <Card>
            <SectionTitle>Drift from base model (KL)</SectionTitle>
            <div className="h-28">
              <ResponsiveContainer>
                <AreaChart data={ser} margin={{ left: -14, right: 8, top: 4 }}>
                  <XAxis dataKey="step" hide type="number" domain={[0, run.steps]} />
                  <YAxis domain={[0, 0.1]} tickLine={false} axisLine={false} />
                  <Area dataKey="kl" stroke={chartColors.ink} fill="#4646431A" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="text-[12px] text-graphite">Stays low: the model is specializing, not forgetting how to write.</div>
          </Card>
          <Card>
            <SectionTitle>Guardrails</SectionTitle>
            <div className="space-y-1.5 text-[13px]">
              {['No reward hacking detected (0 flagged batches)', 'Held-out tracking train reward (no overfit)', `Within budget (${Math.round((run.estCost * p / run.budget) * 100)}% used)`].map((t) => (
                <div key={t} className="flex items-center gap-2"><Check size={14} className="text-good" /> {t}</div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <div className="mt-6">
        <SectionTitle>Checkpoints · read what the model does</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {ckpts.map((c) => (
            <button key={c.step} onClick={() => setCkpt(c.step)} className={cx('rounded-md border px-2.5 py-1.5 font-mono text-[12px]', sel === c.step ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card hover:border-ink/40')}>
              step {c.step} · {pct(c.heldout ?? 0, 0)} {bestCk?.step === c.step && '★'}
            </button>
          ))}
          {!ckpts.length && <div className="text-[13px] text-graphite">First checkpoint at step 10…</div>}
        </div>
        {ckpts.length > 0 && (
          <Card className="mt-3">
            <div className="mb-3 flex items-center justify-between text-[13px] font-medium">
              <span>WC-26-0418837 · F-150 cam phaser claim at step {sel}</span>
              <Badge tone={selScore > 0.6 ? 'good' : 'bad'}>{selScore > 0.6 ? 'graded 0.94' : 'graded 0.31'}</Badge>
            </div>
            <StepList steps={selScore > 0.6 ? TRAINED_STEPS : BASELINE_STEPS} />
          </Card>
        )}
      </div>

      {done && (
        <Card className="mt-6 flex items-center justify-between border-good/40 bg-good-tint/40">
          <div>
            <div className="text-[15px] font-semibold">Beats production by {((run.finalScore - claude.score) * 100).toFixed(1)} points at {Math.round(claude.costPerClaim / model.costPerClaim)}× lower cost</div>
            <div className="text-[13px] text-graphite">Best checkpoint: step {bestCk?.step} · passes the deployment gate (held-out ≥ prod, wrong approvals ≤ prod)</div>
          </div>
          <Link to="/app/evals"><Button variant="secondary">See full comparison <ArrowRight size={14} /></Button></Link>
        </Card>
      )}
    </>
  )
}
