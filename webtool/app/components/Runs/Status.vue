<template>
  <UBadge :icon="statusIcon" size="lg" :color="statusColor" variant="solid">{{ props.status }}</UBadge>
</template>
<script setup lang="ts">
import type { RunStatus } from '~~/shared/run'

const props = defineProps<{
  status: RunStatus
}>()
const statusIcon = computed(() => {
  switch (props.status) {
    case 'pending':
      return 'lucide-clock'
    case 'running':
      return 'lucide-play'
    case 'passed':
      return 'lucide-check'
    case 'failed':
      return 'lucide-x'
    default:
      return 'lucide-ban'
  }
})

const statusColor = computed(() => {
  switch (props.status) {
    case 'pending':
      return 'secondary'
    case 'running':
      return 'primary'
    case 'passed':
      return 'success'
    default:
      return 'error'
  }
})
</script>