import { computed, onScopeDispose, ref, toValue, watch } from 'vue'
import type { MaybeRefOrGetter } from 'vue'
import { fetchGroupUptime } from '~~/app/services/backend/health.service'
import { OrchestratorStatus } from '~~/shared/group'
import type { GroupHealthEvent } from '~~/shared/group'

const TICK_INTERVAL_MS = 1000

function isUptimeState(state: OrchestratorStatus): boolean {
  return state === OrchestratorStatus.ONLINE || state === OrchestratorStatus.NOT_RESPONDING
}

/**
 * Loads all-history uptime once, then accounts for elapsed time and health
 * transitions received through the group's existing health subscription.
 */
export function useGroupUptime(groupId: MaybeRefOrGetter<number | null | undefined>) {
  const groupStore = useGroupStore()
  const uptimeBase = ref(0)
  const downtimeBase = ref(0)
  const since = ref<Date | null>(null)
  const asOf = ref<Date | null>(null)
  const state = ref(OrchestratorStatus.UNKNOWN)
  const now = ref(Date.now())
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  let generation = 0

  const uptimeSeconds = computed(() => {
    const elapsed = asOf.value ? Math.max(0, now.value - asOf.value.getTime()) / 1000 : 0
    return uptimeBase.value + (isUptimeState(state.value) ? elapsed : 0)
  })
  const downtimeSeconds = computed(() => {
    const elapsed = asOf.value ? Math.max(0, now.value - asOf.value.getTime()) / 1000 : 0
    return downtimeBase.value + (state.value === OrchestratorStatus.OFFLINE ? elapsed : 0)
  })
  const totalSeconds = computed(() => uptimeSeconds.value + downtimeSeconds.value)
  const uptimePercentage = computed(() =>
    totalSeconds.value ? uptimeSeconds.value / totalSeconds.value * 100 : null
  )
  const downtimePercentage = computed(() =>
    totalSeconds.value ? downtimeSeconds.value / totalSeconds.value * 100 : null
  )

  function applyEvent(event: GroupHealthEvent, lastEventAt: { value: number }) {
    const eventTime = event.timestamp.getTime()
    if (eventTime <= lastEventAt.value) return

    if (event.state !== state.value && asOf.value) {
      const elapsed = Math.max(0, eventTime - asOf.value.getTime()) / 1000
      if (isUptimeState(state.value)) uptimeBase.value += elapsed
      else if (state.value === OrchestratorStatus.OFFLINE) downtimeBase.value += elapsed
      asOf.value = event.timestamp
      state.value = event.state
    }

    lastEventAt.value = eventTime
  }

  watch(
    () => toValue(groupId),
    (id, _previousId, onCleanup) => {
      const requestGeneration = ++generation
      uptimeBase.value = 0
      downtimeBase.value = 0
      since.value = null
      asOf.value = null
      state.value = OrchestratorStatus.UNKNOWN
      error.value = null
      isLoading.value = id !== null && id !== undefined

      if (id === null || id === undefined) {
        return
      }

      const initialGroupState = groupStore.groups.find(group => group.id === id)?.orchestratorStatus
        ?? OrchestratorStatus.UNKNOWN
      const pendingEvents: GroupHealthEvent[] = []
      let loaded = false
      const lastEventAt = { value: Number.NEGATIVE_INFINITY }
      const unsubscribe = groupStore.subscribeToHealthEvents((event) => {
        if (event.groupId !== id) return
        if (!loaded) pendingEvents.push(event)
        else applyEvent(event, lastEventAt)
      })

      onCleanup(() => {
        unsubscribe()
        if (generation === requestGeneration) generation++
      })

      void fetchGroupUptime(id).then((baseline) => {
        if (generation !== requestGeneration) return

        uptimeBase.value = baseline.uptimeSeconds
        downtimeBase.value = baseline.downtimeSeconds
        since.value = baseline.since
        asOf.value = baseline.asOf
        state.value = initialGroupState
        lastEventAt.value = baseline.asOf.getTime()
        now.value = Date.now()

        pendingEvents.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
        for (const event of pendingEvents) {
          if (event.timestamp.getTime() <= baseline.asOf.getTime()) {
            state.value = event.state
            continue
          }
          applyEvent(event, lastEventAt)
        }
        loaded = true
      }).catch((cause: unknown) => {
        if (generation !== requestGeneration) return
        error.value = cause instanceof Error ? cause : new Error(String(cause))
      }).finally(() => {
        if (generation === requestGeneration) isLoading.value = false
      })
    },
    { immediate: true }
  )

  const timer = setInterval(() => {
    now.value = Date.now()
  }, TICK_INTERVAL_MS)
  onScopeDispose(() => clearInterval(timer))

  return {
    uptimeSeconds,
    downtimeSeconds,
    uptimePercentage,
    downtimePercentage,
    since,
    asOf,
    state,
    isLoading,
    error
  }
}
