import { useEffect, useState } from 'react'

export const CHECK_OVERDUE_HOURS = 36

export function hoursSince(value: string | null | undefined, now: number): number {
  if (!value) return Infinity
  const timestamp = Date.parse(value)
  return Number.isFinite(timestamp) ? (now - timestamp) / 3_600_000 : Infinity
}

export function checkOverdue(value: string | null | undefined, now: number): boolean {
  const hours = hoursSince(value, now)
  return hours > CHECK_OVERDUE_HOURS || hours < -1
}

export function checkLabel(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
    ...(value.includes('T') ? { hour: 'numeric', minute: '2-digit', timeZoneName: 'short' } as const : { timeZone: 'UTC' }),
  })
}

// Age warnings while a visitor leaves the page open, even if publication stops.
export function useFreshnessClock(): number {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000)
    return () => window.clearInterval(timer)
  }, [])
  return now
}

type DatedBenchmark = { last_verified: string; results_status: string; results: { as_of: string | null } | null; flags: string[] }
export function currentFlags<T extends DatedBenchmark>(benchmark: T, now: number, reviewDays: number, resultDays: number): T {
  const flags = benchmark.flags.filter(f => !['review_due', 'results_stale', 'undated_results'].includes(f))
  if (hoursSince(benchmark.last_verified, now) > reviewDays * 24) flags.push('review_due')
  if (benchmark.results_status === 'leaderboard' && benchmark.results) {
    if (!benchmark.results.as_of) flags.push('undated_results')
    else if (hoursSince(benchmark.results.as_of, now) > resultDays * 24) flags.push('results_stale')
  }
  return { ...benchmark, flags }
}
