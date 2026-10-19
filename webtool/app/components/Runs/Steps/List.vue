<template>
  <ol class="flex items-center w-full">
    <li
      v-for="(step, i) in steps"
      :key="i"
      class="flex items-center"
      :class="i < steps.length - 1 ? 'flex-1' : ''"
    >
      <UTooltip :text="step.name ?? `Step ${i + 1}`">
        <span
          class="block size-3 shrink-0 rounded-full"
          :class="dotClass(step.status)"
        />
      </UTooltip>
      <span
        v-if="i < steps.length - 1"
        class="h-0.5 flex-1"
        :class="lineClass(step.status)"
      />
    </li>
  </ol>
</template>
<script setup lang="ts">
import type { RunEventStepData } from '~~/shared/run'

const props = defineProps<{
  eventData: RunEventStepData[],
  runSteps: number
}>()

const steps = computed(() => {
  const total = Math.max(props.runSteps, props.eventData.length)
  return Array.from({ length: total }, (_, i) => {
    const event = props.eventData.find(e => e.index === i) ?? props.eventData[i]
    return { name: event?.name, status: event?.status }
  })
})

function dotClass(status?: string) {
  switch (status) {
    case 'passed': return 'bg-success'
    case 'failed':
    case 'error': return 'bg-error'
    case 'running': return 'bg-primary animate-pulse'
    default: return 'bg-muted'
  }
}

function lineClass(status?: string) {
  if (status === 'passed') return 'bg-success'
  if (status === 'failed' || status === 'error') return 'bg-error'
  return 'bg-muted'
}
</script>
