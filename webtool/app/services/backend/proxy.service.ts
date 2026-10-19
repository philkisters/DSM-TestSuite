import { type NetworkEvent, NetworkEventApiSchema, type NetworkStat, NetworkStatApiSchema } from '../../../shared/network'

export async function getNetworks(): Promise<NetworkStat[]> {
  const response = await fetch('/proxy/networks')
  const data = await response.json()
  return NetworkStatApiSchema.parse(data) as NetworkStat[]
}

export function subscribeToNetworkEvents(
  networkId: string,
  onUpdate: (event: NetworkEvent) => void
): () => void {
  let ws: WebSocket | null = null
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let closed = false

  const connect = () => {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const port = useRuntimeConfig().public.proxyWsPort
    const url = port
      ? `${protocol}://${location.hostname}:${port}/api/ws/${networkId}`
      : `${protocol}://${location.host}/proxy/ws/${networkId}`
    ws = new WebSocket(url)
    ws.onmessage = (event) => {
      const parsed = NetworkEventApiSchema.safeParse(JSON.parse(event.data))
      if (parsed.success) onUpdate(parsed.data)
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
    ws?.close()
  }
}
