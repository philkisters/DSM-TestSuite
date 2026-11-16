<template>
  <div class="flex flex-col space-y-2">
    <RunsAssertionsItem v-for="assertion in assertions" :key="assertion.id" :assertion="assertion" />
  </div>
</template>

<script setup lang="ts">
import type { RunEventResult } from '~~/shared/run'

const props = defineProps<{
  assertions: RunEventResult[]
}>()
</script>