export function rng(seed: number) {
  let s = seed >>> 0 || 1
  return () => {
    s ^= s << 13
    s ^= s >>> 17
    s ^= s << 5
    return ((s >>> 0) % 100000) / 100000
  }
}

export const clamp = (v: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v))

/** Smooth S-curve from `start` to `end` over `n` points with seeded noise. */
export function learningCurve(n: number, start: number, end: number, seed: number, noise = 0.03, knee = 0.35) {
  const r = rng(seed)
  const out: number[] = []
  for (let i = 0; i < n; i++) {
    const t = i / Math.max(1, n - 1)
    const s = 1 / (1 + Math.exp(-10 * (t - knee)))
    const s0 = 1 / (1 + Math.exp(10 * knee))
    const s1 = 1 / (1 + Math.exp(-10 * (1 - knee)))
    const norm = (s - s0) / (s1 - s0)
    const jitter = (r() - 0.5) * 2 * noise * (1 - 0.5 * t)
    out.push(clamp(start + (end - start) * norm + jitter))
  }
  return out
}

export const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`
export const usd = (v: number, d = 0) =>
  v.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: d, maximumFractionDigits: d })
export const num = (v: number) => v.toLocaleString('en-US')

export function ago(ms: number) {
  const s = Math.max(0, Math.round(ms / 1000))
  if (s < 60) return `${s}s ago`
  const m = Math.round(s / 60)
  if (m < 60) return `${m}m ago`
  return `${Math.round(m / 60)}h ago`
}
