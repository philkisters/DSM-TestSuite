<template>
  <div class="flex min-w-0 min-h-0">
    <div class="flex-2 flex flex-col min-w-0 min-h-0 p-4">
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
      <NetworkPreview :peers="peers" class="flex-1 min-h-0" />
    </div>
    <USeparator class="my-2" orientation="vertical" />
    <div class="flex-1 flex flex-col min-w-0 min-h-0 p-4">
      <div class="flex flex-row justify-between">
        <div class="flex-1">
        </div>
        <div class="flex-5 text-center text-lg">
          Message Logs ({{ networkEvents.length }})
        </div>
        <div class="flex-1 flex justify-end">
          <UButton icon="lucide-x" variant="ghost" color="neutral" @click="$emit('close')" />
        </div>
      </div>
      <USeparator class="my-2" />
      <NetworkEventsList class="py-2 flex-1 min-h-0 w-full" :events="networkEvents" />
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

const settings = useSettingsStore()
const networkEvents = shallowRef<NetworkEvent[]>([])
const { peers, pushAll } = useNetworkTopology()
const unsubscribeEvents = ref<(() => void) | null>(null)


onMounted(() => {
  unsubscribeEvents.value = subscribeToNetworkEvents(props.networkId, (events: NetworkEvent[]) => {
    // A new array per batch, so the list's props change and it re-renders.
    networkEvents.value = [...networkEvents.value, ...events].slice(-settings.maxNetworkEvents)
    pushAll(events)
  })
})

onUnmounted(() => {
  if (unsubscribeEvents.value) {
    unsubscribeEvents.value()
  }
})

</script>