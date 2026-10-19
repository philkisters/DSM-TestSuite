import { z } from 'zod'
import { wireDate } from '~~/shared/wireDate'

export const RunStatusSchema = z.enum(['pending', 'running', 'passed', 'failed', 'error'])

export const RunApiSchema = z.object({
  id: z.string(),
  group_id: z.number(),
  challenge_id: z.number(),
  network_id: z.string().nullish(),
  seed: z.number().nullish(),
  status: RunStatusSchema,
  started_at: wireDate,
  finished_at: wireDate.nullish(),
  metrics: z.record(z.string(), z.unknown()).nullish(),
}).transform((r) => ({
  id: r.id,
  groupId: r.group_id,
  challengeId: r.challenge_id,
  networkId: r.network_id ?? undefined,
  seed: r.seed ?? undefined,
  status: r.status,
  startedAt: r.started_at,
  finishedAt: r.finished_at ?? undefined,
  metrics: r.metrics ?? undefined,
}))

export type RunStatus = z.infer<typeof RunStatusSchema>
export type Run = z.infer<typeof RunApiSchema>
export type RunInput = z.input<typeof RunApiSchema>

export const RunEventApiSchema = z.object({
  run_id: z.string(),
  type: z.string(),
  data: z.record(z.string(), z.unknown()),
  timestamp: wireDate,
}).transform((e) => ({
  runId: e.run_id,
  type: e.type,
  data: e.data,
  timestamp: e.timestamp,
}))

export type RunEvent = z.infer<typeof RunEventApiSchema>

export const RunAssertionSchema = z.object({
  id: z.number(),
  run_id: z.string(),
  step_index: z.number(),
  name: z.string(),
  params: z.record(z.string(), z.unknown()).nullish(),
  passed: z.boolean(),
  message: z.string().nullish(),
  created_at: wireDate,
}).transform((a) => ({
  id: a.id,
  runId: a.run_id,
  stepIndex: a.step_index,
  name: a.name,
  params: a.params ?? undefined,
  passed: a.passed,
  message: a.message ?? undefined,
  createdAt: a.created_at,
}))

export type RunAssertion = z.infer<typeof RunAssertionSchema>
export type RunAssertionInput = z.input<typeof RunAssertionSchema>

export const RunEventStepDataSchema = z.object({
  index: z.number(),
  kind: z.enum(['action', 'assert']),
  name: z.string(),
  params: z.record(z.string(), z.unknown()).nullish(),
  status: RunStatusSchema,
  message: z.string().nullish(),
})
  .transform((d) => ({
    index: d.index,
    kind: d.kind,
    name: d.name,
    params: d.params ?? undefined,
    status: d.status,
    message: d.message ?? undefined,
  }))

export type RunEventStepData = z.infer<typeof RunEventStepDataSchema>