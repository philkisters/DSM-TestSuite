import assert from 'node:assert/strict'
import test from 'node:test'

import { rankingSuccess, sortChallengeGroups } from '../app/utils/challengeRanking.ts'

const date = seconds => new Date(seconds * 1000)
const passed = (firstSuccess, lowestMessageCount, shortestDuration) => ({
  status: 'passed',
  timestamp: firstSuccess[2],
  firstSuccess,
  lowestMessageCount,
  shortestDuration
})
const failed = timestamp => ({ status: 'failed', timestamp })
const ids = (results, ranking) => sortChallengeGroups(results, ranking).map(([id]) => id)

test('default ranking keeps successes first and failures ordered by latest attempt', () => {
  const results = new Map([
    [1, failed(date(9))],
    [2, passed([20, 10, date(4)], undefined, undefined)],
    [3, failed(undefined)],
    [4, passed([5, 7, date(2)], undefined, undefined)],
    [5, failed(date(15))]
  ])
  assert.deepEqual(ids(results, 'firstSuccess'), [4, 2, 5, 1, 3])
})

test('metric rankings use their own run, exclude failures and put missing metrics last', () => {
  const first = passed([90, 90, date(1)], [1, 80, date(5)], [50, 2, date(9)])
  const second = passed([30, 30, date(2)], [2, 10, date(3)], [70, 1, date(4)])
  const missing = passed([null, null, date(3)], undefined, undefined)
  const results = new Map([[1, first], [2, second], [3, missing], [4, failed(date(8))]])

  assert.deepEqual(ids(results, 'messages'), [1, 2, 3])
  assert.deepEqual(ids(results, 'duration'), [2, 1, 3])
  assert.deepEqual(rankingSuccess(first, 'firstSuccess'), [90, 90, date(1)])
  assert.deepEqual(rankingSuccess(first, 'messages'), [1, 80, date(5)])
  assert.deepEqual(rankingSuccess(first, 'duration'), [50, 2, date(9)])
  assert.equal(rankingSuccess(missing, 'messages'), undefined)
})

test('zero metrics and ties are ordered by value, completion time, then group id', () => {
  const results = new Map([
    [3, passed([5, 5, date(1)], [0, 5, date(4)], [5, 0, date(4)])],
    [2, passed([5, 5, date(1)], [0, 5, date(2)], [5, 0, date(2)])],
    [1, passed([5, 5, date(1)], [0, 5, date(2)], [5, 0, date(2)])]
  ])
  assert.deepEqual(ids(results, 'messages'), [1, 2, 3])
  assert.deepEqual(ids(results, 'duration'), [1, 2, 3])
  assert.deepEqual(ids(new Map([[1, failed(date(1))]]), 'messages'), [])
  assert.deepEqual(ids(new Map(), 'duration'), [])
})
