import type { GroupChallengeResult } from '../../shared/challenges'

export type ChallengeRanking = 'firstSuccess' | 'messages' | 'duration'
export type ChallengeSuccess = NonNullable<GroupChallengeResult['firstSuccess']>

export function rankingSuccess(
  result: GroupChallengeResult,
  ranking: ChallengeRanking
): ChallengeSuccess | undefined {
  if (ranking === 'messages') return result.lowestMessageCount
  if (ranking === 'duration') return result.shortestDuration
  return result.firstSuccess
}

export function sortChallengeGroups(
  results: Map<number, GroupChallengeResult>,
  ranking: ChallengeRanking
): [number, GroupChallengeResult][] {
  const entries = [...results.entries()]
    .filter(([, result]) => ranking === 'firstSuccess' || result.status === 'passed')

  return entries.sort(([aId, a], [bId, b]) => {
    if (ranking === 'firstSuccess') {
      if (a.status !== b.status) return a.status === 'passed' ? -1 : 1
      const aTime = a.timestamp?.getTime()
      const bTime = b.timestamp?.getTime()
      if (aTime === undefined) return bTime === undefined ? aId - bId : 1
      if (bTime === undefined) return -1
      return (a.status === 'passed' ? aTime - bTime : bTime - aTime) || aId - bId
    }

    const aRun = rankingSuccess(a, ranking)
    const bRun = rankingSuccess(b, ranking)
    if (!aRun) return !bRun ? aId - bId : 1
    if (!bRun) return -1
    const index = ranking === 'messages' ? 0 : 1
    const aValue = aRun[index]
    const bValue = bRun[index]
    if (aValue == null) return bValue == null ? aId - bId : 1
    if (bValue == null) return -1
    return aValue - bValue || aRun[2].getTime() - bRun[2].getTime() || aId - bId
  })
}
