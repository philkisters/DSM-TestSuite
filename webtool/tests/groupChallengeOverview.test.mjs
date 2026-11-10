import assert from 'node:assert/strict'
import { registerHooks } from 'node:module'
import test from 'node:test'

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith('~~/')) {
      return nextResolve(new URL(`../${specifier.slice(3)}.ts`, import.meta.url).href, context)
    }
    return nextResolve(specifier, context)
  }
})

const { GroupChallengeOverviewApiSchema } = await import('../shared/group.ts')
const { getGroupChallengeOverview } = await import('../app/services/backend/group.service.ts')

const payload = {
  group_id: 7,
  group_name: 'Group 7',
  total_passed_challenges: 1,
  first_places: { time: 1, duration: 0, messages: 0 },
  second_places: { time: 0, duration: 1, messages: 0 },
  third_places: { time: 0, duration: 0, messages: 1 },
  challenges_by_status: [
    {
      key: 'week-0/example',
      week: 'week-0',
      title: 'Example',
      tries: 2,
      successes: 1,
      first_pass: '2026-08-18T14:32:00',
      last_fail: '2026-08-18T14:30:00Z'
    },
    {
      key: 'week-0/unattempted',
      week: 'week-0',
      title: 'Unattempted',
      tries: 0,
      successes: 0,
      first_pass: null,
      last_fail: null
    }
  ]
}

test('group overview service fetches and transforms the full response', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => Response.json(payload))
  const result = await getGroupChallengeOverview(7)

  assert.equal(fetchMock.mock.calls[0].arguments[0], '/testsuite/groups/7/challenge_stats')
  assert.deepEqual(result, {
    groupId: 7,
    groupName: 'Group 7',
    totalPassedChallenges: 1,
    firstPlaces: { time: 1, duration: 0, messages: 0 },
    secondPlaces: { time: 0, duration: 1, messages: 0 },
    thirdPlaces: { time: 0, duration: 0, messages: 1 },
    challengesByStatus: [
      {
        key: 'week-0/example',
        week: 'week-0',
        title: 'Example',
        tries: 2,
        successes: 1,
        firstPass: new Date('2026-08-18T14:32:00Z'),
        lastFail: new Date('2026-08-18T14:30:00Z')
      },
      {
        key: 'week-0/unattempted',
        week: 'week-0',
        title: 'Unattempted',
        tries: 0,
        successes: 0,
        firstPass: null,
        lastFail: null
      }
    ]
  })
})

test('group overview schema rejects malformed counts and timestamps', () => {
  assert.equal(GroupChallengeOverviewApiSchema.safeParse({
    ...payload,
    first_places: { time: 1, duration: 0 }
  }).success, false)
  assert.equal(GroupChallengeOverviewApiSchema.safeParse({
    ...payload,
    challenges_by_status: [{ ...payload.challenges_by_status[0], first_pass: 'invalid' }]
  }).success, false)
})

test('group overview service reports HTTP and invalid response errors', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => new Response(null, { status: 404 }))
  await assert.rejects(getGroupChallengeOverview(999), /Failed to load group challenge overview \(404\)/)

  fetchMock.mock.mockImplementation(async () => Response.json({ ...payload, total_passed_challenges: '1' }))
  await assert.rejects(getGroupChallengeOverview(7), /total_passed_challenges/)
})
