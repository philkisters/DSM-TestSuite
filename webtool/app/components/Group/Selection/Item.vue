<template>
  <div class="flex flex-col items-center p-4 border rounded cursor-pointer hover:text-primary hover:border-primary" :class="borderClass">
    <div class="text-xl text-center font-bold">
      {{ group.name }}
    </div>
    <div class="text-sm font-mono text-center text-muted">
      {{ group.vmIp }}
    </div>
  </div>
</template>
  
<script setup lang="ts">
import { OrchestratorStatus, type Group } from '~~/shared/group'
const props = defineProps<{ group: Group }>()

const borderClass = computed(() => {
  switch (props.group.orchestratorStatus) {
    case OrchestratorStatus.ONLINE:
      return 'border-secondary'
    case OrchestratorStatus.OFFLINE:
      return 'border-error'
    case OrchestratorStatus.NOT_RESPONDING:
      return 'border-warning'
    default:
      return 'border-muted'
  }
})
</script>
  