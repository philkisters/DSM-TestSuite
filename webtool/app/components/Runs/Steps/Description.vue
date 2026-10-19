<template>
  <div class="flex items-center space-x-2 rounded p-2 border-primary" :class="stepColor">
    <div>
      <UIcon :name="icon" class="size-6" />
    </div>
    <div class="flex flex-col items-start">
      <div class="font-semibold">
        {{ stepName }}
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import type { RunEventStepData } from '~~/shared/run'

const props = defineProps<{
  stepData: RunEventStepData
}>()

const stepColor = computed(() => {
  if (props.stepData.kind === 'action') return 'bg-muted'
  if (props.stepData.status === 'failed') return 'bg-error'

  return 'bg-success text-inverted'
})
const stepName = computed(() => props.stepData.name
  .replace(/-/g, ' ')
  .replace(/(^|\s)(\S)/g, (_, separator, char) => separator + char.toLocaleUpperCase()))


const icon = computed(() => {
  if (props.stepData.kind === 'action') return 'lucide-waypoints'
  return 'lucide-circle-check-big'
})
</script>