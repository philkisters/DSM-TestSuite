<template>
  <div class="flex flex-col text-center justify-start w-full p-4 ">
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
    <div class="flex overflow-y-scroll" v-if="challengeResults">
      <div class="flex-1 flex flex-col">
        <div class="text-lg text-center">
          Your results
        </div>
        <USeparator class="my-2" />
        <ChallengesRunInfo class="cursor-pointer hover:bg-muted rounded" v-for="run in challengeResults.runResults" :key="run.id" :run="run" @click="showRunDetails(run)" />
      </div>
      <div class="flex-1">
        <div class="text-lg">
          Group Overview 
        </div>
        <USeparator class="my-2" />
        <ChallengesGroupStatus
          v-for="groupId of challengeResults.groupResults.keys()"
          :key="groupId"
          :group-name="groupName(groupId)"
          :group-status="challengeResults.groupResults.get(groupId)!"
        />
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


const { challenge } = defineProps<{
  challenge: Challenge
}>()

const toast = useToast()
const groupStore = useGroupStore()
const challengeResults = ref<ChallengeResults | null>(null)

const activeRun = ref<Run | null>(null)

const groupName = computed(() => (groupId: number) => groupStore.groups.find(group => group.id === groupId)?.name ?? 'Unknown')

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
}
</script>