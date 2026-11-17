import { z } from 'zod'

export enum MessageCode {
  ERROR = -1,
  ACK = 0,
  JOIN = 1,
  LEAVE = 2,
  GET_NEIGHBORS_REQUEST = 3,
  GET_NEIGHBORS_RESPONSE = 4,
  GET_FINGERS_REQUEST = 5,
  GET_FINGERS_RESPONSE = 6,
  PUT_IMAGE = 7,
  LIST_IMAGE_REQUEST = 8,
  LIST_IMAGE_RESPONSE = 9,
  REQUEST_IMAGE = 10
}

export const IdentitySchema = z.object({
  network_id: z.string(),
  peer_id: z.string().min(1)
})

export const MessageSchema = z.object({
  sender: IdentitySchema,
  receiver: IdentitySchema,
  code: z.number().int(),
  content: z.record(z.string(), z.unknown())
})

export const GetFingersRequestSchema = MessageSchema.extend({
  code: z.literal(MessageCode.GET_FINGERS_REQUEST),
  content: z.object({})
})

export const GetFingersResponseSchema = MessageSchema.extend({
  code: z.literal(MessageCode.GET_FINGERS_RESPONSE),
  content: z.object({ fingers: z.array(IdentitySchema) })
})

export const ListImagesRequestSchema = MessageSchema.extend({
  code: z.literal(MessageCode.LIST_IMAGE_REQUEST),
  content: z.object({})
})

export const ListImagesResponseSchema = MessageSchema.extend({
  code: z.literal(MessageCode.LIST_IMAGE_RESPONSE),
  content: z.object({ images: z.array(z.string()) })
})

export const PutImageMessageSchema = MessageSchema.extend({
  code: z.literal(MessageCode.PUT_IMAGE),
  content: z.object({ image_id: z.string().min(1), image: z.string().min(1) })
})

export const RequestImageSchema = MessageSchema.extend({
  code: z.literal(MessageCode.REQUEST_IMAGE),
  content: z.object({ image_id: z.string().min(1) })
})

export const AckMessageSchema = MessageSchema.extend({
  code: z.literal(MessageCode.ACK),
  content: z.object({})
})

export const ErrorMessageSchema = MessageSchema.extend({
  code: z.literal(MessageCode.ERROR),
  content: z.object({ message: z.string() })
})

export type Message = z.infer<typeof MessageSchema>