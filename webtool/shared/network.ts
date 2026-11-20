import { z } from 'zod'
import { wireDate } from '~~/shared/wireDate'

export const OrchestratorVersionSchema = z.enum(['v1', 'v2'])
export type OrchestratorVersion = z.infer<typeof OrchestratorVersionSchema>

export const NetworkCreateSchema = z.object({
  networkId: z.string().trim().min(1).max(128),
  orchestratorVersion: OrchestratorVersionSchema,
  replicationFactor: z.number().int().positive().nullable()
}).superRefine((network, context) => {
  if (network.orchestratorVersion === 'v1' && network.replicationFactor !== null) {
    context.addIssue({
      code: 'custom',
      message: 'Replication requires orchestrator v2',
      path: ['replicationFactor']
    })
  }
}).transform(network => ({
  network_id: network.networkId,
  orchestrator_version: network.orchestratorVersion,
  replication_factor: network.replicationFactor
}))

export const NetworkDefinitionApiSchema = z.object({
  id: z.number(),
  group_id: z.number(),
  network_id: z.string(),
  orchestrator_version: OrchestratorVersionSchema,
  replication_factor: z.number().nullable(),
  created_at: wireDate
}).transform(network => ({
  id: network.id,
  groupId: network.group_id,
  networkId: network.network_id,
  orchestratorVersion: network.orchestrator_version,
  replicationFactor: network.replication_factor,
  createdAt: network.created_at
}))

export type NetworkCreateInput = z.input<typeof NetworkCreateSchema>
export type NetworkDefinition = z.infer<typeof NetworkDefinitionApiSchema>

export const NetworkStatApiSchema = z
  .record(z.string(), z.number())
  .transform((data): NetworkStat[] =>
    Object.entries(data).map(([networkId, peerCount]) => ({
      networkId,
      peerCount
    }))
  )
export const NetworkStatSchema = z.object({
  networkId: z.string(),
  peerCount: z.number()
})

export type NetworkStat = z.infer<typeof NetworkStatSchema>

export const NetworkPeerEventApiSchema = z.object({
  type: z.enum(['peer_registered', 'peer_updated', 'peer_unregistered']),
  ts: wireDate,
  networkId: z.string(),
  peerId: z.string(),
  host: z.string().optional().nullable(),
  port: z.number().optional().nullable(),
  peerData: z.record(z.string(), z.any()).optional(),
  message: z.string().optional()
})

export type NetworkPeerEventInput = z.input<typeof NetworkPeerEventApiSchema>
export type NetworkPeerEvent = z.infer<typeof NetworkPeerEventApiSchema>

export const NetworkPeerMessageEventApiSchema = z.object({
  type: z.literal('message'),
  ts: wireDate,
  networkId: z.string(),
  src: z.string(),
  dst: z.string(),
  code: z.number(),
  size: z.number(),
  status: z.string(),
  delayMs: z.number().nullable(),
  content: z.object({}).optional().nullable()
})

export type NetworkPeerMessageEventInput = z.input<typeof NetworkPeerMessageEventApiSchema>
export type NetworkPeerMessageEvent = z.infer<typeof NetworkPeerMessageEventApiSchema>

export const NetworkEventApiSchema = z.discriminatedUnion('type', [
  NetworkPeerEventApiSchema,
  NetworkPeerMessageEventApiSchema
])

export type NetworkEventInput = z.input<typeof NetworkEventApiSchema>
export type NetworkEvent = z.infer<typeof NetworkEventApiSchema>
