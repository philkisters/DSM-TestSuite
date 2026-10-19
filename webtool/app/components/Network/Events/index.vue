<template>
  <div class="border border-2 p-2 rounded-md bg-muted" :class="`border-${eventColor}`">
    <NetworkEventsRegister v-if="props.event.type === 'peer_registered'" :event="props.event" />
    <NetworkEventsUnregister v-if="props.event.type === 'peer_unregistered'" :event="props.event" />
    <NetworkEventsUpdate v-if="props.event.type === 'peer_updated'" :event="props.event" />
    <NetworkEventsMessage v-if="props.event.type === 'message'" :event="props.event" />
  </div>
</template>

<script setup lang="ts">
import type { NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  event: NetworkEvent
}>()

const eventColor = computed(() => {
  switch (props.event.type) {
    case 'message':
      return 'primary'
    case 'peer_registered':
      return 'secondary'
    case 'peer_unregistered':
      return 'warning'
    default:
      return 'muted'
  }
})

</script>