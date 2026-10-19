import asyncio
import time
from dataclasses import dataclass, field

from dsm_protocol import Identity, Message, MAX_LINE_BYTES


@dataclass
class PeerEntry:
    identity: Identity
    host: str
    port: int
    registered_at: float = field(default_factory=time.time)
    predecessor: Identity | None = None
    successor: Identity | None = None

    def to_json(self) -> dict:
        return {"networkId": self.identity.network_id, "peerId": self.identity.peer_id,
                "host": self.host, "port": self.port, "registeredAt": self.registered_at,
                "predecessor": self.predecessor.network_id + ":" + self.predecessor.peer_id if self.predecessor else None,
                "successor": self.successor.network_id + ":" + self.successor.peer_id if self.successor else None}


class Registry:
    """Lookup table: logical identity (network id + peer id) -> physical address."""

    def __init__(self) -> None:
        self._peers: dict[Identity, PeerEntry] = {}

    def register(self, identity: Identity, host: str, port: int) -> None:
        self._peers[identity] = PeerEntry(identity, host, port)

    def unregister(self, identity: Identity) -> bool:
        return self._peers.pop(identity, None) is not None

    def resolve(self, identity: Identity) -> PeerEntry | None:
        return self._peers.get(identity)

    def peers(self, network_id: str | None = None) -> list[PeerEntry]:
        return [p for i, p in self._peers.items() if network_id is None or i.network_id == network_id]

    def networks(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for identity in self._peers:
            counts[identity.network_id] = counts.get(identity.network_id, 0) + 1
        return counts
    
    async def send_message(self, message: Message) -> Message:
        target = self.resolve(message.receiver)
        timeout = 2
        if (target is None):
            raise ValueError(f"Target {message.receiver} not found")
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target.host, target.port, limit=MAX_LINE_BYTES), timeout)
            writer.write(message.to_line())
            await writer.drain()
            msg = await asyncio.wait_for(reader.readline(), timeout)
            msg = Message.from_line(msg)
            return msg
        except (OSError, asyncio.TimeoutError, ValueError):
            raise ValueError(f"Failed to send message to {message.receiver}")
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
