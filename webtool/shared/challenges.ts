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

export const GroupChallengeResultApiSchema = z.object({
  status: z.enum(['passed', 'failed']),
  timestamp: wireDate.nullable(),
}).transform((r) => ({
  status: r.status,
  timestamp: r.timestamp ?? undefined,
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
