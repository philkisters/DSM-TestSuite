<template>
  <div class="flex flex-col gap-2 text-sm">
    <div class="font-bold">
      {{ eventName }}
    </div>
    <div class="flex gap-2 justify-between">
      <div>
        <UIcon name="lucide-mail" class="size-5" />
      </div>
      <div>
        {{  event.src }}
      </div>
      <div>
        <UIcon name="lucide-arrow-right" class="size-5" />
      </div>
      <div>
        {{  event.dst }}
      </div>
    </div>
    <!-- Event message content goes here -->
  </div>
</template>

<script setup lang="ts">
import { type NetworkPeerMessageEvent } from '~~/shared/network'
import { MessageCode } from '~~/shared/protocol'

const props = defineProps<{
  event: NetworkPeerMessageEvent
}>()

const eventName = computed<string>(() => {
  return MessageCode[props.event.code] ?? 'UNKNOWN'
})
</script>