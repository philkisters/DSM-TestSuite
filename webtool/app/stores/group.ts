import type { Group } from '~~/shared/group'
import { getGroups, createGroup } from '~~/app/services/backend/group.service'
import { fetchGroupHealthStatus, subscribeToGroupHealth } from '~~/app/services/backend/health.service'

export const useGroupStore = defineStore('group', {
  state: () => {
    return {
      groups: [] as Group[],
      activeGroup: null as Group | null,
      isLoading: false,
      initialized: false,
      unsubscribeHealth: null as (() => void) | null
    }
  },
  actions: {
    startHealthUpdates() {
      if (this.unsubscribeHealth) return
      this.unsubscribeHealth = subscribeToGroupHealth((status) => {
        const group = this.groups.find(g => g.id === status.groupId)
        if (group) group.orchestratorStatus = status.state
        else this.fetchGroups()
      })
    },
    stopHealthUpdates() {
      this.unsubscribeHealth?.()
      this.unsubscribeHealth = null
    },
    setActiveGroup(groupId: number) {
      this.activeGroup = this.groups.find(g => g.id === groupId) || null
    },
    removeActiveGroup() {
      this.activeGroup = null
    },
    async fetchGroups() {
      this.isLoading = true
      try {
        this.groups = await getGroups()
        const healthStatus = await fetchGroupHealthStatus()

        for (const group of this.groups) {
          const status = healthStatus.find(h => h.groupId === group.id)
          if (status) {
            group.orchestratorStatus = status.state
          }
        }
      } catch (error) {
        useToast().add({ title: 'Error', description: 'Failed to fetch groups', color: 'error' })
        console.error('Failed to fetch groups:', error)
      } finally {
        this.isLoading = false
        this.initialized = true
      }
    },
    async createGroup(groupData: Partial<Group>) {
      this.isLoading = true
      try {
        const newGroup = await createGroup(groupData)
        await this.fetchGroups()
      } catch (error) {
        useToast().add({ title: 'Error', description: 'Failed to create group', color: 'error' })
        console.error('Failed to create group:', error)
      } finally {
        this.isLoading = false
      }
    }
  }
})