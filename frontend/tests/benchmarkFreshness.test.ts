import assert from 'node:assert/strict'
import { test } from 'node:test'
import { checkOverdue, currentFlags } from '../src/pilot/benchmarkFreshness.ts'

test('freshness advances with real time without another publication', () => {
  const stamp = '2026-10-20T13:17:00Z'
  assert.equal(checkOverdue(stamp, Date.parse('2026-10-21T13:17:00Z')), false)
  assert.equal(checkOverdue(stamp, Date.parse('2026-10-22T13:17:00Z')), true)
  assert.equal(checkOverdue('invalid', Date.now()), true)
  assert.equal(checkOverdue('2099-01-01', Date.now()), true)
})

test('directory flags ignore frozen build-time flags', () => {
  const benchmark = { last_verified: '2026-09-01', results_status: 'leaderboard', results: { as_of: '2026-01-01' }, flags: ['vendor_published'] }
  assert.deepEqual(currentFlags(benchmark, Date.parse('2026-10-20'), 45, 180).flags, ['vendor_published', 'review_due', 'results_stale'])
  assert.deepEqual(currentFlags({ ...benchmark, last_verified: '2026-10-20', results: { as_of: null }, flags: ['results_stale'] }, Date.parse('2026-10-20'), 45, 180).flags, ['undated_results'])
})
