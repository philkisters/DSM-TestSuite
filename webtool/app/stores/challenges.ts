import { getChallenges } from '~/services/backend/challenge.service'
import type { Challenge } from '~~/shared/challenges'

export const useChallengeStore = defineStore('challenge', {
  state: () => {
    return {
      challenges: [] as Challenge[],
      completedChallenges: [] as Challenge[],
      isLoading: false,
      initialized: false,
    }
  },
  actions: {
    async fetchChallenges() {
      this.isLoading = true
      try {
        this.challenges = await getChallenges()
      } catch (error) {
        useToast().add({ title: 'Error', description: 'Failed to fetch Challenges', color: 'error' })
        console.error('Failed to fetch Challenges:', error)
      } finally {
        this.isLoading = false
        this.initialized = true
      }
    },

  }
})