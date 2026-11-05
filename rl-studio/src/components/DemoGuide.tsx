import { useLocation, useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Presentation, RotateCcw, X, FastForward } from 'lucide-react'
import { useDemo } from '../lib/store'
import { cx } from './ui'

export const GUIDE = [
  { path: '/', title: 'The pitch', points: ['Ford has a warranty agent built on Claude. It works, but it’s generic: it doesn’t know Ford’s policy, TSBs or labor ops.', 'Studio turns “what good looks like” into a model Ford owns: environment → experts → training → production.'] },
  { path: '/signup', title: 'Sign up', points: ['Work email detects the company and drops you into the Ford workspace.', 'SSO (Okta / Entra) and a data-governance choice up front: Ford data never trains anyone else’s model.'] },
  { path: '/onboarding', title: 'Connect the agent you already have', points: ['Two-line change: point the Claude/Codex client at the Studio proxy.', 'Traces start flowing immediately; pick a starting template (warranty triage).'] },
  { path: '/app', title: 'The learning loop', points: ['One checklist for the whole journey. Each step unlocks the next.', 'Nothing here requires an ML team.'] },
  { path: '/app/traces', title: 'See where the agent fails', points: ['Studio clusters 1,842 production traces into failure modes and prices each one.', 'Open the F-150 cam-phaser claim: the agent paid the wrong labor op and missed the TSB.'] },
  { path: '/app/environment', title: 'Vibe-build the RL environment', points: ['Describe the job in plain English. Studio drafts tools, tasks and a reward from your traces + APIs.', 'Answer one question: how bad is a wrong approval vs an escalation? That becomes reward weights.', 'Validate: sandbox boots, grader is deterministic, reward hacks are caught, there is headroom.'] },
  { path: '/app/experts', title: 'Bring in experts', points: ['Hire vetted master techs and warranty admins (or invite your own analysts) to author hard tasks, demos and grades.', 'Their grades calibrate the automatic grader, so experts label hundreds, not thousands.'] },
  { path: '/app/evals', title: 'Baseline before training', points: ['Same environment, every model: Claude (today), GPT, Gemini and trainable open-weight models.', 'Frontier is ~61%. Open models start at ~34% but are 10–20× cheaper — that’s the gap training closes.'] },
  { path: '/app/training/new', title: 'Kick off training runs', points: ['Pick a base model and a recipe. Defaults are sane; budget caps and auto-stop are on.', 'Start 2–3 runs in parallel to compare (e.g. Qwen GRPO vs Nemotron GRPO).'] },
  { path: '/app/training', title: 'Watch it learn', points: ['Reward climbs, held-out score tracks it, and you can read what the model does at any checkpoint.', 'Clock is accelerated for the demo (≈5 h → 70 s).'] },
  { path: '/app/deploy', title: 'Deploy safely', points: ['Test endpoint → shadow → 10% canary → 100%. Every promotion is gated by the eval suite.', 'OpenAI-compatible endpoint: the agent code doesn’t change.'] },
  { path: '/app/monitor', title: 'Online evals in production', points: ['Every live claim is graded by the expert-calibrated grader, so you see quality in real time — not just latency.', 'Drift on a new TSB? Send flagged traces to experts, fold them into the environment, retrain. That’s the flywheel.'] },
]

export default function DemoGuide() {
  const { s, set, reset, loadCompleted } = useDemo()
  const loc = useLocation()
  const nav = useNavigate()
  const idx = (() => {
    const exact = GUIDE.findIndex((g) => g.path === loc.pathname)
    if (exact >= 0) return exact
    let best = 0
    let len = 0
    GUIDE.forEach((g, i) => {
      if (g.path !== '/' && loc.pathname.startsWith(g.path + '/') && g.path.length > len) {
        best = i
        len = g.path.length
      }
    })
    return best
  })()
  const step = GUIDE[idx]

  if (!s.guideOpen) {
    return (
      <button onClick={() => set({ guideOpen: true })} className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full bg-ink px-4 py-2.5 text-[13px] font-medium text-paper shadow-lg hover:bg-ink-deep">
        <Presentation size={15} /> Demo guide · {idx + 1}/{GUIDE.length}
      </button>
    )
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 w-[340px] animate-fadein rounded-xl border border-ink/20 bg-ink text-paper shadow-2xl">
      <div className="flex items-center justify-between px-4 pt-3">
        <div className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.14em] text-steel">
          <Presentation size={13} /> Demo guide · step {idx + 1} of {GUIDE.length}
        </div>
        <button onClick={() => set({ guideOpen: false })} className="text-steel hover:text-paper" aria-label="Minimize guide">
          <X size={15} />
        </button>
      </div>
      <div className="px-4 pb-3 pt-2">
        <div className="text-[15px] font-semibold">{step.title}</div>
        <ul className="mt-1.5 space-y-1.5 text-[12.5px] leading-snug text-[#D9D4C7]">
          {step.points.map((p) => (
            <li key={p} className="flex gap-2">
              <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-[#C9A88A]" />
              {p}
            </li>
          ))}
        </ul>
      </div>
      <div className="flex gap-1 px-4 pb-2">
        {GUIDE.map((g, i) => (
          <button key={g.path} onClick={() => nav(g.path)} title={g.title} className={cx('h-1 flex-1 rounded-full', i <= idx ? 'bg-[#C9A88A]' : 'bg-white/15')} />
        ))}
      </div>
      <div className="flex items-center justify-between border-t border-white/10 px-3 py-2">
        <div className="flex gap-1">
          <button onClick={() => { reset(); nav('/') }} className="flex items-center gap-1 rounded px-2 py-1 text-[11.5px] text-steel hover:bg-white/10 hover:text-paper" title="Clear all demo state">
            <RotateCcw size={12} /> Reset
          </button>
          <button onClick={() => { loadCompleted(); nav('/app') }} className="flex items-center gap-1 rounded px-2 py-1 text-[11.5px] text-steel hover:bg-white/10 hover:text-paper" title="Load a fully populated workspace">
            <FastForward size={12} /> Skip to end state
          </button>
        </div>
        <div className="flex gap-1">
          <button disabled={idx === 0} onClick={() => nav(GUIDE[idx - 1].path)} className="rounded p-1 text-steel hover:bg-white/10 hover:text-paper disabled:opacity-30">
            <ChevronLeft size={16} />
          </button>
          <button disabled={idx === GUIDE.length - 1} onClick={() => nav(GUIDE[idx + 1].path)} className="rounded p-1 text-steel hover:bg-white/10 hover:text-paper disabled:opacity-30">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
