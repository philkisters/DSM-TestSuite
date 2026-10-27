<template>
  <div class="flex min-w-0 flex-grow">
    <div class="flex flex-col border-r-muted border-r-1 min-w-48">
      <PanelButton
        v-for="network in networks"
        :key="network.networkId"
        :class="{ 'bg-primary/30': selectedNetworkId === network.networkId }"
      >
        <div
          class="flex flex-col"
          @click="selectedNetworkId = network.networkId"
        >
          <div class="text-lg font-semibold font-mono">
            {{ network.networkId }}
          </div>
          <div class="text-muted text-sm">
            {{ network.peerCount }} peers
          </div>
        </div>
      </PanelButton>
      <div
        v-if="!networks.length"
        class="text-muted text-sm p-4"
      >
        No active networks.
      </div>
    </div>
    <div class="flex h-full min-w-0 min-h-0 flex-grow justify-center overflow-x-hidden p-4">
      <NetworkOverview
        v-if="selectedNetworkId"
        :key="selectedNetworkId"
        :network-id="selectedNetworkId"
        @empty="onEmpty"
      />
      <NetworkCreate
        v-else
        @created="onCreated"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { getNetworks } from '~~/app/services/backend/proxy.service'
import type { NetworkStat } from '~~/shared/network'

const networks = ref<NetworkStat[]>([])
const selectedNetworkId = ref<string | null>(null)
let timer: ReturnType<typeof setInterval> | null = null

async function refresh() {
  try {
    networks.value = await getNetworks()
  } catch {
    // keep the last known list on transient failures
  }
}

async function onCreated(networkId: string) {
  await refresh()
  selectedNetworkId.value = networkId
}

async function onEmpty() {
  selectedNetworkId.value = null
  await refresh()
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 2000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
