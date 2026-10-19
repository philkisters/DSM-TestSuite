<template>
  <div class="flex">
    <div class="flex-1 flex flex-col p-4">
      <div class="flex flex-row justify-between">
        <div class="flex-1">
        </div>
        <div class="flex-1 text-center text-lg">
          Network view
        </div>
        <div class="flex-1 flex justify-end">
        </div>
      </div>
      <USeparator class="my-2" />
      <div class="w-2/3 py-2 mx-auto">
        Here you can see your network in real-time (soon)
      </div>
    </div>
    <USeparator class="my-2" orientation="vertical" />
    <div class="flex-1 flex flex-col p-4">
      <div class="flex flex-row justify-between">
        <div class="flex-1">
        </div>
        <div class="flex-1 text-center text-lg">
          Message Logs
        </div>
        <div class="flex-1 flex justify-end">
          <UButton icon="lucide-x" variant="ghost" color="neutral" @click="$emit('close')" />
        </div>
      </div>
      <USeparator class="my-2" />
      <NetworkEventsList class="py-2 mx-auto" :events="networkEvents" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { subscribeToNetworkEvents } from '~~/app/services/backend/proxy.service'
import type { NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  networkId: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const networkEvents = ref<NetworkEvent[]>([])
const unsubscribeEvents = ref<(() => void) | null>(null)


onMounted(() => {
  unsubscribeEvents.value = subscribeToNetworkEvents(props.networkId, (event: NetworkEvent) => {
    networkEvents.value.push(event)
  })
})

onUnmounted(() => {
  if (unsubscribeEvents.value) {
    unsubscribeEvents.value()
  }
})

</script>