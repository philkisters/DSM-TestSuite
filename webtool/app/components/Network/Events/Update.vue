<template>
  <div class="flex items-center">
    <UIcon name="lucide-rotate-cw-clock" class="size-5" />
    <div class="ml-2 overflow-hidden text-nowrap">
      {{ event.peerId}}
    </div>
  </div>
</template>

<script setup lang="ts">
import { type NetworkPeerEvent } from '~~/shared/network'

const props = defineProps<{
  event: NetworkPeerEvent
}>()
</script>