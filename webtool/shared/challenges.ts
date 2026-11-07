import { z } from "zod"
import { wireDate } from "~~/shared/wireDate"
import { RunApiSchema } from "~~/shared/run"

export const ChallengeApiSchema = z.object({
  id: z.number(),
  key: z.string(),
  title: z.string(),
  steps: z.number(),
  description: z.string().optional(),
  archived: z.boolean()
})


type ChallengeApiModel = z.infer<typeof ChallengeApiSchema>
type ChallengeApiInput = z.input<typeof ChallengeApiSchema>


export class Challenge implements ChallengeApiModel {
  id: number
  key: string
  title: string
  steps: number
  description?: string
  archived: boolean

  constructor(data: ChallengeApiInput) {
    this.id = data.id
    this.key = data.key
    this.title = data.title
    this.steps = data.steps
    this.description = data.description
    this.archived = data.archived
  }
}

export const ChallengeSuccessApiSchema = z.tuple([
  z.number().int().nullable(),
  z.number().nullable(),
  wireDate,
])

const LowestMessageCountApiSchema = z.tuple([
  z.number().int(),
  z.number().nullable(),
  wireDate,
])

const ShortestDurationApiSchema = z.tuple([
  z.number().int().nullable(),
  z.number(),
  wireDate,
])

export const GroupChallengeResultApiSchema = z.object({
  status: z.enum(['passed', 'failed']),
  timestamp: wireDate.nullable(),
  first_success: ChallengeSuccessApiSchema.nullable(),
  lowest_message_count: LowestMessageCountApiSchema.nullable(),
  shortest_duration: ShortestDurationApiSchema.nullable(),
}).transform((r) => ({
  status: r.status,
  timestamp: r.timestamp ?? undefined,
  firstSuccess: r.first_success ?? undefined,
  lowestMessageCount: r.lowest_message_count ?? undefined,
  shortestDuration: r.shortest_duration ?? undefined,
}))

export const ChallengeResultsApiSchema = z.object({
  group_results: z.record(z.string(), GroupChallengeResultApiSchema),
  run_results: RunApiSchema.array(),
}).transform((r) => ({
  groupResults: new Map(
    Object.entries(r.group_results).map(([groupId, result]) => [Number(groupId), result] as const)
  ),
  runResults: r.run_results,
}))

export type GroupChallengeResult = z.infer<typeof GroupChallengeResultApiSchema>
export type ChallengeResults = z.infer<typeof ChallengeResultsApiSchema>

export const GroupChallengeStatsApiSchema = z.object({
  key: z.string(),
  week: z.string(),
  title: z.string(),
  tries: z.number(),
  successes: z.number(),
  first_pass: wireDate.nullable().default(null),
  last_fail: wireDate.nullable().default(null),
}).strict().transform(gc => {
  return {
    key: gc.key,
    week: gc.week,
    title: gc.title,
    tries: gc.tries,
    successes: gc.successes,
    firstPass: gc.first_pass,
    lastFail: gc.last_fail,
  }
})

export const GroupChallengeStatsResultsApiSchema = z.object({
  group_id: z.number(),
  stats: z.array(GroupChallengeStatsApiSchema),
}).strict().transform(gcs => {
  return {
    groupId: gcs.group_id,
    stats: gcs.stats,
  }
})

export type GroupChallengeStats = z.infer<typeof GroupChallengeStatsApiSchema>
export type GroupChallengeStatsResults = z.infer<typeof GroupChallengeStatsResultsApiSchema>