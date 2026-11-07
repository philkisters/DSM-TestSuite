import assert from 'node:assert/strict'
import test from 'node:test'

import { formatDuration, runDuration, runMessageCount } from '../app/utils/challengeMetrics.ts'

test('reads message counts including zero and handles missing or invalid metrics', () => {
  assert.equal(runMessageCount({ metrics: { message_count: 7 } }), 7)
  assert.equal(runMessageCount({ metrics: { message_count: 0 } }), 0)
  assert.equal(runMessageCount({}), undefined)
  assert.equal(runMessageCount({ metrics: {} }), undefined)
  assert.equal(runMessageCount({ metrics: { message_count: '7' } }), undefined)
  assert.equal(runMessageCount({ metrics: { message_count: NaN } }), undefined)
})

test('calculates completed run duration in seconds and leaves unfinished duration unavailable', () => {
  const startedAt = new Date('2026-01-01T00:00:00Z')
  assert.equal(runDuration({ startedAt, finishedAt: new Date('2026-01-01T00:00:01.250Z') }), 1.25)
  assert.equal(runDuration({ startedAt, finishedAt: startedAt }), 0)
  assert.equal(runDuration({ startedAt }), undefined)
})

test('formats duration with at most two fractional digits', () => {
  const expected = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(1.256)
  assert.equal(formatDuration(1.256), expected)
})
