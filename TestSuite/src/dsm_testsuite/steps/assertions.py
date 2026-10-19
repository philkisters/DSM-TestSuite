"""Assertions: observe the network through the proxy. Raise AssertionFailed if wrong."""
from pydantic import Field

from .base import AssertionFailed, Step, StepContext
from .registry import assertion

from dsm_protocol import Message, MessageCode


class _PeerStep(Step):
    peer_name: str = Field(alias="peer-name")


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
        # Implement the logic to check if the peer has not joined the network        
        try:
            response_message : Message = await ctx.proxy.send_get_neighborsmessage(self.peer_name)
        except Exception as exc:
            raise AssertionFailed(f"failed to send GetNeighborsMessage to {self.peer_name!r}: {exc!r}") from exc

        if response_message.code != MessageCode.ERROR :
            raise AssertionFailed(f"peer needs to return an ErrorMessage when it has not in a P2P network")

@assertion("neighbors")
class Neighbors(_PeerStep):
    predecessor: str
    successor: str
    
    async def execute(self, ctx: StepContext) -> None:
        # Implement the logic to check if the peer has not joined the network        
        try:
            response_message : Message = await ctx.proxy.send_get_neighborsmessage(self.peer_name)
        except Exception as exc:
            raise AssertionFailed(f"failed to send GetNeighborsMessage to {self.peer_name!r}: {exc!r}") from exc

        if response_message.code == MessageCode.ERROR:
            raise AssertionFailed(f"Peer returned an ErrorMessage when should be part of the network ${response_message.content.message}")
        
        if response_message.code != MessageCode.GET_NEIGHBORS_RESPONSE:
            raise AssertionFailed(f"The peer should return a GET_NEIGHBORS_RESPONSE message. Received a message with the code '${response_message.code}' instead.")
        
        if (response_message.content.successor == None or response_message.content.predecessor == None):
            raise AssertionFailed(f"The response for GET_NEIGHBORS message should contain a 'predecessor' and 'successor' field.")
        
        if (response_message.content.successor.name != self.successor or response_message.content.predecessor.name != self.predecessor):
            raise AssertionFailed(f"The response returned unexpected neighbors: successor ${response_message.content.successor.name} (should be ${self.successor}); predecessor ${response_message.content.predecessor.name} (should be ${self.predecessor}).") 

