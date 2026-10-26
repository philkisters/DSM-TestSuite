"""Periodic liveness check: GET_NEIGHBORS_REQUEST to every registered peer, drop the unresponsive ones."""
import asyncio
import logging
import os

from dsm_protocol import MAX_LINE_BYTES, Identity, Message, MessageCode

from .hub import Hub
from .recorder import Recorder
from .register import _publish
from .registry import PeerEntry, Registry

log = logging.getLogger("liveness")

PROXY_PEER_ID = "proxy"


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


async def _ping(entry: PeerEntry, timeout: float, hub: Hub, recorder: Recorder) -> bool:
    msg = Message(sender=Identity(entry.identity.network_id, PROXY_PEER_ID),
                  receiver=entry.identity, code=MessageCode.GET_NEIGHBORS_REQUEST)
    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(entry.host, entry.port, limit=MAX_LINE_BYTES), timeout)
        writer.write(msg.to_line())
        await writer.drain()
        line = await asyncio.wait_for(reader.readline(), timeout)
        if not line.endswith(b"\n"):
            return False
        reply = Message.from_line(line)
        if reply.code == MessageCode.GET_NEIGHBORS_RESPONSE:
            succ = reply.content.get("successor") or None
            pred = reply.content.get("predecessor") or None
            entry.successor = Identity.from_json(succ) if succ else None
            entry.predecessor = Identity.from_json(pred) if pred else None
            _publish(hub, recorder, "peer_updated", entry.identity, entry.host, entry.port,
                     peer_data={"successor": succ, "predecessor": pred})
        return True
    except (OSError, asyncio.TimeoutError, ValueError):
        return False
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass


async def _check(registry: Registry, hub: Hub, recorder: Recorder, entry: PeerEntry, retries: int, timeout: float) -> None:
    for _ in range(retries + 1):
        if await _ping(entry, timeout, hub, recorder):
            return
    # Only drop if the peer wasn't re-registered (possibly elsewhere) in the meantime.
    if registry.resolve(entry.identity) is entry and registry.unregister(entry.identity):
        ident = entry.identity
        log.warning("unregister %s/%s at %s:%d: unreachable", ident.network_id, ident.peer_id,
                    entry.host, entry.port)
        _publish(hub, recorder, "peer_unregistered", ident, entry.host, entry.port, peer_data=None, message="unreachable")


async def liveness_loop(registry: Registry, hub: Hub, recorder: Recorder) -> None:
    interval = _env_float("LIVENESS_INTERVAL", 5.0)
    timeout = _env_float("LIVENESS_TIMEOUT", 2.0)
    retries = int(os.getenv("LIVENESS_RETRIES", "2"))
    while True:
        await asyncio.sleep(interval)
        entries = registry.peers()
        log.info("starting to check liveness for %d peers", len(entries))

        if entries:
            results = await asyncio.gather(
                *(_check(registry, hub, recorder, e, retries, timeout) for e in entries),
                return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    log.error("liveness check failed", exc_info=r)
