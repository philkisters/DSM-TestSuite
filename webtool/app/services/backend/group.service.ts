import {
  GroupApiSchema,
  GroupChallengeOverviewApiSchema,
  type Group,
  type GroupChallengeOverview
} from '~~/shared/group'

export async function getGroups(): Promise<Group[]> {
  const response = await fetch('/testsuite/groups')
  const data = await response.json()
  return GroupApiSchema.array().parse(data) as Group[]
}

export async function getGroupChallengeOverview(groupId: number): Promise<GroupChallengeOverview> {
  const response = await fetch(`/testsuite/groups/${groupId}/challenge_stats`)
  if (!response.ok) throw new Error(`Failed to load group challenge overview (${response.status})`)
  return GroupChallengeOverviewApiSchema.parse(await response.json())
}

export async function createGroup(newGroup: Partial<Group>): Promise<Group> {
  const response = await fetch('/testsuite/groups', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: newGroup.name,
      vm_ip: newGroup.vmIp
    })
  })
  const data = await response.json()
  return GroupApiSchema.parse(data) as Group
}
