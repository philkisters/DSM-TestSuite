import asyncio
from unittest.mock import create_autospec

import pytest

from dsm_testsuite.clients import OrchestratorClient, ProxyClient
from dsm_testsuite.steps.actions import DestroyNetwork, StopPeer
from dsm_testsuite.steps.base import StepContext


@pytest.mark.parametrize("destroy", [False, True])
def test_killing_peer_removes_its_images(destroy):
    orchestrator = create_autospec(OrchestratorClient, instance=True)
    ctx = StepContext("network", orchestrator, create_autospec(ProxyClient, instance=True))
    ctx.started_peers.add("a")
    ctx.model.join("a")
    ctx.model.store_image("image")

    action = DestroyNetwork() if destroy else StopPeer(peer_name="a")
    asyncio.run(action.execute(ctx))

    orchestrator.kill.assert_awaited_once_with("a")
    assert not ctx.started_peers
    ctx.model.join("a")
    assert ctx.model.images("a") == []
