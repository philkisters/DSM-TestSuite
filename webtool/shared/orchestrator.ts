import { z } from 'zod'

const id = z.string().min(1).max(128)

export const PeerIdentityRequestSchema = z.object({
  networkId: id,
  peerId: id
}).transform(r => ({ network_id: r.networkId, peer_id: r.peerId }))

export const StartRequestSchema = PeerIdentityRequestSchema
export const LeaveRequestSchema = PeerIdentityRequestSchema
export const StopRequestSchema = PeerIdentityRequestSchema

export const JoinRequestSchema = z.object({
  networkId: id,
  peerId: id,
  bootstrapPeerId: id.nullish()
}).transform(r => ({
  network_id: r.networkId,
  peer_id: r.peerId,
  bootstrap_peer_id: r.bootstrapPeerId ?? null
}))

export const PeerResponseApiSchema = z.object({
  network_id: z.string(),
  peer_id: z.string(),
  status: z.string()
}).transform(r => ({
  networkId: r.network_id,
  peerId: r.peer_id,
  status: r.status
}))

export const OrchestratorValidationErrorSchema = z.object({
  detail: z.array(z.object({
    loc: z.array(z.union([z.string(), z.number()])),
    msg: z.string(),
    type: z.string()
  }).passthrough())
})

export type PeerIdentityInput = z.input<typeof PeerIdentityRequestSchema>
export type StartPeerInput = z.input<typeof StartRequestSchema>
export type JoinPeerInput = z.input<typeof JoinRequestSchema>
export type PeerResponse = z.infer<typeof PeerResponseApiSchema>
