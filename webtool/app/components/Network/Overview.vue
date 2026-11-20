<template>
  <div class="flex flex-col flex-1 min-w-0 min-h-0 gap-4 w-full">
    <div class="flex-3 min-h-0 flex flex-col">
      <div class="flex flex-row items-center">
        <div class="flex-1" />
        <div class="text-center text-lg">
          Network <span class="font-mono">{{ networkId }}</span>
        </div>
        <div class="flex-1 flex justify-end gap-2">
          <NetworkImageModal
            :network-id="networkId"
            :peers="peers"
            :selected-peer="selectedPeer"
            :replication-factor="replicationFactor"
          />
          <NetworkJoinModal
            :network-id="networkId"
            :peers="peers"
          />
        </div>
      </div>
      <USeparator class="my-2" />
      <NetworkPreview
        :peers="peers"
        :highlight="selectedPeer"
        :fingers="fingers"
        :image-counts="imageCounts"
        class="flex-1 min-h-0"
        @select="selectedPeer = $event"
      />
    </div>
    <div class="flex-2 min-h-0 flex flex-row gap-4">
      <div class="flex-1 min-w-0 min-h-0 flex flex-col">
        <div class="text-center text-lg">
          Message Logs ({{ selectedPeer ? `${visibleEvents.length} / ${networkEvents.length}` : networkEvents.length }})
        </div>
        <USeparator class="my-2" />
        <NetworkEventsList
          class="py-2 flex-1 min-h-0 w-full"
          :events="visibleEvents"
        />
      </div>
      <USeparator orientation="vertical" />
      <div class="flex-1 min-w-0 min-h-0 flex flex-col">
        <div class="text-center text-lg">
          Peer Details
        </div>
        <USeparator class="my-2" />
        <div
          v-if="!selectedPeer"
          class="text-muted text-center py-4"
        >
          Select a peer in the network to see its details.
        </div>
        <NetworkPeerDetails
          v-else
          :network-id="networkId"
          :peer-id="selectedPeer"
          :peer="selectedPeerInfo"
          :images="selectedImages"
          :busy="busy"
          @leave="leave"
          @kill="kill"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getPeerFingers, subscribeToNetworkEvents } from '~~/app/services/backend/proxy.service'
import { activeOrchestrator } from '~~/app/services/backend/orchestrator.service'
import { getNetwork } from '~~/app/services/backend/network.service'
import type { NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  networkId: string
}>()
const emit = defineEmits<{ empty: [] }>()

const settings = useSettingsStore()
const networkEvents = shallowRef<NetworkEvent[]>([])
const selectedPeer = ref<string | null>(null)
const fingers = ref<string[]>([])
const peerImages = usePeerImages(toRef(() => props.networkId), selectedPeer)
const imageCounts = computed(() => new Map(
  Array.from(peerImages.value, ([peer, images]) => [peer, images.length])
))
const replicationFactor = ref(1)
const selectedImages = computed(() => selectedPeer.value ? peerImages.value.get(selectedPeer.value) : undefined)
const { peers, pushAll } = useNetworkTopology()
const selectedPeerInfo = computed(() => peers.value.find(p => p.peerId === selectedPeer.value) ?? null)
const visibleEvents = computed(() => {
  const peer = selectedPeer.value
  if (!peer) return networkEvents.value
  return networkEvents.value.filter(e => e.type === 'message' && (e.src === peer || e.dst === peer))
})
const busy = ref<'leave' | 'kill' | null>(null)

watch(() => [props.networkId, useGroupStore().activeGroup?.id], async ([networkId, groupId]) => {
  replicationFactor.value = 1
  if (!groupId) return
  try {
    const network = await getNetwork(groupId, networkId)
    replicationFactor.value = network?.replicationFactor ?? 1
  } catch (error) {
    console.error('Failed to load network settings:', error)
  }
}, { immediate: true })

watch([() => props.networkId, selectedPeer], async ([networkId, peerId], _previous, onCleanup) => {
  fingers.value = []
  if (!peerId) return

  const controller = new AbortController()
  let active = true
  onCleanup(() => {
    active = false
    controller.abort()
  })
  try {
    const result = await getPeerFingers(networkId, peerId, controller.signal)
    if (active) fingers.value = result
  } catch (e) {
    if (active) {
      useToast().add({
        title: 'Failed to load fingers',
        description: e instanceof Error ? e.message : String(e),
        color: 'error'
      })
    }
  }
}, { flush: 'sync' })

async function run(action: 'leave' | 'kill') {
  if (!selectedPeer.value || busy.value) return
  const identity = { networkId: props.networkId, peerId: selectedPeer.value }
  busy.value = action
  try {
    if (action === 'leave') await activeOrchestrator.leave(identity)
    await activeOrchestrator.stop(identity)
    useToast().add({
      title: action === 'leave' ? 'Peer left and stopped' : 'Peer killed',
      description: identity.peerId,
      color: 'success'
    })
    selectedPeer.value = null
  } catch (e) {
    useToast().add({
      title: action === 'leave' ? 'Leave failed' : 'Kill failed',
      description: e instanceof Error ? e.message : String(e),
      color: 'error'
    })
  } finally {
    busy.value = null
  }
}
const leave = () => run('leave')
const kill = () => run('kill')

// Only fire once peers were seen, so the initial empty state doesn't trigger it.
let hadPeers = false
watch(peers, (list) => {
  if (list.length) hadPeers = true
  else if (hadPeers) {
    hadPeers = false
    emit('empty')
  }
})

let unsubscribe: (() => void) | null = null

function subscribe(networkId: string) {
  unsubscribe?.()
  unsubscribe = subscribeToNetworkEvents(networkId, (events: NetworkEvent[]) => {
    // A new array per batch, so the list's props change and it re-renders.
    networkEvents.value = [...networkEvents.value, ...events].slice(-settings.maxNetworkEvents)
    pushAll(events)
  })
}

onMounted(() => subscribe(props.networkId))
onUnmounted(() => unsubscribe?.())
</script>
