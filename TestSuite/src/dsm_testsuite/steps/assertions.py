"""Assertions: observe the network through the proxy. Raise AssertionFailed if wrong."""
import asyncio
import time
from typing import Awaitable, Callable

from pydantic import Field

from .base import AssertionFailed, Step, StepContext
from .registry import assertion

from dsm_protocol import Message, MessageCode


DEFAULT_POLL_INTERVAL = 1.0


class _PeerStep(Step):
    peer_name: str = Field(alias="peer-name")
    
class _TimeoutStep(Step):
    """Mixin for assertions that poll until they hold or `timeout` seconds have passed."""

    timeout: float = Field(default=0, ge=0)
    poll_interval: float = Field(default=DEFAULT_POLL_INTERVAL, gt=0, alias="poll-interval")

    async def retry(self, check: Callable[[], Awaitable[None]]) -> None:
        await _retry(self.timeout, self.poll_interval, check)

async def _registered(ctx: StepContext) -> set[str]:
    return {p["peerId"] for p in await ctx.proxy.peers()}


@assertion("peer-registered")
class PeerRegistered(_PeerStep):
    async def execute(self, ctx: StepContext) -> None:
        peers = await _registered(ctx)
        if self.peer_name not in peers:
            raise AssertionFailed(
                f"peer {self.peer_name!r} is not registered at the proxy (registered: {sorted(peers)})"
            )
            
@assertion("peers-registered")
class PeersRegistered(Step):
    number: int

    async def execute(self, ctx: StepContext) -> None:
        peers = await _registered(ctx)
        if len(peers) != self.number:
            raise AssertionFailed(
                f"expected {self.number} peers registered at the proxy, but found {len(peers)}"
            )

@assertion("peer-not-registered")
class PeerNotRegistered(_PeerStep):
    async def execute(self, ctx: StepContext) -> None:
        if self.peer_name in await _registered(ctx):
            raise AssertionFailed(f"peer {self.peer_name!r} is still registered at the proxy")

@assertion("not-joined")
class NotJoined(_PeerStep):    
    async def execute(self, ctx: StepContext) -> None:
        # Implement the logic to check if the peer has not joined a p2p network        
        try:
            response_message : Message = await ctx.proxy.send_get_neighborsmessage(self.peer_name)
        except Exception as exc:
            raise AssertionFailed(f"failed to send GetNeighborsMessage to {self.peer_name!r}: {exc!r}") from exc

        if response_message.code != MessageCode.ERROR :
            raise AssertionFailed(f"peer needs to return an ErrorMessage when it has not in a P2P network")

@assertion("joined")
class Joined(_PeerStep):
    async def execute(self, ctx: StepContext) -> None:
        # Implement the logic to check if the peer is part of a p2p network
        try:
            response_message : Message = await ctx.proxy.send_get_neighborsmessage(self.peer_name)
        except Exception as exc:
            raise AssertionFailed(f"failed to send GetNeighborsMessage to {self.peer_name!r}: {exc!r}") from exc

        if response_message.code != MessageCode.GET_NEIGHBORS_RESPONSE :
            raise AssertionFailed(f"peer needs to return a GET_NEIGHBORS_RESPONSE message when it has joined the network")


async def _retry(timeout: float, interval: float, check: Callable[[], Awaitable[None]]) -> None:
    """Run `check` every `interval` seconds until it passes or `timeout` seconds have passed (then re-raise the last failure)."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            await check()
            return
        except AssertionFailed:
            if time.monotonic() >= deadline:
                raise
        await asyncio.sleep(interval)

def _error_text(message: Message) -> str:
    return str(message.content.get("message", ""))


async def _check_neighbors(ctx: StepContext, peer: str, successor: str, predecessor: str) -> None:
    try:
        response: Message = await ctx.proxy.send_get_neighborsmessage(peer)
    except Exception as exc:
        raise AssertionFailed(f"failed to send GetNeighborsMessage to {peer!r}: {exc!r}") from exc

    if response.code == MessageCode.ERROR:
        raise AssertionFailed(f"{peer!r} returned an ErrorMessage but should be part of the network: {_error_text(response)}")
    if response.code != MessageCode.GET_NEIGHBORS_RESPONSE:
        raise AssertionFailed(f"{peer!r} should return a GET_NEIGHBORS_RESPONSE, got code '{response.code}'")
    content = response.content
    if "successor" not in content or "predecessor" not in content:
        raise AssertionFailed("The GET_NEIGHBORS_RESPONSE content must contain 'predecessor' and 'successor'")
    if content["successor"] is None or content["predecessor"] is None:
        raise AssertionFailed("The 'predecessor' and 'successor' must never be None")

    got_succ, got_pred = content["successor"]["peer_id"], content["predecessor"]["peer_id"]
    if got_succ != successor or got_pred != predecessor:
        raise AssertionFailed(
            f"unexpected neighbors for {peer!r}: successor {got_succ!r} (should be {successor!r}); "
            f"predecessor {got_pred!r} (should be {predecessor!r})"
        )

async def _count_messages(ctx: StepContext, from_peer: str, to_peer: str, code: MessageCode | None) -> int:
    try:
        return len(await ctx.proxy.messages(src_peer=from_peer, dst_peer=to_peer, code=code))
    except Exception as exc:
        raise AssertionFailed(f"failed to query messages at the proxy: {exc!r}") from exc


def _describe_message(from_peer: str, to_peer: str, code: MessageCode | None) -> str:
    kind = f"a {code.name} message" if code is not None else "a message"
    return f"{kind} from {from_peer!r} to {to_peer!r}"


def _ranges(indices: list[int]) -> str:
    runs: list[str] = []
    start = prev = indices[0]
    for i in indices[1:] + [None]:  # type: ignore[list-item]
        if i is not None and i == prev + 1:
            prev = i
            continue
        runs.append(str(start) if start == prev else f"{start}-{prev}")
        if i is not None:
            start = prev = i
    return ", ".join(runs)


async def _check_fingers(ctx: StepContext, peer: str, expected: list[str]) -> None:
    try:
        response: Message = await ctx.proxy.send_get_finger_message(peer)
    except Exception as exc:
        raise AssertionFailed(f"failed to send GetFingersMessage to {peer!r}: {exc!r}") from exc

    if response.code == MessageCode.ERROR:
        raise AssertionFailed(f"{peer!r} returned an ErrorMessage but should be part of the network: {_error_text(response)}")
    if response.code != MessageCode.GET_FINGERS_RESPONSE:
        raise AssertionFailed(f"{peer!r} should return a GET_FINGERS_RESPONSE, got code '{response.code}'")
    if "fingers" not in response.content:
        raise AssertionFailed("The GET_FINGERS_RESPONSE content must contain the 'fingers' key")
    fingers = response.content["fingers"]
    if not isinstance(fingers, list):
        raise AssertionFailed("The 'fingers' key should be a list")
    if len(fingers) != len(expected):
        raise AssertionFailed(f"The 'fingers' key should contain {len(expected)} entries, got {len(fingers)}")
    if any(not isinstance(f, dict) or "peer_id" not in f for f in fingers):
        raise AssertionFailed("Each finger entry should contain a 'peer_id' key")

    actual = [f["peer_id"] for f in fingers]
    bad = [i for i, (e, a) in enumerate(zip(expected, actual)) if e != a]
    if bad:
        first = bad[0]
        raise AssertionFailed(
            f"finger table of {peer!r} is wrong at {len(bad)} of {len(expected)} entries "
            f"(indices {_ranges(bad)}); e.g. finger {first} should be {expected[first]!r}, got {actual[first]!r}"
        )


def _model_peer(ctx: StepContext, peer: str) -> None:
    if peer not in ctx.model:
        raise AssertionFailed(
            f"{peer!r} is not part of the expected network (expected: {ctx.model.names()}); "
            "provide explicit values or fix the scenario"
        )


@assertion("neighbors")
class Neighbors(_PeerStep, _TimeoutStep):
    # Default to the neighbors expected from the simulated network.
    predecessor: str | None = None
    successor: str | None = None

    async def execute(self, ctx: StepContext) -> None:
        async def check() -> None:
            if self.successor is None or self.predecessor is None:
                _model_peer(ctx, self.peer_name)
            successor = self.successor or ctx.model.successor(self.peer_name)
            predecessor = self.predecessor or ctx.model.predecessor(self.peer_name)
            await _check_neighbors(ctx, self.peer_name, successor, predecessor)

        await self.retry(check)


@assertion("finger-table")
class FingerTable(_PeerStep, _TimeoutStep):

    async def execute(self, ctx: StepContext) -> None:
        async def check() -> None:
            _model_peer(ctx, self.peer_name)
            await _check_fingers(ctx, self.peer_name, ctx.model.fingers(self.peer_name))

        await self.retry(check)


@assertion("valid-network")
class ValidNetwork(_TimeoutStep):
    """Every peer of the simulated network reports the neighbors and fingers the model expects."""

    timeout: float = Field(default=30, ge=0)

    async def execute(self, ctx: StepContext) -> None:
        async def check() -> None:
            errors: list[str] = []
            for peer in ctx.model.names():
                try:
                    await _check_neighbors(ctx, peer, ctx.model.successor(peer), ctx.model.predecessor(peer))
                    if (ctx.check_fingers):
                        await _check_fingers(ctx, peer, ctx.model.fingers(peer))
                except AssertionFailed as exc:
                    errors.append(str(exc))
            if errors:
                raise AssertionFailed(f"network is not valid ({len(errors)} peer(s) wrong): " + " | ".join(errors))

        await self.retry(check)


class _MessageStep(Step):
    from_peer: str = Field(alias="from")
    to_peer: str = Field(alias="to")
    code: MessageCode | None = None


@assertion("message-sent")
class MessageSent(_MessageStep, _TimeoutStep):
    """The proxy forwarded at least one matching message in this network."""

    async def execute(self, ctx: StepContext) -> None:
        async def check() -> None:
            if await _count_messages(ctx, self.from_peer, self.to_peer, self.code) == 0:
                raise AssertionFailed(f"no {_describe_message(self.from_peer, self.to_peer, self.code)} was sent")

        await self.retry(check)


@assertion("message-not-sent")
class MessageNotSent(_MessageStep):
    """The proxy forwarded no matching message in this network."""

    async def execute(self, ctx: StepContext) -> None:
        count = await _count_messages(ctx, self.from_peer, self.to_peer, self.code)
        if count:
            raise AssertionFailed(f"{_describe_message(self.from_peer, self.to_peer, self.code)} was sent {count} time(s)")
