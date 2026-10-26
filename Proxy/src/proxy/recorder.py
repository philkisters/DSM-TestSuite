import asyncio
import json
import logging
from datetime import datetime, timezone

import asyncpg

log = logging.getLogger("recorder")

COLUMNS = ["ts", "network_id", "src_peer", "dst_peer", "code",
           "size", "status", "delay_ms", "content"]
REGISTRY_COLUMNS = ["ts", "network_id", "peer_id", "event", "host", "port", "peer_data", "message"]


class Recorder:
    """Non-blocking event recorder: forwarding enqueues, one task batches to Postgres."""

    def __init__(self, dsn: str, max_queue: int = 10000, flush_interval: float = 0.1, batch: int = 500,
                 on_event=None):
        self.dsn = dsn
        self.queue: asyncio.Queue = asyncio.Queue(max_queue)
        self.flush_interval = flush_interval
        self.batch = batch
        self.dropped = 0
        self.on_event = on_event
        self.registry_queue: asyncio.Queue = asyncio.Queue(max_queue)
        self._task: asyncio.Task | None = None

    def record(self, *, network_id, src_peer=None, dst_peer=None, code=None, size=0, status, delay_ms=None, content=None) -> None:
        row = (datetime.now(timezone.utc), network_id, src_peer, dst_peer, code,
               size, status, delay_ms,
               json.dumps(content) if content is not None else None)
        if self.on_event:
            self.on_event(network_id, {
                "type": "message", "ts": row[0].isoformat(), "networkId": network_id,
                "src": src_peer, "dst": dst_peer, "code": code, "size": size,
                "status": status, "delayMs": delay_ms, "content": content})
        try:
            self.queue.put_nowait(row)
        except asyncio.QueueFull:
            self.dropped += 1

    def record_registry(self, *, ts, network_id, peer_id, event, host=None, port=None, peer_data=None, message=None) -> None:
        try:
            self.registry_queue.put_nowait((ts, network_id, peer_id, event, host, port,
                                            json.dumps(peer_data) if peer_data else None, message))
        except asyncio.QueueFull:
            self.dropped += 1

    async def start(self) -> None:
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        await self._flush()
        await self.pool.close()

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush()

    async def _flush(self) -> None:
        await self._flush_queue(self.queue, "events", COLUMNS)
        await self._flush_queue(self.registry_queue, "registry_events", REGISTRY_COLUMNS)

    async def _flush_queue(self, queue: asyncio.Queue, table: str, columns: list[str]) -> None:
        rows = []
        while not queue.empty() and len(rows) < self.batch:
            rows.append(queue.get_nowait())
        if not rows:
            return
        try:
            async with self.pool.acquire() as conn:
                await conn.copy_records_to_table(table, records=rows, columns=columns, schema_name="proxy")
        except Exception:
            log.exception("flush to %s failed, %d events lost", table, len(rows))
