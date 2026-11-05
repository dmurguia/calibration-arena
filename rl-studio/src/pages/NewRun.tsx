import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Info, Play } from 'lucide-react'
import { MODELS, RECIPES, type RecipeId } from '../lib/data'
import { makeRun, useDemo, useMilestones } from '../lib/store'
import { pct, usd } from '../lib/sim'
import { Badge, Button, Card, cx, PageHeader, SectionTitle } from '../components/ui'

export default function NewRun() {
  const { s, set } = useDemo()
  const m = useMilestones()
  const nav = useNavigate()
  const [modelId, setModelId] = useState('qwen35')
  const [recipe, setRecipe] = useState<RecipeId>('grpo')
  const [warm, setWarm] = useState(true)
  const [steps, setSteps] = useState(120)
  const [budget, setBudget] = useState(2500)
  const [adv, setAdv] = useState(false)
  const preview = makeRun({ recipe, modelId, warmStart: warm, steps, budget, index: s.runs.length })
  const rec = RECIPES.find((r) => r.id === recipe)!
  const trainable = MODELS.filter((x) => x.trainable)

  const launch = (alsoNemo = false) => {
    const runs = [...s.runs, preview]
    if (alsoNemo) runs.push(makeRun({ recipe, modelId: 'nemo', warmStart: warm, steps, budget, index: runs.length, startedAt: Date.now() + 400 }))
    set({ runs })
    nav(alsoNemo ? '/app/training' : `/app/training/${preview.id}`)
  }

  return (
    <>
      <PageHeader eyebrow="Improve · New training run" title="Train a model you own" desc="Defaults are tuned for your environment. Change only what you care about." />
      {!m.envReady && <Card className="mb-5 border-warn/40 bg-warn-tint/50 text-[13px]"><Info size={14} className="mr-1 inline text-warn" /> The environment isn’t validated yet — runs will use the draft. Validate it in <span className="font-medium">Environment</span> first for reliable results.</Card>}
      <div className="grid grid-cols-[1fr_340px] gap-6">
        <div className="space-y-6">
          <div>
            <SectionTitle>1 · Base model</SectionTitle>
            <div className="grid grid-cols-3 gap-3">
              {trainable.map((x) => (
                <button key={x.id} onClick={() => setModelId(x.id)} className={cx('rounded-lg border bg-card p-4 text-left', modelId === x.id ? 'border-ink ring-1 ring-ink' : 'border-hairline hover:border-ink/40')}>
                  <div className="text-[14px] font-medium">{x.name}</div>
                  <div className="text-[12px] text-graphite">{x.vendor}</div>
                  <div className="mt-2 flex justify-between font-mono text-[12px]"><span>baseline {pct(x.score, 0)}</span><span>${x.costPerClaim.toFixed(3)}/claim</span></div>
                  {x.id === 'qwen35' && <Badge tone="good" className="mt-2">Recommended</Badge>}
                </button>
              ))}
            </div>
          </div>
          <div>
            <SectionTitle>2 · Recipe</SectionTitle>
            <div className="space-y-2">
              {RECIPES.map((r) => (
                <button key={r.id} onClick={() => setRecipe(r.id)} className={cx('flex w-full items-start gap-3 rounded-lg border bg-card p-4 text-left', recipe === r.id ? 'border-ink ring-1 ring-ink' : 'border-hairline hover:border-ink/40')}>
                  <span className={cx('mt-0.5 h-4 w-4 shrink-0 rounded-full border-2', recipe === r.id ? 'border-ink bg-ink shadow-[inset_0_0_0_2px_#FAF9F6]' : 'border-hairline')} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 text-[14px] font-medium">{r.name} <Badge tone={r.tag === 'Recommended' ? 'good' : r.tag === 'Research preview' ? 'leather' : 'neutral'}>{r.tag}</Badge></div>
                    <div className="text-[12.5px] text-graphite">{r.desc}</div>
                  </div>
                </button>
              ))}
            </div>
            {recipe !== 'sft' && (
              <label className="mt-3 flex cursor-pointer items-center gap-2 text-[13px]">
                <input type="checkbox" checked={warm} onChange={() => setWarm(!warm)} className="accent-[#464643]" />
                Warm-start with expert demonstrations first {s.expertOrder ? <span className="text-graphite">(200 demos available)</span> : <span className="text-warn">(order demos in Experts)</span>}
              </label>
            )}
          </div>
          <div>
            <SectionTitle right={<button onClick={() => setAdv(!adv)} className="text-[12px] text-leather">{adv ? 'Hide' : 'Show'} advanced</button>}>3 · Budget & guardrails</SectionTitle>
            <Card className="space-y-4">
              <div>
                <div className="flex justify-between text-[13px]"><span>Training steps</span><span className="font-mono">{steps}</span></div>
                <input type="range" min={40} max={200} step={10} value={steps} onChange={(e) => setSteps(+e.target.value)} className="w-full accent-[#464643]" />
              </div>
              <div>
                <div className="flex justify-between text-[13px]"><span>Hard budget cap</span><span className="font-mono">{usd(budget)}</span></div>
                <input type="range" min={500} max={10000} step={250} value={budget} onChange={(e) => setBudget(+e.target.value)} className="w-full accent-[#464643]" />
              </div>
              <div className="grid grid-cols-2 gap-2 text-[12.5px] text-graphite">
                <div>✓ Auto-stop if held-out score drops 3 evals in a row</div>
                <div>✓ Checkpoint + held-out eval every 10 steps</div>
                <div>✓ Reward-hacking monitor on every batch</div>
                <div>✓ Weights exportable (safetensors)</div>
              </div>
              {adv && (
                <div className="grid grid-cols-3 gap-3 border-t border-hairline pt-3 font-mono text-[12px]">
                  {[['group_size', '8'], ['batch_size', '64 tasks'], ['learning_rate', '1e-6'], ['kl_coef', '0.02'], ['max_turns', '12'], ['lora_rank', '64']].map(([k, v]) => (
                    <div key={k} className="rounded bg-paper px-2 py-1.5"><div className="text-steel">{k}</div><div>{v}</div></div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
        <div>
          <div className="sticky top-16 space-y-3">
            <Card>
              <div className="text-[12.5px] font-medium text-graphite">Run summary</div>
              <div className="mt-2 text-[15px] font-semibold">{preview.name}</div>
              <div className="mt-3 space-y-1.5 text-[13px]">
                {[['Environment', 'ford-warranty-triage v4'], ['Train / test', '1,054 / 186 tasks'], ['Estimated time', `${Math.round(rec.minutes * steps / 120 / 60 * 10) / 10} h`], ['Estimated cost', usd(Math.min(preview.estCost, budget))], ['Expected held-out', `${pct(preview.finalScore - 0.03, 0)}–${pct(preview.finalScore + 0.02, 0)}`]].map(([k, v]) => (
                  <div key={k} className="flex justify-between"><span className="text-graphite">{k}</span><span className="font-mono">{v}</span></div>
                ))}
              </div>
              <Button size="lg" className="mt-4 w-full" onClick={() => launch(false)}><Play size={14} /> Start training</Button>
              {modelId !== 'nemo' && <Button variant="secondary" className="mt-2 w-full" onClick={() => launch(true)}>Start + compare with Nemotron</Button>}
            </Card>
            <div className="px-1 text-[12px] leading-relaxed text-graphite">The “expected” range comes from runs on similar environments. You only pay for steps actually run.</div>
          </div>
        </div>
      </div>
    </>
  )
}
