<template>
  <div class="flex items-center w-full p-2">
    <RunsStatus :status="props.run.status" />
    <div class="flex-1 flex flex-col text-center">
      <UiTime :timestamp="timestamp" />
    </div>
  </div>
</template>
<script setup lang="ts">
import type { Run } from '~~/shared/run'

const props = defineProps<{
  run: Run
}>()

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