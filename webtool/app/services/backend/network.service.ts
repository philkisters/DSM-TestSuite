import {
  NetworkCreateSchema,
  NetworkDefinitionApiSchema,
  type NetworkCreateInput,
  type NetworkDefinition
} from '~~/shared/network'

export async function createNetwork(
  groupId: number,
  input: NetworkCreateInput
): Promise<NetworkDefinition> {
  const response = await fetch(`/testsuite/groups/${groupId}/networks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(NetworkCreateSchema.parse(input))
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = typeof data?.detail === 'string'
      ? data.detail
      : `Failed to save network (${response.status})`
    throw new Error(detail)
  }
  return NetworkDefinitionApiSchema.parse(data)
}

export async function getNetwork(
  groupId: number,
  networkId: string
): Promise<NetworkDefinition | null> {
  const response = await fetch(`/testsuite/groups/${groupId}/networks`)
  if (!response.ok) throw new Error(`Failed to load networks (${response.status})`)
  const networks = NetworkDefinitionApiSchema.array().parse(await response.json())
  return networks.find(network => network.networkId === networkId) ?? null
}
