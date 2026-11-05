import { Link } from 'react-router-dom'
import { ArrowRight, Boxes, Gauge, Rocket, ScrollText, Users, Activity } from 'lucide-react'
import { Button, Logo } from '../components/ui'

const LOOP = [
  { icon: ScrollText, title: 'Capture', body: 'Point your existing Claude or Codex agent at Studio. Two lines of code.' },
  { icon: Boxes, title: 'Build the environment', body: 'Describe the job in plain English. Studio drafts tools, tasks and a reward.' },
  { icon: Users, title: 'Add experts', body: 'Vetted specialists author hard cases and calibrate the grader.' },
  { icon: Gauge, title: 'Train', body: 'One click RL on open-weight models you own. Compare runs side by side.' },
  { icon: Rocket, title: 'Deploy', body: 'Shadow, canary, promote. OpenAI-compatible endpoint, nothing to rewrite.' },
  { icon: Activity, title: 'Grade online', body: 'Every production call is scored. Drift feeds the next training run.' },
]

export default function Landing() {
  return (
    <div className="min-h-full bg-paper">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-8 py-5">
        <Logo />
        <nav className="flex items-center gap-6 text-[13.5px] text-graphite">
          <a className="hover:text-ink">Platform</a>
          <a className="hover:text-ink">Expert Network</a>
          <a className="hover:text-ink">Docs</a>
          <Link to="/signup" className="hover:text-ink">Log in</Link>
          <Link to="/signup"><Button size="sm">Start free</Button></Link>
        </nav>
      </header>

      <section className="mx-auto max-w-6xl px-8 pb-16 pt-14">
        <div className="max-w-3xl">
          <div className="mb-4 font-mono text-[11px] uppercase tracking-[0.16em] text-leather">RL environments, without the research team</div>
          <h1 className="font-identity text-[54px] leading-[1.02] tracking-tight text-ink">
            Vibe-build the environment.<br />Train the model you own.
          </h1>
          <p className="mt-5 max-w-2xl text-[17px] leading-relaxed text-graphite">
            Coding agents let anyone ship software. Calibrated Studio does the same for post-training: turn the agent you
            prototyped on Claude or Codex into a specialist model — with your experts’ judgment as the reward, and online
            evals watching it in production.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <Link to="/signup"><Button size="lg">Start with your agent <ArrowRight size={16} /></Button></Link>
            <Link to="/signup"><Button size="lg" variant="secondary">See the Ford demo</Button></Link>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-3 gap-px overflow-hidden rounded-xl border border-hairline bg-hairline">
          {LOOP.map((s, i) => (
            <div key={s.title} className="bg-card p-6">
              <div className="flex items-center gap-3">
                <span className="font-mono text-[11px] text-steel">0{i + 1}</span>
                <s.icon size={18} className="text-leather" strokeWidth={1.8} />
              </div>
              <div className="mt-3 text-[16px] font-semibold">{s.title}</div>
              <div className="mt-1 text-[13.5px] leading-relaxed text-graphite">{s.body}</div>
            </div>
          ))}
        </div>

        <div className="mt-12 grid grid-cols-3 gap-8 border-t border-hairline pt-8">
          {[
            ['10×', 'cheaper per task than the frontier API you prototyped on'],
            ['78%', 'task success after one RL run, vs 61% for the frontier model (Ford demo)'],
            ['< 1 day', 'from first trace to a trained, canaried model'],
          ].map(([k, v]) => (
            <div key={k}>
              <div className="font-identity text-[34px] text-ink">{k}</div>
              <div className="mt-1 text-[13.5px] text-graphite">{v}</div>
            </div>
          ))}
        </div>
      </section>
      <footer className="border-t border-hairline py-6 text-center text-[12px] text-steel">
        Demo build · all company data, claims and bulletins shown are fictional · Calibrated Co.
      </footer>
    </div>
  )
}
