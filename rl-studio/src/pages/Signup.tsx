import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Building2, Check, KeyRound, Lock, ShieldCheck } from 'lucide-react'
import { COMPANY, DEMO_USER } from '../lib/data'
import { useDemo } from '../lib/store'
import { Badge, Button, Card, cx, Logo } from '../components/ui'

export default function Signup() {
  const { set } = useDemo()
  const nav = useNavigate()
  const [step, setStep] = useState<'email' | 'code' | 'workspace'>('email')
  const [email, setEmail] = useState(DEMO_USER.email)
  const [code, setCode] = useState('')
  const [gov, setGov] = useState({ isolate: true, pii: true, vpc: false })

  const finish = () => {
    set({ user: { name: DEMO_USER.name, email, title: DEMO_USER.title } })
    nav('/onboarding')
  }

  return (
    <div className="grid min-h-full grid-cols-[1fr_1.1fr]">
      <div className="flex flex-col bg-ink px-12 py-10 text-paper">
        <Logo dark />
        <div className="my-auto max-w-md">
          <div className="font-identity text-[36px] leading-tight">Your experts know what good looks like.</div>
          <p className="mt-4 text-[15px] leading-relaxed text-[#D9D4C7]">
            Studio turns that judgment into a reward, trains a model on it, and keeps grading it in production.
          </p>
          <div className="mt-8 space-y-3 text-[13.5px] text-[#D9D4C7]">
            {['Your data trains only your models', 'SOC 2 Type II · SSO / SCIM · audit log on every run', 'Weights are yours to export or self-host'].map((t) => (
              <div key={t} className="flex items-center gap-2"><Check size={15} className="text-[#C9A88A]" /> {t}</div>
            ))}
          </div>
        </div>
        <div className="text-[12px] text-steel">Demo build · fictional data</div>
      </div>

      <div className="flex items-center justify-center px-10">
        <div className="w-full max-w-[420px] animate-fadein" key={step}>
          {step === 'email' && (
            <>
              <h1 className="text-[24px] font-semibold">Create your workspace</h1>
              <p className="mt-1 text-sm text-graphite">Free trial includes $500 of training credits.</p>
              <div className="mt-6 space-y-2">
                <Button variant="secondary" className="w-full" onClick={() => setStep('code')}><KeyRound size={15} /> Continue with Okta SSO</Button>
                <Button variant="secondary" className="w-full" onClick={() => setStep('code')}><Building2 size={15} /> Continue with Microsoft Entra ID</Button>
              </div>
              <div className="my-5 flex items-center gap-3 text-[11px] uppercase tracking-wider text-steel"><div className="h-px flex-1 bg-hairline" />or<div className="h-px flex-1 bg-hairline" /></div>
              <label className="text-[12.5px] font-medium">Work email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 h-10 w-full rounded-md border border-hairline bg-card px-3 text-sm outline-none focus:border-ink" />
              <Button className="mt-4 w-full" size="lg" onClick={() => setStep('code')}>Continue <ArrowRight size={15} /></Button>
            </>
          )}

          {step === 'code' && (
            <>
              <h1 className="text-[24px] font-semibold">Check your inbox</h1>
              <p className="mt-1 text-sm text-graphite">We sent a 6-digit code to <span className="font-medium text-ink">{email}</span>.</p>
              <div className="mt-6 flex gap-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className={cx('flex h-12 w-12 items-center justify-center rounded-md border bg-card font-mono text-lg', code.length > i ? 'border-ink' : 'border-hairline')}>{code[i] ?? ''}</div>
                ))}
              </div>
              <div className="mt-4 flex gap-2">
                <Button className="flex-1" size="lg" onClick={() => { setCode('418837'); setTimeout(() => setStep('workspace'), 450) }}>Auto-fill demo code</Button>
              </div>
            </>
          )}

          {step === 'workspace' && (
            <>
              <Badge tone="good"><ShieldCheck size={11} /> Domain verified</Badge>
              <h1 className="mt-3 text-[24px] font-semibold">We found your company</h1>
              <Card className="mt-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[#1B3A6B] font-semibold text-white">F</div>
                <div>
                  <div className="font-medium">{COMPANY.name}</div>
                  <div className="text-[12.5px] text-graphite">@{COMPANY.domain} · 3 colleagues already here · Global Warranty Ops</div>
                </div>
              </Card>
              <div className="mt-6 text-[12.5px] font-medium">Data governance</div>
              <div className="mt-2 space-y-2">
                {([
                  ['isolate', 'Isolate training data', 'Ford traces and expert data only ever train Ford-owned models.'],
                  ['pii', 'Scrub PII and hash VINs before storage', 'Customer names, phone numbers and VINs never leave in clear text.'],
                  ['vpc', 'Run training in Ford’s cloud (BYO-VPC)', 'Enterprise option. Trial uses Calibrated’s isolated tenancy.'],
                ] as const).map(([k, t, d]) => (
                  <label key={k} className="flex cursor-pointer gap-3 rounded-md border border-hairline bg-card p-3">
                    <input type="checkbox" checked={gov[k]} onChange={() => setGov({ ...gov, [k]: !gov[k] })} className="mt-0.5 accent-[#464643]" />
                    <div>
                      <div className="text-[13.5px] font-medium">{t}</div>
                      <div className="text-[12px] text-graphite">{d}</div>
                    </div>
                  </label>
                ))}
              </div>
              <Button className="mt-5 w-full" size="lg" onClick={finish}><Lock size={14} /> Join Ford workspace</Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
