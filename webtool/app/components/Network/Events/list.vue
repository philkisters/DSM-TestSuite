<template>
  <div class="flex flex-col-reverse space-y-2 overflow-y-auto min-h-0 h-full min-w-0">
    <NetworkEvents v-for="event in props.events" :key="eventKey(event)" :event="event" />
  </div>
</template>

<script setup lang="ts">
import { type NetworkEvent } from '~~/shared/network'

const props = defineProps<{
  events: NetworkEvent[]
}>()

// Events are immutable objects, so object identity gives a stable key even as old ones are dropped.
const keys = new WeakMap<object, number>()
let nextKey = 0
function eventKey(event: NetworkEvent): number {
  let key = keys.get(event)
  if (key === undefined) {
    key = nextKey++
    keys.set(event, key)
  }
  return key
}
</script>