import type { GroupChallengeOverview } from '~~/shared/group'

export function sumPlaces(places: GroupChallengeOverview['firstPlaces']): number {
  return places.time + places.duration + places.messages
}
