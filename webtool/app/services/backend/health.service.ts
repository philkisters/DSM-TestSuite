import { GroupHealthStatusApiSchema, GroupHealthEventApiSchema, type GroupHealthEvent, type GroupHealthStatus } from "~~/shared/group"

export async function fetchGroupHealthStatus(): Promise<GroupHealthStatus[]> {
    const response = await fetch('/testsuite/groups/health')
    const data = await response.json()
    return GroupHealthStatusApiSchema.array().parse(data) as GroupHealthStatus[]
}


export function subscribeToGroupHealth(
    onUpdate: (status: GroupHealthEvent) => void
): () => void {
    let ws: WebSocket | null = null
    let retryTimer: ReturnType<typeof setTimeout> | null = null
    let closed = false

    const connect = () => {
        const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
        const port = useRuntimeConfig().public.testsuiteWsPort
        const url = port
            ? `${protocol}://${location.hostname}:${port}/api/groups/health/ws`
            : `${protocol}://${location.host}/testsuite/groups/health/ws`
        ws = new WebSocket(url)
        ws.onmessage = (event) => {
            const parsed = GroupHealthEventApiSchema.safeParse(JSON.parse(event.data))
            if (parsed.success) onUpdate(parsed.data)
            else console.error('Invalid health event', parsed.error)
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
