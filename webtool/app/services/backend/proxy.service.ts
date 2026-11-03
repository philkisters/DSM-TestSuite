import { type NetworkEvent, NetworkEventApiSchema, type NetworkStat, NetworkStatApiSchema } from '~~/shared/network'

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
