<template>
  <div class="flex p-2 border rounded-md border-muted">
    <div class="flex flex-col space-y-1 px-2 border-r border-muted">
      <div class="text-sm">Step</div>
      <div class="text-2xl">
        {{ assertion.stepIndex }}
      </div>
    </div>
    <div class="flex flex-col space-y-1 px-2 w-full">
      <div class="flex items-center justify-between space-x-4">
        <div class="flex items-center">
          <UIcon v-if="isAssertion && assertion.passed" name="lucide-check" class="ml-2 size-5 text-success" />
          <UIcon v-else name="lucide-x-circle" class="ml-2 size-5 text-error" />
          <div class="text-lg ml-2">
            {{ assertionName }}
          </div>
          <UBadge v-if="isError" variant="subtle" color="red" class="ml-2">Error</UBadge>
        </div>
        <UiTime :timestamp="assertion.createdAt" />
      </div>
      <div v-if="displayMessage">
        {{ displayMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RunEventResult } from '~~/shared/run'

const props = defineProps<{
  assertion: RunEventResult
}>()

const isAssertion = computed(() => props.assertion.type === 'assertion')
const isError = computed(() => props.assertion.type === 'error')

const displayMessage = computed(() => {
  if (isAssertion.value && !props.assertion.passed) {
    return props.assertion.message
  }
  if (isError.value) {
    return `${props.assertion.errorCode ? `[${props.assertion.errorCode}] ` : ''}${props.assertion.errorText}`
  }
  return undefined
})

const assertionName = computed(() => props.assertion.name
  .replace(/-/g, ' ')
  .replace(/(^|\s)(\S)/g, (_, separator, char) => separator + char.toLocaleUpperCase()))
</script>