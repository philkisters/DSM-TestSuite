<template>
  <UPopover mode="hover" :close-delay="300">
    <div class="size-2 rounded-full cursor-pointer" :class="color" />
    <template #content>
      <div class="flex flex-col items-center gap-2 p-2">
        <div class="font-bold text-lg">{{ group.name }}</div>
        <div class="font-mono">{{ group.vmIp }}</div>
        <div class="italic">Status: {{ status }}</div>
      </div>
    </template>
  </UPopover>
</template>
<script setup lang="ts">
import { type Group, OrchestratorStatus } from "~~/shared/group"

const props = defineProps<{ group: Group, active: boolean }>()

const color = computed(() => {
  let colors = ''
  if (!props.group) return 'bg-gray-500'
  switch (props.group.orchestratorStatus) {
    case OrchestratorStatus.ONLINE:
      colors = 'bg-secondary'
      break
    case OrchestratorStatus.NOT_RESPONDING:
      colors = 'bg-warning'
      break 
    case OrchestratorStatus.OFFLINE:
      colors = 'bg-error'
      break
    default:
      colors = 'bg-gray-500'
      break
  }

  if (props.active) colors += ' ring-2 ring-highlight'

  return colors
})

const status = computed(() => props.group.orchestratorStatus.toLowerCase())
</script>