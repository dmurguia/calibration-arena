import { MODELS } from './data'
import { learningCurve } from './sim'
import type { TrainingRun } from './store'

export function runSeries(run: TrainingRun) {
  const n = run.steps
  const train = learningCurve(n + 1, run.startScore * 0.92, run.finalScore * 0.98, run.seed, 0.05)
  const evalPts = Math.floor(n / 10) + 1
  const held = learningCurve(evalPts, run.startScore, run.finalScore, run.seed + 7, 0.012)
  const kl = learningCurve(n + 1, 0, 0.07, run.seed + 3, 0.004, 0.25)
  return Array.from({ length: n + 1 }, (_, i) => ({
    step: i,
    reward: +train[i].toFixed(3),
    heldout: i % 10 === 0 ? +held[i / 10].toFixed(3) : undefined,
    kl: +kl[i].toFixed(4),
  }))
}

export function modelOf(run: TrainingRun) {
  return MODELS.find((m) => m.id === run.modelId)!
}

/** Leakage falls roughly in proportion to quality gained (leakage-weighted reward). */
export function runLeak(run: TrainingRun) {
  const m = modelOf(run)
  const gain = (run.finalScore - m.score) / Math.max(0.01, 0.86 - m.score)
  return Math.max(0.012, m.leak * (1 - gain * 0.9))
}
