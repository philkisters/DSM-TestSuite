<template>
  <USelect
    v-model="selected"
    :items="items"
    :placeholder="placeholder"
    class="w-full"
  />
</template>

<script setup lang="ts">
import type { TopologyPeer } from '~/composables/useNetworkTopology'

const props = defineProps<{
  peers: TopologyPeer[]
  placeholder?: string
  noneValue?: string
}>()
const selected = defineModel<string>({ required: true })
const items = computed(() => [
  ...(props.noneValue === undefined ? [] : [{ label: 'None', value: props.noneValue }]),
  ...props.peers.map(peer => ({ label: peer.peerId, value: peer.peerId }))
])
</script>
