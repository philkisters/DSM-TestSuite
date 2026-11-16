import asyncio
from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest

from dsm_protocol import MessageCode

from dsm_testsuite.clients import OrchestratorClient, ProxyClient
from dsm_testsuite.model import ChordModel
from dsm_testsuite.steps.assertions import _check_images
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
