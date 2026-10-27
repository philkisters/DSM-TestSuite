<template>
  <div class="flex flex-col flex-1 min-w-0 min-h-0 gap-4 w-full">
    <div class="flex-3 min-h-0 flex flex-col">
      <div class="flex flex-row items-center">
        <div class="flex-1" />
        <div class="text-center text-lg">
          Network <span class="font-mono">{{ networkId }}</span>
        </div>
        <div class="flex-1 flex justify-end">
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
        <template v-else>
          <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 py-2 overflow-auto">
            <dt class="text-muted">
              Peer
            </dt>
            <dd class="font-mono truncate">
              {{ selectedPeerInfo?.peerId ?? selectedPeer }}
            </dd>
            <dt class="text-muted">
              Hash
            </dt>
            <dd class="font-mono">
              {{ selectedPeerInfo?.hash ?? '-' }}
            </dd>
            <dt class="text-muted">
              Status
            </dt>
            <dd>{{ selectedPeerInfo ? 'Active' : 'Unknown' }}</dd>
            <dt class="text-muted">
              Successor
            </dt>
            <dd class="font-mono truncate">
              {{ selectedPeerInfo?.successor ?? '-' }}
            </dd>
            <dt class="text-muted">
              Predecessor
            </dt>
            <dd class="font-mono truncate">
              {{ selectedPeerInfo?.predecessor ?? '-' }}
            </dd>
          </dl>
          <div class="flex gap-2 pt-2">
            <UButton
              color="warning"
              :loading="busy === 'leave'"
              :disabled="busy !== null"
              @click="leave"
            >
              Leave
            </UButton>
            <UButton
              color="error"
              :loading="busy === 'kill'"
              :disabled="busy !== null"
              @click="kill"
            >
              Kill
            </UButton>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { subscribeToNetworkEvents } from '~~/app/services/backend/proxy.service'
import { activeOrchestrator } from '~~/app/services/backend/orchestrator.service'
import type { NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  networkId: string
}>()
const emit = defineEmits<{ empty: [] }>()

const networkEvents = ref<NetworkEvent[]>([])
const selectedPeer = ref<string | null>(null)
const { peers, push } = useNetworkTopology()
const selectedPeerInfo = computed(() => peers.value.find(p => p.peerId === selectedPeer.value) ?? null)
const visibleEvents = computed(() => {
  const peer = selectedPeer.value
  if (!peer) return networkEvents.value
  return networkEvents.value.filter(e => e.type === 'message' && (e.src === peer || e.dst === peer))
})
const busy = ref<'leave' | 'kill' | null>(null)

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
  unsubscribe = subscribeToNetworkEvents(networkId, (event: NetworkEvent) => {
    networkEvents.value.push(event)
    push(event)
  })
}

onMounted(() => subscribe(props.networkId))
onUnmounted(() => unsubscribe?.())
</script>
