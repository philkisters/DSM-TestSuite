import type { Run } from '../../shared/run'

export function runMessageCount(run: Run): number | undefined {
  const count = run.metrics?.message_count
  return typeof count === 'number' && Number.isFinite(count) ? count : undefined
}

export function runDuration(run: Run): number | undefined {
  return run.finishedAt === undefined
    ? undefined
    : (run.finishedAt.getTime() - run.startedAt.getTime()) / 1000
}

export function formatDuration(seconds: number): string {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(seconds)
}
