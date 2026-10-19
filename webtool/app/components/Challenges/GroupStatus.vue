<template>
  <div class="flex items-center w-full p-2">
    <div class="flex-1 flex flex-col text-center">
      <h2 class="text-center text-xl font-bold">{{ props.groupName }}</h2>
    </div>
    <div>
      <ChallengesStatus class="flex-shrink" :status="props.groupStatus.status" size="lg"/>
    </div>
    <div v-if="props.groupStatus.timestamp" class="flex-1 flex flex-col text-center">
      <UiTime :timestamp="props.groupStatus.timestamp" />
    </div>
    <div v-else class="flex-1 flex flex-col text-center">
      No run available
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GroupChallengeResult } from '~~/shared/challenges'

const props = defineProps<{
  groupName: string
  groupStatus: GroupChallengeResult
}>()
</script>