"""Registration endpoint: newline-delimited JSON, one request/response per connection.

Request:  {"action": "register"|"unregister", "networkId": "...", "peerId": "...","port": 1234}
Response: {"status": "ok"} or {"status": "error", "message": "..."}
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from dsm_protocol import Identity, ProtocolError

from .hub import Hub
from .recorder import Recorder
from .registry import Registry

log = logging.getLogger("register")


def _publish(hub: Hub, recorder: Recorder, event: str, identity: Identity, host=None, port=None, peer_data=None, message=None) -> None:
    now = datetime.now(timezone.utc)
    recorder.record_registry(ts=now, network_id=identity.network_id, peer_id=identity.peer_id,
                             event=event, host=host, port=port, peer_data=peer_data, message=message)
    hub.publish(identity.network_id, {
        "type": event, "ts": now.isoformat(),
        "networkId": identity.network_id, "peerId": identity.peer_id, "host": host, "port": port,
        **({"peerData": peer_data} if peer_data else {}),
        **({"message": message} if message else {})})


def _handle_request(registry: Registry, hub: Hub, recorder: Recorder, document, peername) -> dict:
    if not isinstance(document, dict):
        raise ProtocolError("request must be a JSON object")
    identity = Identity.from_json(document)
    action = document.get("action", "register")
    host = peername[0] if peername else None
    if action == "unregister":
        removed = registry.unregister(identity)
        if removed:
            _publish(hub, recorder, "peer_unregistered", identity, message="requested")
        log.info("unregistered %s/%s at %s", identity.network_id, identity.peer_id, host)
        return {"status": "ok", "removed": removed}
    if action != "register":
        raise ProtocolError(f"unknown action {action!r}")
    port = document.get("port")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ProtocolError("'port' must be an integer between 1 and 65535")
    if not isinstance(host, str) or not host:
        raise ProtocolError("'host' is missing")
    is_new = registry.resolve(identity) is None
    registry.register(identity, host, port)
    _publish(hub, recorder, "peer_registered" if is_new else "peer_updated", identity, host, port)
    log.info("registered %s/%s at %s:%d", identity.network_id, identity.peer_id, host, port)
    return {"status": "ok"}


def make_register_handler(registry: Registry, hub: Hub, recorder: Recorder):
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            line = await reader.readline()
            if not line:
                return
            try:
                response = _handle_request(registry, hub, recorder, json.loads(line), writer.get_extra_info("peername"))
            except (ValueError, ProtocolError) as exc:
                response = {"status": "error", "message": str(exc)}
            writer.write(json.dumps(response, separators=(",", ":")).encode() + b"\n")
            await writer.drain()
        except (ConnectionError, asyncio.LimitOverrunError):
            pass
        finally:
            writer.close()
    return handle
