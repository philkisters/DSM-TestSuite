import { z } from 'zod'
import { wireDate } from '~~/shared/wireDate'

export const GroupApiSchema = z.object({
  id: z.number(),
  name: z.string(),
  vm_ip: z.string(),
  created_at: wireDate.default(() => new Date()),
}).strict().transform((g) => ({
  id: g.id,
  name: g.name,
  vmIp: g.vm_ip,
  orchestratorStatus: OrchestratorStatus.UNKNOWN,
  createdAt: g.created_at,
}))

export type GroupModel = z.infer<typeof GroupApiSchema>
export type GroupInput = z.input<typeof GroupApiSchema>

export const GroupHealthStatusApiSchema = z.object({
  id: z.number(),
  group_id: z.number(),
  state: z.string(),
  failures: z.number(),
  timestamp: wireDate.default(() => new Date()),
}).strict().transform((g) => ({
  id: g.id,
  groupId: g.group_id,
  state: OrchestratorStatus[g.state as keyof typeof OrchestratorStatus],
  failures: g.failures,
  timestamp: g.timestamp,
}))

export const GroupHealthEventApiSchema = z.object({
  group_id: z.number(),
  state: z.string(),
  failures: z.number(),
  timestamp: wireDate.default(() => new Date()),
}).strict().transform((g) => ({
  groupId: g.group_id,
  state: OrchestratorStatus[g.state as keyof typeof OrchestratorStatus],
  failures: g.failures,
  timestamp: g.timestamp,
}))

export type GroupHealthEvent = z.infer<typeof GroupHealthEventApiSchema>

export type GroupHealthStatusModel = z.infer<typeof GroupHealthStatusApiSchema>
export type GroupHealthStatusInput = z.input<typeof GroupHealthStatusApiSchema>

export enum OrchestratorStatus {
  ONLINE = 'ONLINE',
  NOT_RESPONDING = 'NOT_RESPONDING',
  OFFLINE = 'OFFLINE',
  UNKNOWN = 'UNKNOWN'
}

export class Group implements GroupModel {
  id!: number
  name!: string
  vmIp!: string
  orchestratorStatus!: OrchestratorStatus
  createdAt!: Date

  constructor(data: GroupModel) {
    Object.assign(this, GroupApiSchema.parse(data))
  }
}

export class GroupHealthStatus implements GroupHealthStatusModel {
  id!: number
  groupId!: number
  state!: OrchestratorStatus
  failures!: number
  timestamp!: Date

  constructor(data: GroupHealthStatusModel) {
    Object.assign(this, GroupHealthStatusApiSchema.parse(data))
  }
}

