import { GroupApiSchema, type Group } from '~~/shared/group'

export async function getGroups(): Promise<Group[]> {
  const response = await fetch('/testsuite/groups')
  const data = await response.json()
  return GroupApiSchema.array().parse(data) as Group[]
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