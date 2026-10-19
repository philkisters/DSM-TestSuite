"""Periodically probes every group's Orchestrator /health endpoint."""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

import httpx
from sqlalchemy.engine import Engine
from dsm_db import GroupHealth as GroupHealthRow

from .clients import OrchestratorClient
from .db import list_groups, save_group_health
from .schemas import GroupHealthEvent

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 5.0
PROBE_TIMEOUT = 3.0
RETRIES = 3
SUBSCRIBER_QUEUE_SIZE = 100


class HealthState(str, Enum):
    ONLINE = "ONLINE"
    NOT_RESPONDING = "NOT_RESPONDING"
    OFFLINE = "OFFLINE"


@dataclass
class GroupHealth:
    group_id: int
    name: str
    vm_ip: str | None
    state: HealthState = HealthState.OFFLINE
    failures: int = 0


class HealthService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._health: dict[int, GroupHealth] = {}
        self._task: asyncio.Task | None = None
        self._http: httpx.AsyncClient | None = None
        self._published: dict[int, GroupHealthEvent] = {}
        self._subscribers: set[asyncio.Queue[GroupHealthEvent]] = set()

    def subscribe(self) -> asyncio.Queue[GroupHealthEvent]:
        """Queue pre-filled with the last known state of every group, then state changes."""
        queue: asyncio.Queue[GroupHealthEvent] = asyncio.Queue(SUBSCRIBER_QUEUE_SIZE)
        for event in self._published.values():
            queue.put_nowait(event)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[GroupHealthEvent]) -> None:
        self._subscribers.discard(queue)

    def _publish(self, event: GroupHealthEvent) -> None:
        self._published[event.group_id] = event
        for queue in self._subscribers:
            if queue.full():
                queue.get_nowait()  # a slow client loses its oldest event, never blocks the service
            queue.put_nowait(event)

    async def start(self) -> None:
        self._http = httpx.AsyncClient(timeout=PROBE_TIMEOUT)
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        if self._http:
            await self._http.aclose()

    async def _run(self) -> None:
        while True:
            started = asyncio.get_running_loop().time()
            try:
                await self._check_all()
            except Exception:
                logger.exception("Health check cycle failed")
            elapsed = asyncio.get_running_loop().time() - started
            await asyncio.sleep(max(0.0, CHECK_INTERVAL - elapsed))

    async def _check_all(self) -> None:
        groups = await asyncio.to_thread(list_groups, self.engine)
        current = {g.id for g in groups}
        for gid in set(self._health) - current:
            del self._health[gid]
            self._published.pop(gid, None)
        entries = []
        for g in groups:
            entry = self._health.setdefault(g.id, GroupHealth(g.id, g.name, g.vm_ip))
            entry.name, entry.vm_ip = g.name, g.vm_ip
            entries.append(entry)
        # All probes run concurrently; each is bounded by PROBE_TIMEOUT.
        await asyncio.gather(*(self._check_one(e) for e in entries))
        for e in entries:
            previous = self._published.get(e.group_id)
            if previous is None or previous.state != e.state.value:
                self._publish(GroupHealthEvent(group_id=e.group_id, state=e.state.value, failures=e.failures))
        rows = [GroupHealthRow(group_id=e.group_id, state=e.state.value, failures=e.failures) for e in entries]
        await asyncio.to_thread(save_group_health, self.engine, rows)

    async def _check_one(self, entry: GroupHealth) -> None:
        ok = False
        if entry.vm_ip:
            try:
                await OrchestratorClient(entry.vm_ip, "", self._http).health()
                ok = True
            except Exception:
                ok = False
        if ok:
            entry.failures = 0
            entry.state = HealthState.ONLINE
            return
        entry.failures += 1
        # First miss -> NOT_RESPONDING, then RETRIES more misses before OFFLINE.
        entry.state = (
            HealthState.NOT_RESPONDING if entry.failures <= RETRIES else HealthState.OFFLINE
        )
