<template>
  <div class="flex items-center">
    <UIcon name="lucide-plus-circle" class="size-5" />
    <div class="ml-2 overflow-hidden text-nowrap">
      {{ event.peerId}}@{{ event.host }}:{{ event.port }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { type NetworkPeerEvent } from '~~/shared/network'

const props = defineProps<{
  event: NetworkPeerEvent
}>()
</script>