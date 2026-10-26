<template>
  <div class="flex flex-col min-w-0 w-full">
    <USeparator class="my-2" />
    <div class="flex max-h-[50vh] min-w-0 overflow-hidden">
      <div class="flex-1 flex flex-col min-w-0 min-h-0 p-4">
        <div class="flex flex-row justify-center">
          <div class="flex-5 text-center text-lg">
            Active Run Events
          </div>
        </div>
        <USeparator class="my-2" />
        <div class="py-2 shrink-0">
          <RunsStepsList :run-steps="props.runSteps" :event-data="runEvents"/>
        </div>
        <div class="flex flex-col-reverse flex-1 min-h-0 overflow-y-auto space-y-2 w-full">
          <RunsStepsDescription v-for="event in runEvents" :key="event.index" :step-data="event" /> 
        </div>
      </div>
      <USeparator class="my-2" orientation="vertical" />
      <NetworkPanel class="flex-3 min-w-0 min-h-0" :network-id="props.networkId" @close="emit('close')" />
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
