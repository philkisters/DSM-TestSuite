"""Actions: do something to the network. Raise StepError if that is impossible."""
import asyncio

from pydantic import Field

from .base import Step, StepContext
from .registry import action


class _PeerStep(Step):
    peer_name: str = Field(alias="peer-name")


@action("start-peer")
class StartPeer(_PeerStep):
    async def execute(self, ctx: StepContext) -> None:
        await ctx.orchestrator.start(self.peer_name)
        ctx.started_peers.add(self.peer_name)


@action("join-peer")
class JoinPeer(_PeerStep):
    bootstrap_peer_name: str | None = Field(default=None, alias="bootstrap-peer-name")

    async def execute(self, ctx: StepContext) -> None:
        await ctx.orchestrator.join(self.peer_name, self.bootstrap_peer_name)
        ctx.model.join(self.peer_name)


@action("leave-peer")
class LeavePeer(_PeerStep):
    async def execute(self, ctx: StepContext) -> None:
        await ctx.orchestrator.leave(self.peer_name)
        ctx.model.leave(self.peer_name)


@action("stop-peer")
class StopPeer(_PeerStep):
    async def execute(self, ctx: StepContext) -> None:
        await ctx.orchestrator.kill(self.peer_name)
        ctx.started_peers.discard(self.peer_name)
        ctx.model.leave(self.peer_name)


@action("setup-network")
class SetupNetwork(Step):
    """Start and join all peers one after another; each joins via the previous peer."""

    peer_names: list[str] = Field(alias="peer-names", min_length=1)
    timeout: float = Field(default=5, ge=0)

    async def execute(self, ctx: StepContext) -> None:
        bootstrap: str | None = None
        for index, name in enumerate(self.peer_names):
            if index:
                await asyncio.sleep(self.timeout)
            await ctx.orchestrator.start(name)
            ctx.started_peers.add(name)
            await ctx.orchestrator.join(name, bootstrap)
            ctx.model.join(name)
            bootstrap = name


@action("destroy-network")
class DestroyNetwork(Step):
    """Kill every peer started during this run."""

    async def execute(self, ctx: StepContext) -> None:
        for name in sorted(ctx.started_peers):
            await ctx.orchestrator.kill(name)
            ctx.started_peers.discard(name)
            ctx.model.leave(name)


@action("wait")
class Wait(Step):
    duration: float = Field(ge=0)

    async def execute(self, ctx: StepContext) -> None:
        await asyncio.sleep(self.duration)
