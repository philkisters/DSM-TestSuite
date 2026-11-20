import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from dsm_protocol import (
    Message,
    MessageCode,
    OrchestratorProtocolVersion,
    PeerProtocolVersion,
)
from dsm_testsuite.clients import ClientError, OrchestratorClient, ProxyClient
from dsm_testsuite.scenario import Scenario


@pytest.mark.parametrize(
    "version",
    [
        PeerProtocolVersion.V1,
        PeerProtocolVersion.V2,
        PeerProtocolVersion.V3,
        PeerProtocolVersion.V4,
    ],
)
def test_peer_versions_use_the_same_wire_format(version):
    requests = []
    expected = {
        "sender": {"network_id": "network", "peer_id": "TestSuite"},
        "receiver": {"network_id": "network", "peer_id": "peer"},
        "code": MessageCode.GET_NEIGHBORS_REQUEST,
        "content": {},
    }

    def handle(request):
        requests.append(json.loads(request.content))
        response = dict(expected)
        response["code"] = MessageCode.GET_NEIGHBORS_RESPONSE
        return httpx.Response(200, json=response)

    async def send():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            client = ProxyClient("http://proxy", "network", http, version)
            return await client.send_get_neighborsmessage("peer")

    response = asyncio.run(send())
    payload = requests[0]
    assert payload.pop("protocol_version") == version.value
    assert payload == expected
    assert response.code == MessageCode.GET_NEIGHBORS_RESPONSE


def test_messages_require_the_stable_snake_case_format():
    document = {
        "sender": {"networkId": "network", "peerId": "sender"},
        "receiver": {"networkId": "network", "peerId": "receiver"},
        "message-code": MessageCode.GET_NEIGHBORS_RESPONSE,
        "content": {},
    }

    with pytest.raises(ValueError):
        Message.from_json(document, PeerProtocolVersion.V2)


@pytest.mark.parametrize(
    ("version", "replication"),
    [
        (PeerProtocolVersion.V3, None),
        (PeerProtocolVersion.V4, -1),
    ],
)
def test_put_image_content_matches_selected_peer_version(
    monkeypatch, version, replication
):
    requests = []
    monkeypatch.setattr(
        "dsm_testsuite.clients._load_image_as_base64", lambda _image: "encoded"
    )

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "sender": requests[0]["receiver"],
                "receiver": requests[0]["sender"],
                "code": MessageCode.ACK,
                "content": {},
            },
        )

    async def send():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            client = ProxyClient("http://proxy", "network", http, version)
            return await client.put_images("peer", ["image-0.png"])

    asyncio.run(send())
    content = requests[0]["content"]
    assert content["image_id"] == "image-0.png"
    assert content.get("replication") == replication


def test_orchestrator_v2_start_includes_replication_factor():
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(201, json={})

    async def start():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            client = OrchestratorClient(
                "127.0.0.1",
                "network",
                http,
                OrchestratorProtocolVersion.V2,
                3,
            )
            await client.start("peer")

    asyncio.run(start())
    assert requests == [
        {"network_id": "network", "peer_id": "peer", "replications": 3}
    ]


def test_orchestrator_v1_start_does_not_include_replication():
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(201, json={})

    async def start():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            await OrchestratorClient("127.0.0.1", "network", http).start("peer")

    asyncio.run(start())
    assert requests == [{"network_id": "network", "peer_id": "peer"}]


@pytest.mark.parametrize(
    "scenario",
    [
        {
            "protocols": {"peer": "v4", "orchestrator": "v1"},
            "replication-factor": 2,
        },
        {"protocols": {"peer": "v4", "orchestrator": "v2"}},
        {
            "protocols": {"peer": "v3", "orchestrator": "v1"},
            "replication-factor": 2,
        },
    ],
)
def test_scenario_rejects_invalid_protocol_combinations(scenario):
    with pytest.raises(ValidationError):
        Scenario(name="invalid", steps=[], **scenario)


def test_orchestrator_v2_allows_legacy_start_without_replication():
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(201, json={})

    async def start():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            client = OrchestratorClient(
                "127.0.0.1",
                "network",
                http,
                OrchestratorProtocolVersion.V2,
            )
            await client.start("peer")

    asyncio.run(start())
    assert requests == [{"network_id": "network", "peer_id": "peer"}]


def test_peer_v1_rejects_messages_it_does_not_define(monkeypatch):
    monkeypatch.setattr(
        "dsm_testsuite.clients._load_image_as_base64", lambda _image: "encoded"
    )

    async def send():
        async with httpx.AsyncClient() as http:
            client = ProxyClient(
                "http://proxy", "network", http, PeerProtocolVersion.V1
            )
            await client.send_put_image_message("peer", "image-0.png")

    with pytest.raises(ClientError, match="not available"):
        asyncio.run(send())


def test_peer_versions_define_incremental_message_capabilities():
    assert PeerProtocolVersion.V1.supports(MessageCode.GET_NEIGHBORS_REQUEST)
    assert not PeerProtocolVersion.V1.supports(MessageCode.GET_FINGERS_REQUEST)
    assert PeerProtocolVersion.V2.supports(MessageCode.GET_FINGERS_REQUEST)
    assert not PeerProtocolVersion.V2.supports(MessageCode.PUT_IMAGE)
    assert PeerProtocolVersion.V3.supports(MessageCode.PUT_IMAGE)
    assert PeerProtocolVersion.V4.supports(MessageCode.PUT_IMAGE)
