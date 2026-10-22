<template>
  <div class="flex flex-col">
    <div class="flex flex-col">
      <h1 class="text-center text-6xl font-bold my-4">Challenges</h1>
      <p class="text-center text-4xl mt-4">
        Here you can view and select challenges you want to run as your group.
      </p>
    </div>
    <USeparator class="my-4"/>
    <UiLoading v-if="loading" text="Loading Group Challenge results..." />
    <div v-else class="overflow-scroll flex flex-col">
      <div class="flex justify-end">
        <UInput
          v-model="keyFilter"
          placeholder="Filter Challenges"
          size="lg"
        />
      </div>
      <USeparator class="my-4"/>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        <UCard v-for="stat in filteredGroupChallengeStats" :key="stat.key" class="cursor-pointer hover:bg-muted" @click="emit('select', stat.key)">
          <template #header>
            <div class="flex items-center space-x-4">
              <UIcon v-if="stat.successes > 0" name="lucide-check-circle" color="primary" class="size-8 text-primary" />
              <UIcon v-else name="lucide-x-circle" color="warning" class="size-8 text-error" />
              <h2 class="text-2xl font-bold">{{ stat.title }}</h2>
            </div>
          </template>
          <template #default>
            <div class="flex flex-col space-y-2">
              <div class="flex w-full justify-between">
                <div>Runs/Passes</div>
                <div>{{ stat.tries }}/{{ stat.successes }}</div>
              </div>
              <div class="flex w-full justify-between">
                <div>First Pass</div>
                <UiTime v-if="stat.firstPass" :timestamp="stat.firstPass" />
                <div v-else>You never passed</div>
              </div>
              <div class="flex w-full justify-between">
                <div>Last Fail</div>
                <UiTime v-if="stat.lastFail" :timestamp="stat.lastFail" />
                <div v-else>You never failed</div>
              </div>
            </div>
          </template>
        </UCard>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import type { GroupChallengeStats } from '~~/shared/challenges'
import { getGroupChallengeStats } from '~~/app/services/backend/challenge.service'

const groupStore = useGroupStore()

const emit = defineEmits<{
  (e: 'select', challengeKey: string): void
}>()

const loading = ref(true)
const groupChallengeStats = ref<GroupChallengeStats[]>([])

const keyFilter = ref('')

const activeGroup = computed(() => groupStore.activeGroup?.id ?? -1)
const filteredGroupChallengeStats = computed(() => {
  if (!keyFilter.value) {
    return groupChallengeStats.value
  }
  return groupChallengeStats.value.filter(stat => stat.key.includes(keyFilter.value))
})

function fetchGroupChallengeStats(groupId: number) {
  loading.value = true
  getGroupChallengeStats(groupId).then(stats => {
    groupChallengeStats.value = stats.stats
    loading.value = false
  })
}

onMounted(() => {
  if (activeGroup.value !== -1) {
    fetchGroupChallengeStats(activeGroup.value)
  }
})

watch(activeGroup, (newGroupId) => {
  fetchGroupChallengeStats(newGroupId)
})

</script>