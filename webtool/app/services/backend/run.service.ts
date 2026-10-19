import { RunApiSchema, RunEventApiSchema, RunAssertionSchema, type Run, type RunEvent, type RunAssertion } from '~~/shared/run'

export async function createRun(groupId: number, challengeId: number): Promise<Run> {
  const response = await fetch('/testsuite/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ group_id: groupId, challenge_id: challengeId })
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Failed to create run (${response.status})`)
  }
  return RunApiSchema.parse(await response.json())
}

export async function getRunAssertions(runId: string): Promise<RunAssertion[]> {
  const response = await fetch(`/testsuite/runs/${runId}/events`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Failed to get run events (${response.status})`)
  }
  return (await response.json()).map((assertion: unknown) => RunAssertionSchema.parse(assertion))
}


const TERMINAL_STATUSES = ['passed', 'failed', 'error']

export function subscribeToRun(
  runId: string,
  onEvent: (event: RunEvent) => void
): () => void {
  let ws: WebSocket | null = null
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let closed = false

  const connect = () => {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const port = useRuntimeConfig().public.testsuiteWsPort
    const url = port
      ? `${protocol}://${location.hostname}:${port}/api/runs/${runId}/ws`
      : `${protocol}://${location.host}/testsuite/runs/${runId}/ws`
    ws = new WebSocket(url)
    ws.onmessage = (message) => {
      const parsed = RunEventApiSchema.safeParse(JSON.parse(message.data))
      if (!parsed.success) {
        console.error('Invalid run event', parsed.error)
        return
      }
      if (parsed.data.type === 'status' && TERMINAL_STATUSES.includes(String(parsed.data.data.status))) {
        closed = true
      }
      onEvent(parsed.data)
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
