<template>
  <div class="flex flex-col text-center justify-start w-full min-w-0">
    <div class="flex justify-between items-center">
      <div class="flex-1 flex justify-start">
        <UButton icon="lucide-arrow-left" @click="$emit('close')">
          Back
        </UButton>
      </div>
      <div class="flex-1">
        <h1 class="text-center text-4xl font-bold align-middle">{{ challenge.title }}</h1>
      </div>
      <div class="flex-1"/>
    </div>
    <p class="text-center text-2xl">
      {{ challenge.description }}
    </p>
    <USeparator class="my-4" />
    <div class="flex justify-center">
      <UButton icon="lucide-play" @click="startRun">
        Start Challenge
      </UButton>
      <ChallengesStatus v-if="challengeResults" :status="challengeResults.groupResults.get(groupStore.activeGroup!.id)!.status" class="ml-4" size="xl"/>
    </div>
    <USeparator class="my-4" />
    <div class="flex overflow-y-scroll gap-4" v-if="challengeResults">
      <div class="flex-1 flex flex-col">
        <div class="flex flex-wrap items-center justify-between gap-3 px-2">
          <h2 class="text-lg">
            Group Overview
          </h2>
          <div class="flex gap-2">
            <UButton
              icon="lucide-clock"
              color="primary"
              variant="ghost"
              class="text-primary"
              title="Order by first success"
              aria-label="Order by first success"
            />
          </div>
        </div>
        <USeparator class="my-2" />
        <ChallengesRunInfo class="cursor-pointer hover:bg-muted rounded" v-for="run in challengeResults.runResults" :key="run.id" :run="run" @click="showRunDetails(run)" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex flex-wrap items-center justify-between gap-3 px-2">
          <h2 class="text-lg">
            Group Overview
          </h2>
          <div class="flex gap-2">
            <UButton
              icon="lucide-clock"
              :color="ranking === 'firstSuccess' ? 'primary' : 'neutral'"
              variant="ghost"
              :class="{ 'text-primary': ranking === 'firstSuccess' }"
              @click="ranking = 'firstSuccess'"
              title="Order by first success"
              aria-label="Order by first success"
            />
            <UButton
              icon="lucide-mail"
              :color="ranking === 'messages' ? 'primary' : 'neutral'"
              variant="ghost"
              :class="{ 'text-primary': ranking === 'messages' }"
              @click="ranking = 'messages'"
              title="Order by fewest messages"
              aria-label="Order by fewest messages"
            />
            <UButton
              icon="lucide-hourglass"
              :color="ranking === 'duration' ? 'primary' : 'neutral'"
              variant="ghost"
              :class="{ 'text-primary': ranking === 'duration' }"
              @click="ranking = 'duration'"
              title="Order by shortest duration"
              aria-label="Order by shortest duration"
            />
          </div>
        </div>
        <USeparator class="my-2" />
        <ChallengesGroupStatus
          v-for="[groupId, result] of sortedGroupResults"
          :key="groupId"
          :group-name="groupName(groupId)"
          :group-status="result"
          :ranking="ranking"
        />
        <p v-if="sortedGroupResults.length === 0" class="p-4 text-sm text-muted">
          {{ ranking === 'firstSuccess' ? 'No groups available.' : 'No successful groups yet.' }}
        </p>
      </div>
    </div>
    <UiLoading v-else text="Loading your results..." />
    <template v-if="activeRun && ['pending', 'running'].includes(activeRun.status ?? '')">
      <RunsEventStream :run-id="activeRun.id" :network-id="activeRun.networkId!" :run-steps="challenge.steps" @close="activeRun = null" @update-status="updateStatus" />
    </template>
    <div v-if="activeRun && ['passed', 'failed', 'error'].includes(activeRun.status ?? '')">
      <RunsAssertionPanel :run-id="activeRun.id" @close="activeRun = null" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { getChallengeResults } from '~~/app/services/backend/challenge.service'
import { createRun } from '~~/app/services/backend/run.service'

import type { Challenge, ChallengeResults } from '~~/shared/challenges'
import type { Run } from '~~/shared/run'
import { OrchestratorStatus } from '~~/shared/group'
import { sortChallengeGroups, type ChallengeRanking } from '~~/app/utils/challengeRanking'


const { challenge } = defineProps<{
  challenge: Challenge
}>()

const toast = useToast()
const groupStore = useGroupStore()
const challengeResults = ref<ChallengeResults | null>(null)

const activeRun = ref<Run | null>(null)

const groupName = computed(() => (groupId: number) => groupStore.groups.find(group => group.id === groupId)?.name ?? 'Unknown')

const ranking = ref<ChallengeRanking>('firstSuccess')
const sortedGroupResults = computed(() =>
  sortChallengeGroups(challengeResults.value?.groupResults ?? new Map(), ranking.value)
)

defineEmits<{
  (e: 'close'): void
}>()

onMounted(async () => {
  refreshChallengeResults()
})

watch(() => challenge, () => {
  refreshChallengeResults()
})

async function refreshChallengeResults() {
  if (groupStore.activeGroup) {
    challengeResults.value = await getChallengeResults(challenge.id, groupStore.activeGroup.id)
  }
}

function startRun() {
  if (!groupStore.activeGroup) return

  if (groupStore.activeGroup.orchestratorStatus !== OrchestratorStatus.ONLINE) {
    toast.add({ color: 'error', title: 'Orchestrator not online', description: 'Ensure that your orchestrator is reachable to start a challange' })
    return
  }

  createRun(groupStore.activeGroup.id, challenge.id)
    .then(run => {
      challengeResults.value!.runResults = [run, ...(challengeResults.value?.runResults ?? [])]
      activeRun.value = run
    })
    .catch(err => {
      toast.add({ color: 'error', title: 'Error', description: 'Failed to start run' })
      console.error('Failed to start run:', err)
    })
}

function showRunDetails(run: Run) {
  activeRun.value = run
}

function updateStatus(runId: string, status: 'running' | 'passed' | 'failed' | 'error') {
  const run = challengeResults.value?.runResults.find(r => r.id === runId)
  if (run) {
    run.status = status
  }
  if (status !== 'running') {
    refreshChallengeResults().catch((err) => {
      toast.add({ color: 'error', title: 'Error', description: 'Failed to refresh challenge results' })
      console.error('Failed to refresh challenge results:', err)
    })
  }
}
</script>