<template>
  <div
    class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-default p-3 mb-2 text-left"
    :class="{
      'border-error': !success,
      'border-success': success
    }"
  >
    <div class="flex min-w-0 items-center gap-2">
      <h3 class="truncate font-semibold">
        {{ props.groupName }}
      </h3>
    </div>
    <div class="text-sm text-muted text-right">
      <template v-if="success">
        <div class="flex flex-wrap justify-end gap-x-3">
          <div class="flex items-center gap-1">
            <UIcon name="lucide-mail" />
            <span>{{ success[0] == null ? '---' : `${success[0]} messages` }}</span>
          </div>
          <div class="flex items-center gap-1">
            <UIcon name="lucide-hourglass" />
            <span>{{ success[1] == null ? '---' : `${formatDuration(success[1])} s` }}</span>
          </div>
          <div class="flex items-center gap-1">
            <UIcon name="lucide-clock" />
            <UiTime :timestamp="success[2]" />
          </div>
        </div>
      </template>
      <template v-else-if="props.groupStatus.status === 'passed' && props.ranking !== 'firstSuccess'">
        {{ props.ranking === 'messages' ? 'Message count unavailable' : 'Duration unavailable' }}
      </template>
      <UiTime
        v-else-if="props.groupStatus.timestamp"
        :timestamp="props.groupStatus.timestamp"
      />
      <span v-else>No run available</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GroupChallengeResult } from '~~/shared/challenges'
import { rankingSuccess, type ChallengeRanking } from '~~/app/utils/challengeRanking'
import { formatDuration } from '~~/app/utils/challengeMetrics'

const props = defineProps<{
  groupName: string
  groupStatus: GroupChallengeResult
  ranking: ChallengeRanking
}>()

const success = computed(() => rankingSuccess(props.groupStatus, props.ranking))
</script>
