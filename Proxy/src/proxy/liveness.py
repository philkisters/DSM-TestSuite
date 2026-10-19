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
        msg = await asyncio.wait_for(reader.readline(), timeout)
        log.log(logging.INFO, "received message %s from %s/%s at %s:%d", msg.decode().strip(), entry.identity.network_id, entry.identity.peer_id, entry.host, entry.port)
        msg = Message.from_line(msg)
        if (msg.code == Message.GET_NEIGHBORS_RESPONSE):
            entry.successor = Identity.from_json(msg.data.successor) if hasattr(msg.data, "successor") else None
            entry.predecessor = Identity.from_json(msg.data.predecessor) if hasattr(msg.data, "predecessor") else None
            _publish(hub, recorder, "peer_updated", entry.identity, entry.host, entry.port, peer_data={"successor": entry.successor, "predecessor": entry.predecessor})
        return msg.endswith(b"\n")
    except (OSError, asyncio.TimeoutError, ValueError):
        return False
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


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
            await asyncio.gather(*(_check(registry, hub, recorder, e, retries, timeout) for e in entries))
