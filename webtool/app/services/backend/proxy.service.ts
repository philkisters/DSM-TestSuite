import { type NetworkEvent, NetworkEventApiSchema, type NetworkStat, NetworkStatApiSchema } from '~~/shared/network'
import { AckMessageSchema, ErrorMessageSchema, GetFingersRequestSchema, GetFingersResponseSchema, ListImagesRequestSchema, ListImagesResponseSchema, MessageCode, MessageSchema, PutImageMessageSchema, RequestImageSchema, type Message } from '~~/shared/protocol'

async function sendPeerMessage(request: Message, description: string, signal?: AbortSignal): Promise<Message> {
  const response = await fetch('/proxy/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal
  })
  if (!response.ok) throw new Error(`Failed to request ${description} (${response.status})`)

  const message = MessageSchema.parse(await response.json())
  if (message.sender.network_id !== request.receiver.network_id || message.sender.peer_id !== request.receiver.peer_id
    || message.receiver.network_id !== request.sender.network_id || message.receiver.peer_id !== request.sender.peer_id) {
    throw new Error(`${description} response has incorrect sender or receiver`)
  }
  if (message.code === MessageCode.ERROR) throw new Error(ErrorMessageSchema.parse(message).content.message)
  return message
}

export async function getPeerFingers(networkId: string, peerId: string, signal?: AbortSignal): Promise<string[]> {
  const request = GetFingersRequestSchema.parse({
    sender: { network_id: networkId, peer_id: 'Webtool' },
    receiver: { network_id: networkId, peer_id: peerId },
    code: MessageCode.GET_FINGERS_REQUEST,
    content: {}
  })
  const message = await sendPeerMessage(request, 'fingers', signal)
  const fingers = GetFingersResponseSchema.parse(message).content.fingers
  if (fingers.some(finger => finger.network_id !== networkId)) {
    throw new Error('Finger belongs to a different network')
  }
  return [...new Set(fingers.map(finger => finger.peer_id))]
}

export async function getPeerImages(networkId: string, peerId: string, signal?: AbortSignal): Promise<string[]> {
  const request = ListImagesRequestSchema.parse({
    sender: { network_id: networkId, peer_id: 'Webtool' },
    receiver: { network_id: networkId, peer_id: peerId },
    code: MessageCode.LIST_IMAGE_REQUEST,
    content: {}
  })
  const message = await sendPeerMessage(request, 'images', signal)
  return ListImagesResponseSchema.parse(message).content.images
}

export async function getPeerImage(networkId: string, peerId: string, imageId: string, signal?: AbortSignal): Promise<string> {
  const request = RequestImageSchema.parse({
    sender: { network_id: networkId, peer_id: 'Webtool' },
    receiver: { network_id: networkId, peer_id: peerId },
    code: MessageCode.REQUEST_IMAGE,
    content: { image_id: imageId }
  })
  const message = await sendPeerMessage(request, 'image', signal)
  const image = PutImageMessageSchema.parse(message).content
  if (image.image_id !== imageId) throw new Error('Image response has incorrect image ID')
  return image.image
}

export async function putPeerImage(networkId: string, peerId: string, imageId: string, image: string): Promise<void> {
  const request = PutImageMessageSchema.parse({
    sender: { network_id: networkId, peer_id: 'Webtool' },
    receiver: { network_id: networkId, peer_id: peerId },
    code: MessageCode.PUT_IMAGE,
    content: { image_id: imageId, image }
  })
  const message = await sendPeerMessage(request, 'put image')
  AckMessageSchema.parse(message)
}

export async function   getNetworks(): Promise<NetworkStat[]> {
  const response = await fetch('/proxy/networks')
  const data = await response.json()
  return NetworkStatApiSchema.parse(data) as NetworkStat[]
}

export function subscribeToNetworkEvents(
  networkId: string,
  onUpdate: (events: NetworkEvent[]) => void
): () => void {
  let ws: WebSocket | null = null
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  const settings = useSettingsStore()
  let closed = false
  let buffer: NetworkEvent[] = []
  let flushTimer: ReturnType<typeof setTimeout> | null = null

  // Events are delivered in batches so consumers update once per interval, not once per message.
  const flush = () => {
    flushTimer = null
    if (!buffer.length) return
    const batch = buffer
    buffer = []
    onUpdate(batch)
  }

  const connect = () => {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const port = useRuntimeConfig().public.proxyWsPort
    const url = port
      ? `${protocol}://${location.hostname}:${port}/api/ws/${networkId}`
      : `${protocol}://${location.host}/proxy/ws/${networkId}`
    ws = new WebSocket(url)
    ws.onmessage = (event) => {
      const parsed = NetworkEventApiSchema.safeParse(JSON.parse(event.data))
      if (parsed.success) {
        buffer.push(parsed.data)
        flushTimer ??= setTimeout(flush, settings.eventBatchIntervalMs)
      }
      else console.error('Invalid network event', parsed.error)
    }
    ws.onclose = () => {
      if (!closed) retryTimer = setTimeout(connect, 3000)
    }
    ws.onerror = () => ws?.close()
  }

  connect()

  return () => {
    closed = true
    if (retryTimer) clearTimeout(retryTimer)
    if (flushTimer) clearTimeout(flushTimer)
    buffer = []
    ws?.close()
  }
}
