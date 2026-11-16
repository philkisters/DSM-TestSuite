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
  >
  <div v-if="!showPlacementDetailed" class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-sm tabular-nums cursor-pointer" @click="showPlacementDetailed = true">
    <UIcon name="lucide-chevron-down" class="rotate-270" />
    <span :aria-label="`${overview.totalPassedChallenges} of ${overview.challengesByStatus.length} challenges passed`">
      {{ overview.totalPassedChallenges }} / {{ overview.challengesByStatus.length }} passed
    </span>
    <GroupChallengeRow :first="sumPlaces(overview.firstPlaces)" :second="sumPlaces(overview.secondPlaces)" :third="sumPlaces(overview.thirdPlaces)" />
  </div>
  <div v-if="showPlacementDetailed" class="flex align-top justify-between gap-x-4 cursor-pointer" @click="showPlacementDetailed = false">
    <div>
        <UIcon name="lucide-chevron-down" />
    </div>
    <div class="flex flex-col">
      <div class="flex gap-x-2 justify-between items-center align-center">
        <UIcon name="lucide-clock" class="size-5 mr-4" />
        <GroupChallengeRow :first="overview.firstPlaces.time" :second="overview.secondPlaces.time" :third="overview.thirdPlaces.time" />
      </div>
      <div class="flex gap-x-2 justify-between items-center align-center my-2">
        <UIcon name="lucide-mail" class="size-5 mr-4" /> 
        <GroupChallengeRow :first="overview.firstPlaces.messages" :second="overview.secondPlaces.messages" :third="overview.thirdPlaces.messages" />
      </div>  
      <div class="flex gap-x-2 justify-between items-center align-center">
        <UIcon name="lucide-hourglass" class="size-5 mr-4" />
        <GroupChallengeRow :first="overview.firstPlaces.duration" :second="overview.secondPlaces.duration" :third="overview.thirdPlaces.duration" />
      </div>
    </div>
  </div>  
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
const showPlacementDetailed = ref(false)

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
