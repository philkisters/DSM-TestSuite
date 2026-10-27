import { shortHash } from '~/composables/useHash'
import type { NetworkEvent } from '~~/shared/network'

export interface TopologyPeer {
  peerId: string
  hash: string
  predecessor: string | null
  successor: string | null
}

// Neighbors may arrive as a plain id or as an identity object.
function neighborId(value: unknown): string | null {
  if (typeof value === 'string') return value || null
  if (value && typeof value === 'object') {
    const v = value as Record<string, unknown>
    const id = v.peer_id ?? v.peerId
    if (typeof id === 'string' && id) return id
  }
  return null
}

/**
 * Applies a proxy event to the peer map. Returns true if the topology changed.
 */
export function applyNetworkEvent(peers: Map<string, TopologyPeer>, event: NetworkEvent): boolean {
  if (event.type === 'message') return false

  if (event.type === 'peer_unregistered') return peers.delete(event.peerId)

  const existing = peers.get(event.peerId)
  const peer: TopologyPeer = existing ?? {
    peerId: event.peerId,
    hash: shortHash(event.peerId),
    predecessor: null,
    successor: null
  }
  let changed = !existing

  if (event.peerData) {
    const predecessor = neighborId(event.peerData.predecessor)
    const successor = neighborId(event.peerData.successor)
    if (predecessor !== peer.predecessor || successor !== peer.successor) {
      peer.predecessor = predecessor
      peer.successor = successor
      changed = true
    }
  }

  peers.set(event.peerId, peer)
  return changed
}

/**
 * Reactive peer list for a network, built incrementally from proxy events.
 * Feed every event to `push`; `peers` is replaced only when the topology changes.
 */
export function useNetworkTopology() {
  const state = new Map<string, TopologyPeer>()
  const peers = shallowRef<TopologyPeer[]>([])

  function push(event: NetworkEvent) {
    if (applyNetworkEvent(state, event)) {
      peers.value = Array.from(state.values(), p => ({ ...p }))
    }
  }

  function reset() {
    state.clear()
    peers.value = []
  }

  return { peers, push, reset }
}
