"""Wire format of the P2P protocol (newline-delimited JSON, see protocol.md)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

MAX_LINE_BYTES = 16 * 1024 * 1024


class MessageCode(IntEnum):
    ERROR = -1
    ACK = 0
    JOIN = 1
    LEAVE = 2
    GET_NEIGHBORS_REQUEST = 3
    GET_NEIGHBORS_RESPONSE = 4
    GET_FINGERS_REQUEST = 5
    GET_FINGERS_RESPONSE = 6
    PUT_IMAGE = 7
    LIST_IMAGE_REQUEST = 8
    LIST_IMAGE_RESPONSE = 9
    REQUEST_IMAGE = 10


class ProtocolError(ValueError):
    """Raised when received data is not a valid protocol message."""


def hash_id(identifier: str) -> int:
    """SHA-256 over the UTF-8 bytes, read as an unsigned big-endian integer."""
    return int.from_bytes(hashlib.sha256(identifier.encode("utf-8")).digest(), "big")


@dataclass(frozen=True)
class Identity:
    network_id: str
    peer_id: str

    @property
    def ring_key(self) -> tuple[int, str]:
        # The raw ID breaks ties between equal hashes.
        return (hash_id(self.peer_id), self.peer_id)

    def to_json(self) -> dict[str, str]:
        return {"network_id": self.network_id, "peer_id": self.peer_id}

    @classmethod
    def from_json(cls, data: Any) -> Identity:
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("network_id"), str)
            or not isinstance(data.get("peer_id"), str)
            or not data["peer_id"]
        ):
            raise ProtocolError(f"Invalid peer identity: {data!r}")
        return cls(network_id=data["network_id"], peer_id=data["peer_id"])


@dataclass(frozen=True)
class Message:
    sender: Identity
    receiver: Identity
    code: int
    content: dict[str, Any] = field(default_factory=dict)

    def to_line(self) -> bytes:
        return json.dumps(self.to_json(), separators=(",", ":")).encode("utf-8") + b"\n"

    def to_json(self) -> dict[str, Any]:
        return {
            "sender": self.sender.to_json(),
            "receiver": self.receiver.to_json(),
            "code": int(self.code),
            "content": self.content,
        }

    @classmethod
    def from_json(cls, data: Any) -> Message:
        if not isinstance(data, dict):
            raise ProtocolError(f"Invalid message format: {data!r}")
        sender = Identity.from_json(data.get("sender"))
        receiver = Identity.from_json(data.get("receiver"))
        code = data.get("code")
        content = data.get("content", {})
        if isinstance(code, bool) or not isinstance(code, int):
            raise ProtocolError("'message-code' must be an integer")
        if not isinstance(content, dict):
            raise ProtocolError("'content' must be a JSON object")
        return cls(sender=sender, receiver=receiver, code=code, content=content)
    
    @classmethod
    def from_line(cls, line: bytes) -> Message:
        try:
            document = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ProtocolError(f"Message is not valid JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise ProtocolError("Message must be a JSON object")

        code = document.get("code")
        content = document.get("content", {})
        if isinstance(code, bool) or not isinstance(code, int):
            raise ProtocolError("'code' must be an integer")
        if not isinstance(content, dict):
            raise ProtocolError("'content' must be a JSON object")
        return cls(
            sender=Identity.from_json(document.get("sender")),
            receiver=Identity.from_json(document.get("receiver")),
            code=code,
            content=content,
        )
