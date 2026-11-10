import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { MODELS, RECIPES, type RecipeId } from './data'
import { clamp } from './sim'

/** Demo clock: things that take hours in real life complete in seconds here. */
export const DEMO_SPEED = {
  trainingMs: 70_000,
  expertJobMs: 45_000,
  baselineMs: 14_000,
  validateMs: 9_000,
}

export interface TrainingRun {
  id: string
  name: string
  recipe: RecipeId
  modelId: string
  warmStart: boolean
  steps: number
  requestedSteps?: number
  startedAt: number
  durationMs: number
  seed: number
  startScore: number
  finalScore: number
  budget: number
  estCost: number
}

export type DeployStage = 'test' | 'shadow' | 'canary' | 'full'

export interface DemoState {
  user?: { name: string; email: string; title: string }
  onboardingDone: boolean
  harness?: string
  agentConnected: boolean
  templateId?: string
  builderStep: number
  taskMix?: 'mixed' | 'real'
  leakageWeighted: boolean
  validateStartedAt?: number
  expertOrder?: { startedAt: number; durationMs: number; experts: string[]; counts: Record<string, number>; cost: number }
  baselineStartedAt?: number
  runs: TrainingRun[]
  deployment?: { runId: string; stage: DeployStage; updatedAt: number; approved?: boolean }
  driftSentAt?: number
  retrainScheduled: boolean
  guideOpen: boolean
}

const INITIAL: DemoState = {
  onboardingDone: false,
  agentConnected: false,
  builderStep: 0,
  leakageWeighted: false,
  runs: [],
  retrainScheduled: false,
  guideOpen: true,
}

const KEY = 'calibrated-studio-demo-v1'

/** Task split for the drafted environment; depends on the copilot's task-source choice. */
export function taskCounts(s: Pick<DemoState, 'taskMix'>) {
  const replay = 812
  const synthetic = s.taskMix === 'real' ? 0 : 428
  const total = replay + synthetic
  const test = Math.round(total * 0.15)
  return { replay, synthetic, total, test, train: total - test }
}

export function progressOf(startedAt: number | undefined, durationMs: number, now: number) {
  if (!startedAt) return 0
  return clamp((now - startedAt) / durationMs)
}

export function runProgress(run: TrainingRun, now: number) {
  return progressOf(run.startedAt, run.durationMs, now)
}

export function makeRun(opts: { recipe: RecipeId; modelId: string; warmStart: boolean; steps: number; budget: number; name?: string; startedAt?: number; durationMs?: number; index: number }): TrainingRun {
  const model = MODELS.find((m) => m.id === opts.modelId)!
  const recipe = RECIPES.find((r) => r.id === opts.recipe)!
  const warmBonus = opts.warmStart && opts.recipe !== 'sft' ? 0.06 : 0
  const rate = model.id === 'glm' ? 1.5 : model.id === 'nemo' ? 0.7 : 1
  const steps = Math.max(1, Math.min(opts.steps, Math.floor(opts.budget / (recipe.costPerStep * rate))))
  const stepFactor = clamp(steps / 120, 0.55, 1.15)
  const finalScore = clamp(model.score + (recipe.uplift + warmBonus) * stepFactor, 0, 0.86)
  const startScore = opts.warmStart && opts.recipe !== 'sft' ? model.score + 0.18 : model.score
  return {
    id: `run-${String(opts.index + 1).padStart(2, '0')}`,
    name: opts.name ?? `${recipe.name.split(' (')[0]} · ${model.name}`,
    recipe: opts.recipe,
    modelId: opts.modelId,
    warmStart: opts.warmStart,
    steps,
    requestedSteps: opts.steps,
    startedAt: opts.startedAt ?? Date.now(),
    durationMs: opts.durationMs ?? DEMO_SPEED.trainingMs,
    seed: 17 + opts.index * 31,
    startScore,
    finalScore,
    budget: opts.budget,
    estCost: Math.round(steps * recipe.costPerStep * rate),
  }
}

/** Fully-populated workspace for jumping straight to the end of the story. */
export function completedState(): DemoState {
  const t = Date.now() - 3 * 60 * 60 * 1000
  const runs = [
    makeRun({ recipe: 'sft', modelId: 'qwen35', warmStart: false, steps: 60, budget: 1000, index: 0, startedAt: t, name: 'Warm start on expert demos' }),
    makeRun({ recipe: 'grpo', modelId: 'qwen35', warmStart: true, steps: 120, budget: 2500, index: 1, startedAt: t + 1000, name: 'GRPO · Qwen 3.6 35B · leakage-weighted' }),
    makeRun({ recipe: 'grpo', modelId: 'nemo', warmStart: true, steps: 120, budget: 2500, index: 2, startedAt: t + 2000, name: 'GRPO · Nemotron Lightning' }),
  ]
  return {
    ...INITIAL,
    user: { name: 'Maya Patel', email: 'maya.patel@ford.com', title: 'Sr. Engineer, Warranty Analytics' },
    onboardingDone: true,
    harness: 'claude',
    agentConnected: true,
    templateId: 'warranty',
    builderStep: 5,
    leakageWeighted: true,
    validateStartedAt: t,
    expertOrder: { startedAt: t, durationMs: DEMO_SPEED.expertJobMs, experts: ['e1', 'e2', 'e3', 'e6'], counts: { tasks: 300, demos: 200, labels: 1200, redteam: 60 }, cost: 24180 },
    baselineStartedAt: t,
    runs,
    deployment: { runId: 'run-02', stage: 'canary', updatedAt: t, approved: true },
    taskMix: 'mixed',
    guideOpen: true,
  }
}

interface Ctx {
  s: DemoState
  set: (patch: Partial<DemoState> | ((s: DemoState) => Partial<DemoState>)) => void
  reset: () => void
  loadCompleted: () => void
  now: number
}

const DemoCtx = createContext<Ctx | null>(null)

export function DemoProvider({ children }: { children: ReactNode }) {
  const [s, setS] = useState<DemoState>(() => {
    try {
      const raw = localStorage.getItem(KEY)
      return raw ? { ...INITIAL, ...JSON.parse(raw) } : INITIAL
    } catch {
      return INITIAL
    }
  })
  const [now, setNow] = useState(Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 500)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(s))
  }, [s])

  const set = useCallback<Ctx['set']>((patch) => {
    setS((prev) => ({ ...prev, ...(typeof patch === 'function' ? patch(prev) : patch) }))
  }, [])

  const value = useMemo<Ctx>(
    () => ({
      s,
      set,
      now,
      reset: () => setS({ ...INITIAL }),
      loadCompleted: () => setS(completedState()),
    }),
    [s, set, now],
  )
  return <DemoCtx.Provider value={value}>{children}</DemoCtx.Provider>
}

export function useDemo() {
  const c = useContext(DemoCtx)
  if (!c) throw new Error('useDemo outside provider')
  return c
}

/** Derived milestones used by the overview checklist and the demo guide. */
export function useMilestones() {
  const { s, now } = useDemo()
  const envReady = progressOf(s.validateStartedAt, DEMO_SPEED.validateMs, now) >= 1
  const expertsDone = s.expertOrder ? progressOf(s.expertOrder.startedAt, s.expertOrder.durationMs, now) >= 1 : false
  const baselineDone = progressOf(s.baselineStartedAt, DEMO_SPEED.baselineMs, now) >= 1
  const anyRunDone = s.runs.some((r) => runProgress(r, now) >= 1)
  const anyRun = s.runs.length > 0
  const deployed = !!s.deployment
  const live = s.deployment?.stage === 'canary' || s.deployment?.stage === 'full'
  return { connected: s.agentConnected, envReady, expertsDone, expertsOrdered: !!s.expertOrder, baselineDone, anyRun, anyRunDone, deployed, live }
}
