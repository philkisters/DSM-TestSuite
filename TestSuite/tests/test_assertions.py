import asyncio
from types import SimpleNamespace
from unittest.mock import call, create_autospec

import pytest

from dsm_protocol import MessageCode

from dsm_testsuite.clients import OrchestratorClient, ProxyClient
from dsm_testsuite.model import ChordModel
from dsm_testsuite.steps.assertions import ValidNetwork, _check_images
from dsm_testsuite.steps.base import AssertionFailed, StepContext


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ([], ["image-1"]),
        (["image-1"], ["image-1", "image-2"]),
        (["image-1", "image-2"], ["image-1"]),
    ],
)
def test_image_distribution_requires_exact_membership(expected, actual):
    proxy = create_autospec(ProxyClient, instance=True)
    proxy.send_list_images_message.return_value = SimpleNamespace(
        code=MessageCode.LIST_IMAGE_RESPONSE,
        content={"images": actual},
    )
    ctx = StepContext(
        "network",
        create_autospec(OrchestratorClient, instance=True),
        proxy,
        model=ChordModel(),
    )

    with pytest.raises(AssertionFailed, match="image list.*wrong"):
        asyncio.run(_check_images(ctx, "peer", expected))


def test_image_distribution_does_not_depend_on_list_order():
    proxy = create_autospec(ProxyClient, instance=True)
    proxy.send_list_images_message.return_value = SimpleNamespace(
        code=MessageCode.LIST_IMAGE_RESPONSE,
        content={"images": ["image-2", "image-1"]},
    )
    ctx = StepContext(
        "network",
        create_autospec(OrchestratorClient, instance=True),
        proxy,
        model=ChordModel(),
    )

    asyncio.run(_check_images(ctx, "peer", ["image-1", "image-2"]))


def test_valid_network_requests_image_lists_from_every_peer():
    proxy = create_autospec(ProxyClient, instance=True)
    model = ChordModel()
    model.join("peer-a")
    model.join("peer-b")

    async def get_neighbors(peer):
        return SimpleNamespace(
            code=MessageCode.GET_NEIGHBORS_RESPONSE,
            content={
                "successor": {"peer_id": model.successor(peer)},
                "predecessor": {"peer_id": model.predecessor(peer)},
            },
        )

    proxy.send_get_neighborsmessage.side_effect = get_neighbors
    proxy.send_list_images_message.return_value = SimpleNamespace(
        code=MessageCode.LIST_IMAGE_RESPONSE,
        content={"images": []},
    )
    ctx = StepContext(
        "network",
        create_autospec(OrchestratorClient, instance=True),
        proxy,
        check_images=True,
        model=model,
    )

    asyncio.run(ValidNetwork(timeout=0).execute(ctx))

    proxy.send_list_images_message.assert_has_awaits([call(peer) for peer in model.names()])
    assert proxy.send_list_images_message.await_count == len(model.names())


def test_valid_network_requests_images_even_when_neighbors_are_wrong():
    proxy = create_autospec(ProxyClient, instance=True)
    model = ChordModel()
    model.join("peer")
    proxy.send_get_neighborsmessage.return_value = SimpleNamespace(
        code=MessageCode.GET_NEIGHBORS_RESPONSE,
        content={
            "successor": {"peer_id": "wrong-peer"},
            "predecessor": {"peer_id": "wrong-peer"},
        },
    )
    proxy.send_list_images_message.return_value = SimpleNamespace(
        code=MessageCode.LIST_IMAGE_RESPONSE,
        content={"images": []},
    )
    ctx = StepContext(
        "network",
        create_autospec(OrchestratorClient, instance=True),
        proxy,
        check_images=True,
        model=model,
    )

    with pytest.raises(AssertionFailed, match="network is not valid"):
        asyncio.run(ValidNetwork(timeout=0).execute(ctx))

    proxy.send_list_images_message.assert_awaited_once_with("peer")
