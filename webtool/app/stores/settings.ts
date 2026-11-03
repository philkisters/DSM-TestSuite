export const useSettingsStore = defineStore('settings', {
  state: () => {
    return {
      maxNetworkEvents: 1000,
      eventBatchIntervalMs: 100,
      activeGroupId: null as number | null
    }
  }
})
