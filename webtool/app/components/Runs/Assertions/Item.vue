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
          <UIcon v-if="assertion.passed" name="lucide-check" class="ml-2 size-5 text-success" />
          <UIcon v-else name="lucide-x-circle" class="ml-2 size-5 text-error" />
          <div class="text-lg ml-2">
            {{ assertionName }}
          </div>
        </div>
        <UiTime :timestamp="assertion.createdAt" />
      </div>
      <div v-if="!assertion.passed">
        {{ assertion.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RunAssertion } from '~~/shared/run'

const props = defineProps<{
  assertion: RunAssertion
}>()

const assertionName = computed(() => props.assertion.name
  .replace(/-/g, ' ')
  .replace(/(^|\s)(\S)/g, (_, separator, char) => separator + char.toLocaleUpperCase()))
</script>