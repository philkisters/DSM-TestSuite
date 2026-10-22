<template>
  <div class="flex flex-grow">
    <div class="flex flex-col border-r-muted border-r-1 min-w-48">
      <PanelButton v-for="challenge in challenges" :key="challenge.id" :class="{ 'bg-primary/30': selectedChallenge?.id === challenge.id }">
        <div class="flex flex-col" @click="setSelectedChallenge(challenge)">
          <div class="text-lg font-semibold">
            {{ challenge.title }}
          </div>
          <div class="text-muted text-sm font-mono">
            {{ challenge.key.split('/')[0] }}
          </div>
        </div>
      </PanelButton>
    </div>
    <div class="flex h-full flex-grow justify-center p-4">
      <ChallengesDefault v-if="!selectedChallenge" @select="setChallenge" />
      <ChallengesDetails v-else :challenge="selectedChallenge" @close="setSelectedChallenge(null)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Challenge } from '~~/shared/challenges'

const challengeStore = useChallengeStore()
const challenges = computed(() => challengeStore.challenges)

const selectedChallenge = ref<Challenge | null>(null)

function setChallenge(challengeKey: string) {
  selectedChallenge.value = challengeStore.getChallengeByKey(challengeKey)
}

function setSelectedChallenge(challenge: Challenge | null) {
  selectedChallenge.value = challenge
}


onMounted(() => {
  challengeStore.fetchChallenges()
})
</script>