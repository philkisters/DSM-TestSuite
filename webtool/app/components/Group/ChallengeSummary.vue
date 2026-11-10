<template>
  <div
    v-if="isLoading"
    class="text-sm text-muted"
    role="status"
  >
    Loading challenge results...
  </div>
  <div
    v-else-if="error"
    class="text-sm text-error"
    role="alert"
  >
    Couldn't load challenge results: {{ error }}
  </div>
  <div
    v-else-if="overview"
    class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-sm tabular-nums"
  >
    <span :aria-label="`${overview.totalPassedChallenges} of ${overview.challengesByStatus.length} challenges passed`">
      {{ overview.totalPassedChallenges }} / {{ overview.challengesByStatus.length }} passed
    </span>
    <span
      class="flex items-center gap-1"
      :aria-label="`${sumPlaces(overview.firstPlaces)} first places`"
    >
      <UIcon
        name="lucide-trophy"
        class="size-5 text-amber-500"
        aria-hidden="true"
      />
      {{ sumPlaces(overview.firstPlaces) }}
    </span>
    <span
      class="flex items-center gap-1"
      :aria-label="`${sumPlaces(overview.secondPlaces)} second places`"
    >
      <UIcon
        name="lucide-star"
        class="size-5 text-gray-400"
        aria-hidden="true"
      />
      {{ sumPlaces(overview.secondPlaces) }}
    </span>
    <span
      class="flex items-center gap-1"
      :aria-label="`${sumPlaces(overview.thirdPlaces)} third places`"
    >
      <UIcon
        name="lucide-star"
        class="size-5 text-amber-700"
        aria-hidden="true"
      />
      {{ sumPlaces(overview.thirdPlaces) }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { getGroupChallengeOverview } from '~~/app/services/backend/group.service'
import { sumPlaces } from '~~/app/utils/groupChallengeOverview'
import type { GroupChallengeOverview } from '~~/shared/group'

const props = defineProps<{ groupId: number }>()
const overview = ref<GroupChallengeOverview | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

onMounted(() => {
  watch(() => props.groupId, (groupId, _previousId, onCleanup) => {
    let active = true
    onCleanup(() => {
      active = false
    })
    overview.value = null
    error.value = null
    isLoading.value = true

    void getGroupChallengeOverview(groupId).then((result) => {
      if (active) overview.value = result
    }).catch((cause: unknown) => {
      if (active) error.value = cause instanceof Error ? cause.message : String(cause)
    }).finally(() => {
      if (active) isLoading.value = false
    })
  }, { immediate: true })
})
</script>
