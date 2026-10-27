<template>
  <UCard class="w-full max-w-xl">
    <div class="flex flex-col gap-6 sm:flex-row sm:items-center">
      <div
        class="mx-auto grid size-40 shrink-0 place-items-center rounded-full"
        :style="chartStyle"
        role="img"
        :aria-label="chartLabel"
      >
        <div class="grid size-28 place-content-center rounded-full bg-default text-center">
          <template v-if="uptimePercentage !== null">
            <span class="text-3xl font-bold tabular-nums">
              {{ uptimePercentage.toFixed(2) }}%
            </span>
            <span class="text-xs text-muted">uptime</span>
          </template>
          <span
            v-else
            class="text-sm text-muted"
          >No data</span>
        </div>
      </div>

      <div class="min-w-0 flex-1">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold">
              Group uptime
            </h2>
            <p class="text-sm text-muted">
              All recorded history
            </p>
          </div>
          <UBadge
            :color="statusColor"
            variant="subtle"
          >
            {{ formattedStatus }}
          </UBadge>
        </div>

        <div
          v-if="isLoading"
          class="space-y-3"
          aria-live="polite"
        >
          <USkeleton class="h-5 w-full" />
          <USkeleton class="h-5 w-3/4" />
        </div>
        <UAlert
          v-else-if="error"
          color="error"
          variant="subtle"
          title="Couldn't load uptime"
          :description="error.message"
        />
        <div
          v-else
          class="space-y-3"
        >
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-2">
              <span class="size-2.5 rounded-full bg-green-500" />
              <span>Uptime</span>
            </div>
            <span class="text-right font-medium tabular-nums">
              {{ formatDuration(uptimeSeconds) }}
              <span class="text-muted">({{ formatPercentage(uptimePercentage) }})</span>
            </span>
          </div>
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-2">
              <span class="size-2.5 rounded-full bg-red-500" />
              <span>Downtime</span>
            </div>
            <span class="text-right font-medium tabular-nums">
              {{ formatDuration(downtimeSeconds) }}
              <span class="text-muted">({{ formatPercentage(downtimePercentage) }})</span>
            </span>
          </div>
          <p
            v-if="since"
            class="border-t border-default pt-3 text-xs text-muted"
          >
            Tracking since {{ since.toLocaleString() }}
          </p>
        </div>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CSSProperties } from 'vue'
import { useGroupUptime } from '~~/app/composables/useGroupUptime'
import { OrchestratorStatus } from '~~/shared/group'

const props = defineProps<{ groupId: number }>()
const {
  uptimeSeconds,
  downtimeSeconds,
  uptimePercentage,
  downtimePercentage,
  since,
  state,
  isLoading,
  error
} = useGroupUptime(() => props.groupId)

const formattedStatus = computed(() => state.value.replaceAll('_', ' ').toLowerCase())
const statusColor = computed(() => {
  switch (state.value) {
    case OrchestratorStatus.ONLINE:
      return 'success'
    case OrchestratorStatus.NOT_RESPONDING:
      return 'warning'
    case OrchestratorStatus.OFFLINE:
      return 'error'
    default:
      return 'neutral'
  }
})

const chartStyle = computed<CSSProperties>(() => {
  if (uptimePercentage.value === null) {
    return {
      background: 'var(--color-gray-300)'
    }
  }

  const uptime = uptimePercentage.value
  return {
    background: `conic-gradient(var(--color-green-500) 0% ${uptime}%, var(--color-red-500) ${uptime}% 100%)`
  }
})

const chartLabel = computed(() => uptimePercentage.value === null
  ? 'No uptime history available'
  : `Uptime ${formatPercentage(uptimePercentage.value)}, downtime ${formatPercentage(downtimePercentage.value)}`
)

function formatPercentage(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(2)}%`
}

function formatDuration(seconds: number): string {
  let remaining = Math.floor(seconds)
  const days = Math.floor(remaining / 86400)
  remaining %= 86400
  const hours = Math.floor(remaining / 3600)
  remaining %= 3600
  const minutes = Math.floor(remaining / 60)
  const secs = remaining % 60

  if (days) return `${days}d ${hours}h ${minutes}m`
  if (hours) return `${hours}h ${minutes}m ${secs}s`
  if (minutes) return `${minutes}m ${secs}s`
  return `${secs}s`
}
</script>
