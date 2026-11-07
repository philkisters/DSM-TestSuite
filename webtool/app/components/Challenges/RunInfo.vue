<template>
  <div
    class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-default p-3 mb-2 text-left"
    :class="{
      'border-success': props.run.status === 'passed',
      'border-error': props.run.status === 'failed' || props.run.status === 'error'
    }"
  >
    <RunsStatus :status="props.run.status" />
    <div class="flex flex-wrap justify-end gap-x-3 text-sm text-muted">
      <div class="flex items-center gap-1">
        <UIcon name="lucide-mail" />
        <span>{{ messageCount == null ? '---' : `${messageCount} messages` }}</span>
      </div>
      <div class="flex items-center gap-1">
        <UIcon name="lucide-hourglass" />
        <span>{{ duration == null ? '---' : `${formatDuration(duration)} s` }}</span>
      </div>
      <div class="flex items-center gap-1">
        <UIcon name="lucide-clock" />
        <UiTime :timestamp="timestamp" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Run } from '~~/shared/run'
import { formatDuration, runDuration, runMessageCount } from '~~/app/utils/challengeMetrics'

const props = defineProps<{
  run: Run
}>()

const messageCount = computed(() => runMessageCount(props.run))
const duration = computed(() => runDuration(props.run))

const timestamp = computed(() => {
  switch (props.run.status) {
    case 'pending':
    case 'running':
      return props.run.startedAt
    default:
      return props.run.finishedAt ?? props.run.startedAt
  }
})
</script>
