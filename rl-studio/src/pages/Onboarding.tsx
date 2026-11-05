import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Check, ClipboardList, Factory, FileText, Loader2, Wrench } from 'lucide-react'
import { AGENT, HARNESSES, TEMPLATES } from '../lib/data'
import { useDemo } from '../lib/store'
import { num } from '../lib/sim'
import { Badge, Button, Card, Code, cx, LiveDot, Logo } from '../components/ui'

const ICONS = { clipboard: ClipboardList, wrench: Wrench, file: FileText, factory: Factory }

const SNIPPETS: Record<string, string> = {
  claude: `# warranty_agent.py  (2 lines changed)
import anthropic
+ from calibrated import capture            # pip install calibrated-sdk

client = anthropic.Anthropic(
+   base_url=capture.proxy("warranty-triage-agent"),
)
# ...your existing Claude Agent SDK loop is unchanged`,
  codex: `# warranty_agent.py  (2 lines changed)
from openai import OpenAI
+ from calibrated import capture

client = OpenAI(
+   base_url=capture.proxy("warranty-triage-agent"),
)`,
  langgraph: `+ from calibrated.integrations.langgraph import CalibratedTracer
graph = build_warranty_graph()
+ graph = graph.with_config(callbacks=[CalibratedTracer("warranty-triage-agent")])`,
  http: `# Any OpenAI-compatible client: change one URL
OPENAI_BASE_URL=https://proxy.calibrated.studio/v1/warranty-triage-agent
CALIBRATED_API_KEY=cal_live_••••••••`,
}

export default function Onboarding() {
  const { s, set } = useDemo()
  const nav = useNavigate()
  const [step, setStep] = useState(0)
  const [harness, setHarness] = useState(s.harness ?? 'claude')
  const [listening, setListening] = useState(false)
  const [count, setCount] = useState(0)
  const [template, setTemplate] = useState('warranty')

  useEffect(() => {
    if (!listening) return
    const id = setInterval(() => setCount((c) => Math.min(1842, c + 97 + Math.floor(Math.random() * 60))), 120)
    return () => clearInterval(id)
  }, [listening])

  const connected = count >= 1842

  const done = () => {
    set({ onboardingDone: true, harness, agentConnected: true, templateId: template })
    nav('/app')
  }

  const steps = ['Your agent', 'Connect', 'Starting point']
  return (
    <div className="min-h-full">
      <header className="flex items-center justify-between border-b border-hairline px-8 py-4">
        <Logo />
        <div className="flex items-center gap-6">
          {steps.map((t, i) => (
            <div key={t} className={cx('flex items-center gap-2 text-[13px]', i <= step ? 'text-ink' : 'text-steel')}>
              <span className={cx('flex h-5 w-5 items-center justify-center rounded-full border text-[11px]', i < step ? 'border-ink bg-ink text-paper' : i === step ? 'border-ink' : 'border-hairline')}>{i < step ? <Check size={11} /> : i + 1}</span>
              {t}
            </div>
          ))}
        </div>
        <div className="w-32" />
      </header>

      <div className="mx-auto max-w-3xl px-8 py-12 animate-fadein" key={step}>
        {step === 0 && (
          <>
            <h1 className="text-[26px] font-semibold">Welcome, Maya. What are you building on today?</h1>
            <p className="mt-1 text-graphite">Pick the harness your agent runs on. Studio works with any of them — nothing to rewrite.</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {HARNESSES.map((h) => (
                <button key={h.id} onClick={() => setHarness(h.id)} className={cx('rounded-lg border bg-card p-4 text-left transition-colors', harness === h.id ? 'border-ink ring-1 ring-ink' : 'border-hairline hover:border-ink/40')}>
                  <div className="font-medium">{h.name}</div>
                  <div className="text-[12.5px] text-graphite">{h.detail}</div>
                </button>
              ))}
            </div>
            <Card className="mt-6">
              <div className="text-[12.5px] font-medium text-graphite">Detected in your Ford GitHub org</div>
              <div className="mt-2 flex items-center justify-between">
                <div>
                  <div className="font-mono text-[13.5px]">ford-gwo/{AGENT.name}</div>
                  <div className="text-[12.5px] text-graphite">{AGENT.harness} · {AGENT.model} · ~{num(AGENT.claimsPerDay)} claims/day in the pilot region</div>
                </div>
                <Badge tone="leather">Prototype</Badge>
              </div>
            </Card>
            <div className="mt-8 flex justify-end"><Button size="lg" onClick={() => setStep(1)}>Next <ArrowRight size={15} /></Button></div>
          </>
        )}

        {step === 1 && (
          <>
            <h1 className="text-[26px] font-semibold">Connect your agent</h1>
            <p className="mt-1 text-graphite">Route model calls through Studio. Your agent keeps calling the same model; Studio records every trajectory — messages, tool calls, outcomes.</p>
            <Code className="mt-6" title="warranty_agent.py" code={SNIPPETS[harness]} />
            <Card className="mt-4">
              {!listening && (
                <div className="flex items-center justify-between">
                  <div className="text-sm text-graphite">Deploy the change, or import the last 30 days of logs.</div>
                  <Button onClick={() => setListening(true)}>Import last 30 days</Button>
                </div>
              )}
              {listening && (
                <div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      {connected ? <Check size={16} className="text-good" /> : <Loader2 size={16} className="animate-spin text-leather" />}
                      {connected ? 'Connected — traces flowing' : 'Importing traces…'}
                    </div>
                    <div className="font-mono text-sm">{num(count)} traces</div>
                  </div>
                  {connected && (
                    <div className="mt-3 grid grid-cols-4 gap-3 text-[12.5px]">
                      {[['Claims', '1,842'], ['Tool calls', '14,206'], ['Analyst overrides', '412'], ['Avg. cost / claim', '$0.42']].map(([k, v]) => (
                        <div key={k} className="rounded-md bg-paper p-2">
                          <div className="text-graphite">{k}</div>
                          <div className="font-mono text-[15px] text-ink">{v}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {connected && <div className="mt-3 flex items-center gap-2 text-[12.5px] text-graphite"><LiveDot /> Live: new production traces will appear in Production traces.</div>}
                </div>
              )}
            </Card>
            <div className="mt-8 flex justify-between">
              <Button variant="ghost" onClick={() => setStep(0)}>Back</Button>
              <Button size="lg" disabled={!connected} onClick={() => setStep(2)}>Next <ArrowRight size={15} /></Button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h1 className="text-[26px] font-semibold">What should this agent get better at?</h1>
            <p className="mt-1 text-graphite">Start from a template. Studio pre-fills the environment with your traces; you can change everything later.</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {TEMPLATES.map((t) => {
                const Icon = ICONS[t.icon]
                return (
                  <button key={t.id} onClick={() => setTemplate(t.id)} className={cx('rounded-lg border bg-card p-4 text-left transition-colors', template === t.id ? 'border-ink ring-1 ring-ink' : 'border-hairline hover:border-ink/40')}>
                    <div className="flex items-center justify-between">
                      <Icon size={18} className="text-leather" />
                      {t.id === 'warranty' && <Badge tone="good">Matches your traces</Badge>}
                    </div>
                    <div className="mt-2 font-medium">{t.title}</div>
                    <div className="mt-0.5 text-[12.5px] leading-snug text-graphite">{t.blurb}</div>
                    <div className="mt-2 font-mono text-[11px] text-steel">{t.who} · {t.tools} tools</div>
                  </button>
                )
              })}
            </div>
            <div className="mt-8 flex justify-between">
              <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
              <Button size="lg" onClick={done}>Open workspace <ArrowRight size={15} /></Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
