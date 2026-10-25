import { z } from 'zod'
import { wireDate } from '~~/shared/wireDate'

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
  corrId: z.string(),
  status: z.string(),
  delayMs: z.number(),
  content: z.string().optional()
})

export type NetworkPeerMessageEventInput = z.input<typeof NetworkPeerMessageEventApiSchema>
export type NetworkPeerMessageEvent = z.infer<typeof NetworkPeerMessageEventApiSchema>

export const NetworkEventApiSchema = z.discriminatedUnion('type', [
  NetworkPeerEventApiSchema,
  NetworkPeerMessageEventApiSchema
])

export type NetworkEventInput = z.input<typeof NetworkEventApiSchema>
export type NetworkEvent = z.infer<typeof NetworkEventApiSchema>
