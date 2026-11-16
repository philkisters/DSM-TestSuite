import { getPeerImages } from '~~/app/services/backend/proxy.service'
import { onScopeDispose, shallowRef, watch, type Ref } from 'vue'

export function usePeerImages(networkId: Readonly<Ref<string>>, selectedPeer: Readonly<Ref<string | null>>) {
  const peerImages = shallowRef<ReadonlyMap<string, string[]>>(new Map())
  const requests = new Map<string, AbortController>()

  function cancelRequests() {
    for (const controller of requests.values()) controller.abort()
    requests.clear()
  }

  watch(networkId, () => {
    cancelRequests()
    peerImages.value = new Map()
  }, { flush: 'sync' })

  watch([networkId, selectedPeer], async ([network, peer]) => {
    if (!peer) return
    requests.get(peer)?.abort()
    const controller = new AbortController()
    requests.set(peer, controller)
    try {
      const images = await getPeerImages(network, peer, controller.signal)
      if (requests.get(peer) === controller) {
        peerImages.value = new Map(peerImages.value).set(peer, images)
      }
    } catch (e) {
      if (!controller.signal.aborted) {
        useToast().add({
          title: 'Failed to load images',
          description: `${peer}: ${e instanceof Error ? e.message : String(e)}`,
          color: 'error'
        })
      }
    } finally {
      if (requests.get(peer) === controller) requests.delete(peer)
    }
  }, { flush: 'sync' })

  onScopeDispose(cancelRequests)
  return peerImages
}
