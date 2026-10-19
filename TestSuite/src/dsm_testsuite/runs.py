"""In-memory registry and event broker for active runs; finished runs live only in the DB."""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from secrets import choice
from string import ascii_letters, digits
from threading import Lock

import httpx

from .db import Engine, insert_run, update_run, update_run_peers, save_assertion
from .clients import OrchestratorClient, ProxyClient
from .config import settings
from .executor import execute_scenario
from .scenario import Scenario
from .schemas import Run, RunEvent, RunStatus
from .steps import StepContext

logger = logging.getLogger(__name__)


class ActiveRunExists(Exception):
    pass


class RunManager:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.tasks: set[asyncio.Task] = set()
        self.runs: dict[str, Run] = {}
        self.events: dict[str, list[RunEvent]] = defaultdict(list)
        self.subscribers: dict[str, set[asyncio.Queue[RunEvent]]] = defaultdict(set)
        self._lock = Lock()

    def create(
        self, group_id: int, group_name: str, vm_ip: str, challenge_id: int, scenario: Scenario
    ) -> Run:
        with self._lock:
            if any(
                run.group_id == group_id
                and run.status in {RunStatus.PENDING, RunStatus.RUNNING}
                for run in self.runs.values()
            ):
                raise ActiveRunExists(group_id)
            suffix = "".join(choice(ascii_letters + digits) for _ in range(8))
            run = Run(
                group_id=group_id,
                challenge_id=challenge_id,
                network_id=f"net-{group_name}-{challenge_id}-{suffix}",
            )
            self.runs[run.id] = run
        task = asyncio.create_task(self._execute(run, scenario, vm_ip))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return run

    async def shutdown(self) -> None:
        """Cancel active runs; their executor's `finally` stops the peers they started."""
        for task in list(self.tasks):
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    def publish(self, event: RunEvent) -> None:
        self.events[event.run_id].append(event)
        for queue in self.subscribers[event.run_id]:
            queue.put_nowait(event)

    def subscribe(self, run_id: str) -> asyncio.Queue[RunEvent]:
        queue: asyncio.Queue[RunEvent] = asyncio.Queue()
        for event in self.events[run_id]:
            queue.put_nowait(event)
        self.subscribers[run_id].add(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[RunEvent]) -> None:
        subscribers = self.subscribers.get(run_id)
        if subscribers is not None:
            subscribers.discard(queue)

    async def _persist(self, fn, *args) -> None:
        if self.engine is None:
            return
        try:
            await asyncio.to_thread(fn, self.engine, *args)
        except Exception:
            logger.exception("Could not persist run data")

    def _set_status(self, run: Run, status: RunStatus) -> None:
        run.status = status
        if status in {RunStatus.PASSED, RunStatus.FAILED, RunStatus.ERROR}:
            run.finished_at = datetime.now(timezone.utc)

    async def _execute(self, run: Run, scenario: Scenario, vm_ip: str) -> None:
        await self._persist(insert_run, run)
        self._set_status(run, RunStatus.RUNNING)
        await self._persist(update_run, run)
        self.publish(RunEvent(run_id=run.id, type="status", data={"status": run.status}))

        persisted_peers: list[str] = []

        async def report(index: int, step: dict, passed: bool, message: str | None) -> None:
            peers = sorted(ctx.started_peers)
            if peers != persisted_peers:
                persisted_peers[:] = peers
                await self._persist(update_run_peers, run.id, peers)
            if step["kind"] == "assert":
                await self._persist(
                    save_assertion, run.id, index, step["name"], step["params"], passed, message
                )
            self.publish(
                RunEvent(
                    run_id=run.id,
                    type="step",
                    data={
                        "index": index,
                        **step,
                        "status": "passed" if passed else "failed",
                        "message": message,
                    },
                )
            )

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as http:
                ctx = StepContext(
                    network_id=run.network_id,
                    orchestrator=OrchestratorClient(vm_ip, run.network_id, http),
                    proxy=ProxyClient(settings.proxy_admin_url, run.network_id, http),
                )
                status = await execute_scenario(scenario, ctx, report)
        except Exception:
            logger.exception("Run %s crashed", run.id)
            status = RunStatus.ERROR
        self._set_status(run, status)
        await self._persist(update_run, run)
        self.publish(RunEvent(run_id=run.id, type="status", data={"status": run.status}))
        self._forget(run.id)

    def _forget(self, run_id: str) -> None:
        """Drop a finished run from memory; the DB is the source of truth from here on."""
        self.runs.pop(run_id, None)
        self.events.pop(run_id, None)
        self.subscribers.pop(run_id, None)
