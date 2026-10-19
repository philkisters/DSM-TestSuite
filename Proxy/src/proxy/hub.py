import asyncio
from collections import defaultdict


class Hub:
    """Fan-out of recorded events to live subscribers, per network id."""

    def __init__(self, max_queue: int = 1000) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._max_queue = max_queue

    def subscribe(self, network_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(self._max_queue)
        self._subs[network_id].add(queue)
        return queue

    def unsubscribe(self, network_id: str, queue: asyncio.Queue) -> None:
        self._subs[network_id].discard(queue)
        if not self._subs[network_id]:
            del self._subs[network_id]

    def publish(self, network_id: str, event: dict) -> None:
        for queue in self._subs.get(network_id, ()):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow subscriber: drop rather than block forwarding
