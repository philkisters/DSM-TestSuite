from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dsm_testsuite.api import networks, orchestrator
from dsm_testsuite.main import app
from dsm_testsuite.schemas import NetworkCreate


def test_network_v1_rejects_replication_factor():
    try:
        NetworkCreate(
            network_id="network",
            orchestrator_version="v1",
            replication_factor=2,
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("orchestrator v1 accepted a replication factor")


def test_store_custom_network(monkeypatch):
    group = SimpleNamespace(id=4)
    network = SimpleNamespace(
        id=1,
        group_id=4,
        network_id="custom",
        orchestrator_version="v2",
        replication_factor=3,
        created_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(networks, "get_engine", lambda _request: "engine")
    monkeypatch.setattr(networks, "list_groups", lambda _engine: [group])
    monkeypatch.setattr(
        networks,
        "create_network",
        lambda engine, group_id, network_id, version, replication: network,
    )

    client = TestClient(app)
    response = client.post(
        "/api/groups/4/networks",
        json={
            "network_id": "custom",
            "orchestrator_version": "v2",
            "replication_factor": 3,
        },
    )

    assert response.status_code == 201
    assert response.json()["replication_factor"] == 3


def test_stored_replication_is_forwarded_for_every_new_peer(monkeypatch):
    requests = []

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, _url, *, json, headers):
            requests.append((json, headers))
            return httpx.Response(201, json=json)

        async def get(self, _url):
            return httpx.Response(200, json={"status": "ok"})

        async def aclose(self):
            return None

    monkeypatch.setattr(orchestrator, "get_engine", lambda _request: "engine")
    monkeypatch.setattr(
        orchestrator,
        "list_groups",
        lambda _engine: [SimpleNamespace(id=4, vm_ip="127.0.0.1")],
    )
    monkeypatch.setattr(
        orchestrator,
        "get_network",
        lambda _engine, _network_id: SimpleNamespace(
            orchestrator_version="v2", replication_factor=3
        ),
    )
    monkeypatch.setattr(orchestrator.httpx, "AsyncClient", FakeClient)

    client = TestClient(app)
    response = client.post(
        "/api/groups/4/orchestrator/start",
        json={"network_id": "custom", "peer_id": "peer-2"},
    )

    assert response.status_code == 201
    assert requests[0][0] == {
        "network_id": "custom",
        "peer_id": "peer-2",
        "replications": 3,
    }
