import {
  ChallengeApiSchema,
  ChallengeResultsApiSchema,
  type Challenge,
  type ChallengeResults
} from '~~/shared/challenges'

export async function getChallengeResults(
  challengeId: number,
  groupId: number
): Promise<ChallengeResults> {
  const response = await fetch(`/testsuite/challenges/${challengeId}/${groupId}/results`)
  if (!response.ok) throw new Error(`Failed to load challenge results (${response.status})`)
  return ChallengeResultsApiSchema.parse(await response.json())
}

export async function getChallenges(): Promise<Challenge[]> {
  const response = await fetch('/testsuite/challenges')
  const data = await response.json()
  return ChallengeApiSchema.array().parse(data) as Challenge[]
}

export async function startChallenge(
  challengeId: number,
  groupId: number
): Promise<void> {
  const response = await fetch(`/testsuite/challenges/${challengeId}/${groupId}/start`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error(`Failed to start challenge (${response.status})`)
}