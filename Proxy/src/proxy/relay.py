"""Message relay: request/response over one TCP connection per request."""
import asyncio
import logging
import time

from dsm_protocol import MAX_LINE_BYTES, Message, MessageCode, ProtocolError

from .recorder import Recorder
from .registry import Registry

log = logging.getLogger("relay")

PEER_TIMEOUT = 10.0


class Stats:
    def __init__(self) -> None:
        self.started = time.time()
        self.relayed = 0
        self.failed = 0
        self.invalid = 0


async def apply_conditions(msg: Message) -> float:
    """Hook for network conditions (delay, drop, reorder, partition). Returns the applied delay in ms."""
    return 0.0


def _record(recorder: Recorder, msg: Message, size: int, status: str, delay_ms=None, **extra) -> None:
    content = None if msg.code == MessageCode.PUT_IMAGE else msg.content  # strip image payloads
    recorder.record(network_id=msg.sender.network_id, src_peer=msg.sender.peer_id,
                    dst_peer=msg.receiver.peer_id, code=msg.code, size=size, status=status,
                    delay_ms=delay_ms, content=content, **extra)


def make_relay_handler(registry: Registry, recorder: Recorder, stats: Stats):
    async def forward(msg: Message, line: bytes) -> bytes | None:
        sender = registry.resolve(msg.sender)
        if sender is None:
            stats.failed += 1
            _record(recorder, msg, len(line), "unknown_sender")
            return None
        
        entry = registry.resolve(msg.receiver)
        if entry is None:
            stats.failed += 1
            _record(recorder, msg, len(line), "unknown_receiver")
            return None
        
        if sender.identity.network_id != entry.identity.network_id:
            stats.failed += 1
            _record(recorder, msg, len(line), "mismatched_identity")
            return None
        
        delay_ms = await apply_conditions(msg)
        if delay_ms:
            await asyncio.sleep(delay_ms / 1000)
        try:
            peer_reader, peer_writer = await asyncio.wait_for(
                asyncio.open_connection(entry.host, entry.port, limit=MAX_LINE_BYTES), PEER_TIMEOUT)
        except (OSError, asyncio.TimeoutError):
            stats.failed += 1
            _record(recorder, msg, len(line), "unreachable", delay_ms)
            return None
        try:
            peer_writer.write(line)
            await peer_writer.drain()
            response = await asyncio.wait_for(peer_reader.readline(), PEER_TIMEOUT)
        except (OSError, asyncio.TimeoutError, ValueError, asyncio.LimitOverrunError):
            response = b""
        finally:
            peer_writer.close()
        if not response.endswith(b"\n"):
            stats.failed += 1
            _record(recorder, msg, len(line), "no_response", delay_ms)
            return None
        stats.relayed += 1
        _record(recorder, msg, len(line), "forwarded", delay_ms)
        try:
            reply = Message.from_line(response)
        except ProtocolError:
            return response
        _record(recorder, reply, len(response), "forwarded")
        return response

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            line = await reader.readline()
            if not line:
                return
            try:
                msg = Message.from_line(line)
            except ProtocolError:
                stats.invalid += 1
                recorder.record(network_id="?", size=len(line), status="invalid")
                return
            response = await forward(msg, line)
            if response is not None:
                writer.write(response)
                await writer.drain()
        except (ConnectionError, asyncio.LimitOverrunError, ValueError):
            pass
        except Exception:
            log.exception("relay failed")
        finally:
            writer.close()
    return handle
