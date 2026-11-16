<template>
  <UModal
    v-model:open="open"
    title="Join with peer"
  >
    <UButton
      icon="lucide-plus"
      label="Join"
      variant="soft"
      @click="openModal()"
    />
    <template #content>
      <UCard>
        <template #header>
          <div class="font-semibold">
            Join with peer
          </div>
        </template>
        <form
          class="flex flex-col gap-3"
          @submit.prevent="submit"
        >
          <UFormField label="Network ID">
            <UInput
              :model-value="networkId"
              disabled
              class="w-full"
            />
          </UFormField>
          <UFormField label="Peer name">
            <UInput
              v-model="peerId"
              class="w-full"
              placeholder="peer-2"
            />
            <template #help>
              <UtilHashHint :value="peerId.trim()" />
            </template>
          </UFormField>
          <UFormField label="Bootstrap peer (optional)">
            <NetworkPeerSelect
              v-model="bootstrapPeerId"
              :peers="peers"
              :none-value="NONE"
              placeholder="None"
            />
          </UFormField>
          <UButton
            type="submit"
            label="Join"
            :loading="loading"
            :disabled="!networkId.trim() || !peerId.trim() || !group"
          />
        </form>
      </UCard>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { activeOrchestrator } from '~~/app/services/backend/orchestrator.service'
import type { TopologyPeer } from '~/composables/useNetworkTopology'

const props = defineProps<{
  networkId: string
  peers: TopologyPeer[]
}>()

const NONE = '__none__'

const group = computed(() => useGroupStore().activeGroup)
const networkId = computed(() => props.networkId)
const peerId = ref('')
const bootstrapPeerId = ref<string>(NONE)
const loading = ref(false)
const open = ref(false)

function getRandomBootstrap() {
  if (!props.peers.length) return NONE
  return props.peers[Math.floor(Math.random() * props.peers.length)]!.peerId
}

async function submit() {
  loading.value = true
  try {
    const identity = { networkId: networkId.value.trim(), peerId: peerId.value.trim() }
    await activeOrchestrator.start(identity)
    const peer = await activeOrchestrator.join({
      ...identity,
      bootstrapPeerId: bootstrapPeerId.value === NONE ? null : bootstrapPeerId.value
    })
    useToast().add({ title: 'Peer joined', description: `${peer.peerId} joined ${peer.networkId}`, color: 'success' })
    peerId.value = ''
    bootstrapPeerId.value = NONE
    open.value = false
  } catch (error) {
    useToast().add({
      title: 'Failed to join',
      description: error instanceof Error ? error.message : String(error),
      color: 'error'
    })
  } finally {
    loading.value = false
  }
}
function openModal() {
  bootstrapPeerId.value = getRandomBootstrap()
  open.value = true
}

</script>
