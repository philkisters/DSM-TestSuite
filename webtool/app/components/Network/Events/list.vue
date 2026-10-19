<template>
  <div class="flex flex-col space-y-2">
    <NetworkEvents v-for="(event, index) in props.events" :key="index" :event="event" />
  </div>
</template>

<script setup lang="ts">
import { type NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  events: NetworkEvent[]
}>()
</script>