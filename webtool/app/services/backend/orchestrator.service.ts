import {
  JoinRequestSchema,
  LeaveRequestSchema,
  OrchestratorValidationErrorSchema,
  PeerResponseApiSchema,
  StartRequestSchema,
  StopRequestSchema,
  type JoinPeerInput,
  type PeerIdentityInput,
  type PeerResponse,
  type StartPeerInput
} from '~~/shared/orchestrator'
import type { Group } from '~~/shared/group'

type GroupRef = Pick<Group, 'id'>

async function post(group: GroupRef, action: string, body: unknown): Promise<PeerResponse> {
  const response = await fetch(`/testsuite/groups/${group.id}/orchestrator/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const validation = OrchestratorValidationErrorSchema.safeParse(data)
    const message = validation.success
      ? validation.data.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join('; ')
      : `Orchestrator request failed (${response.status})`
    throw new Error(message)
  }
  return PeerResponseApiSchema.parse(data)
}

export function startPeer(group: GroupRef, input: StartPeerInput) {
  return post(group, 'start', StartRequestSchema.parse(input))
}

export function stopPeer(group: GroupRef, input: PeerIdentityInput) {
  return post(group, 'kill', StopRequestSchema.parse(input))
}

export function joinPeer(group: GroupRef, input: JoinPeerInput) {
  return post(group, 'join', JoinRequestSchema.parse(input))
}

export function leavePeer(group: GroupRef, input: PeerIdentityInput) {
  return post(group, 'leave', LeaveRequestSchema.parse(input))
}

// Convenience wrappers that target the currently active group.
function activeGroup(): Group {
  const group = useGroupStore().activeGroup
  if (!group) throw new Error('No active group selected')
  return group
}

export const activeOrchestrator = {
  start: (input: StartPeerInput) => startPeer(activeGroup(), input),
  stop: (input: PeerIdentityInput) => stopPeer(activeGroup(), input),
  join: (input: JoinPeerInput) => joinPeer(activeGroup(), input),
  leave: (input: PeerIdentityInput) => leavePeer(activeGroup(), input)
}
