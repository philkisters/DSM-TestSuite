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
      <UButton
        type="submit"
        label="Create"
        :loading="loading"
        :disabled="!networkId.trim() || !peerId.trim() || !group"
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

const emit = defineEmits<{
  (e: 'created', networkId: string): void
}>()

const group = computed(() => useGroupStore().activeGroup)
const networkId = ref('')
const peerId = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    const identity = { networkId: networkId.value.trim(), peerId: peerId.value.trim() }
    await activeOrchestrator.start(identity)
    // No bootstrap peer: the first peer starts a new ring.
    const peer = await activeOrchestrator.join(identity)
    useToast().add({ title: 'Network created', description: `${peer.peerId} started in ${peer.networkId}`, color: 'success' })
    emit('created', peer.networkId)
    networkId.value = ''
    peerId.value = ''
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
