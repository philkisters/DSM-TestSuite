<template>
  <div>
    <!-- Event message content goes here -->
  </div>
</template>

<script setup lang="ts">
import { type NetworkPeerMessageEvent } from '~~/shared/network'

const props = defineProps<{
  event: NetworkPeerMessageEvent
}>()
</script>