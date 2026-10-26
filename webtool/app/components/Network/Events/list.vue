<template>
  <div class="flex flex-col-reverse space-y-2 overflow-y-auto min-h-0 h-full min-w-0">
    <NetworkEvents v-for="(event, index) in props.events" :key="index" :event="event" />
  </div>
</template>

<script setup lang="ts">
import { type NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  events: NetworkEvent[]
}>()
</script>