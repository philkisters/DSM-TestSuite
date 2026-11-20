<template>
  <UCard class="w-full max-w-md self-start mt-8">
    <template #header>
      <div class="text-lg font-semibold">
        Create network
      </div>
      <div class="text-muted text-sm">
        Starts the first peer of a new network on the active group's orchestrator.
      </div>
    </template>
    <form
      class="flex flex-col gap-4"
      @submit.prevent="submit"
    >
      <UFormField
        label="Network ID"
        required
      >
        <UInput
          v-model="networkId"
          class="w-full"
          placeholder="my-network"
        />
      </UFormField>
      <UFormField
        label="Peer name"
        required
      >
        <UInput
          v-model="peerId"
          class="w-full"
          placeholder="peer-1"
        />
      </UFormField>
      <UFormField label="Orchestrator version">
        <USelect
          v-model="orchestratorVersion"
          class="w-full"
          :items="orchestratorVersions"
        />
      </UFormField>
      <UFormField
        v-if="orchestratorVersion === 'v2'"
        label="Replication factor"
        help="Optional for legacy v2 peers."
      >
        <UInput
          v-model.number="replicationFactor"
          type="number"
          min="1"
          step="1"
          class="w-full"
          placeholder="3"
        />
      </UFormField>
      <UButton
        type="submit"
        label="Create"
        :loading="loading"
        :disabled="!networkId.trim() || !peerId.trim() || !group || !replicationValid"
      />
      <div
        v-if="!group"
        class="text-muted text-sm"
      >
        Select a group to create a network.
      </div>
    </form>
  </UCard>
</template>

<script setup lang="ts">
import { activeOrchestrator } from '~~/app/services/backend/orchestrator.service'
import { createNetwork } from '~~/app/services/backend/network.service'
import type { OrchestratorVersion } from '~~/shared/network'

const emit = defineEmits<{
  (e: 'created', networkId: string): void
}>()

const group = computed(() => useGroupStore().activeGroup)
const networkId = ref('')
const peerId = ref('')
const orchestratorVersion = ref<OrchestratorVersion>('v1')
const replicationFactor = ref<number | string | undefined>()
const replicationValid = computed(() =>
  replicationFactor.value === undefined
  || replicationFactor.value === ''
  || (typeof replicationFactor.value === 'number'
    && Number.isInteger(replicationFactor.value)
    && replicationFactor.value > 0)
)
const orchestratorVersions = [
  { label: 'Version 1', value: 'v1' },
  { label: 'Version 2', value: 'v2' }
]
const loading = ref(false)

async function submit() {
  if (!group.value) return
  loading.value = true
  try {
    const identity = { networkId: networkId.value.trim(), peerId: peerId.value.trim() }
    await createNetwork(group.value.id, {
      networkId: identity.networkId,
      orchestratorVersion: orchestratorVersion.value,
      replicationFactor: orchestratorVersion.value === 'v2'
        ? (typeof replicationFactor.value === 'number' ? replicationFactor.value : null)
        : null
    })
    await activeOrchestrator.start(identity)
    // No bootstrap peer: the first peer starts a new ring.
    const peer = await activeOrchestrator.join(identity)
    useToast().add({ title: 'Network created', description: `${peer.peerId} started in ${peer.networkId}`, color: 'success' })
    emit('created', peer.networkId)
    networkId.value = ''
    peerId.value = ''
    orchestratorVersion.value = 'v1'
    replicationFactor.value = undefined
  } catch (error) {
    useToast().add({
      title: 'Failed to create network',
      description: error instanceof Error ? error.message : String(error),
      color: 'error'
    })
  } finally {
    loading.value = false
  }
}
</script>
