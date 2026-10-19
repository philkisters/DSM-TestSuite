<template>
  <div class="flex flex-col min-h-96">
    <USeparator class="my-2" />
    <div class="flex">
      <div class="flex-1 flex flex-col p-4">
        <div class="flex flex-row justify-between">
          <div class="flex-1">
          </div>
          <div class="flex-1 text-center text-lg">
            Active Run Events
          </div>
          <div class="flex-1 flex justify-end">
          </div>
        </div>
        <USeparator class="my-2" />
        <div class="py-2">
          <RunsStepsList :run-steps="props.runSteps" :event-data="runEvents"/>
        </div>
        <div class="flex flex-col-reverse overflow-y-scroll space-y-2 w-full">
          <RunsStepsDescription v-for="event in runEvents" :key="event.index" :step-data="event" /> 
        </div>
      </div>
      <USeparator class="my-2" orientation="vertical" />
      <NetworkPanel :network-id="props.networkId" @close="emit('close')" />
    </div>
  </div>
</template>
<script setup lang="ts">
import type { RunEvent, RunEventStepData } from '~~/shared/run'
import { subscribeToRun } from '~~/app/services/backend/run.service'

const props = defineProps<{
  runId: string
  networkId: string
  runSteps: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updateStatus', runId: string, status: 'running' | 'passed' | 'failed' | 'error'): void
}>()

const unsubscribeRun = ref<(() => void) | null>(null)
const runEvents = ref<RunEventStepData[]>([])

watch(() => props.runId, async (newRunId) => {
  if (newRunId) {
    if (unsubscribeRun.value) {
      unsubscribeRun.value()
      unsubscribeRun.value = null
    }
    runEvents.value = []
    unsubscribeRun.value = subscribeToRun(newRunId, subscribe)
  }
})

onMounted(() => {
  unsubscribeRun.value = subscribeToRun(props.runId, subscribe)
})

function subscribe(event: RunEvent) {
  if (event.type === 'status') {
    emit('updateStatus', props.runId, event.data.status as 'running' | 'passed' | 'failed' | 'error')
    return
  }
  runEvents.value.push(event.data as RunEventStepData)
}

onBeforeUnmount(() => {
  unsubscribeRun.value?.()
  unsubscribeRun.value = null
})
</script>
