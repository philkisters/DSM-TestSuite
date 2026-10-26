<template>
  <div class="flex flex-col max-h-[50vh]">
    <USeparator class="my-2" />
    <div class="flex flex-row justify-between">
      <div class="flex-1">
      </div>
      <div class="flex-1 text-center text-lg">
        Run Report
      </div>
      <div class="flex-1  flex justify-end">
        <UButton icon="lucide-x" variant="ghost" color="neutral" @click="$emit('close')" />
      </div>
    </div>
    <USeparator class="my-2" />
    <RunsAssertionsList :assertions="runAssertions" class="overflow-scroll" />
  </div>
</template>
<script setup lang="ts">
import type { RunAssertion } from '~~/shared/run'
import { getRunAssertions } from '~~/app/services/backend/run.service'

const props = defineProps<{
  runId: string
}>()

const runAssertions = ref<RunAssertion[]>([])

onMounted(async () => {
  if (props.runId) {
    runAssertions.value = await getRunAssertions(props.runId)
  }
})

watch(() => props.runId, async (newRunId) => {
  if (newRunId) {
    runAssertions.value = await getRunAssertions(newRunId)
  }
})

defineEmits<{
  (e: 'close'): void
}>()
</script>