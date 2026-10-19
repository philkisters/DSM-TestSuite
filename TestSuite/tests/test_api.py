import json
import re
import types

import pytest
import httpx
from fastapi.testclient import TestClient

from dsm_testsuite import runs
from dsm_testsuite.api import routes
from dsm_testsuite.main import app
from dsm_testsuite.runs import manager
from dsm_testsuite.scenario import ChallengeNotFound, load_scenario
from dsm_testsuite.schemas import Run, RunStatus


def test_load_first_peer():
    scenario = load_scenario("week-0/first-peer")
    assert scenario.name == "first-peer"
    assert len(scenario.steps) == 8


@pytest.mark.parametrize("bad", ["nope/x", "../pyproject", "week-0"])
def test_bad_challenge(bad):
    with pytest.raises(ChallengeNotFound):
        load_scenario(bad)


async def _no_sleep(_seconds):
    pass


class _FakeNetwork:
    """Orchestrator (:9090) and proxy in one; `leaky=True` never unregisters on kill."""

    def __init__(self) -> None:
        self.reset()

    def reset(self, leaky: bool = False) -> None:
        self.peers: set[str] = set()
        self.leaky = leaky

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json=[{"peerId": p} for p in sorted(self.peers)])
        peer = json.loads(request.content)["peer_id"]
        if request.url.path == "/start":
            self.peers.add(peer)
        elif request.url.path == "/kill" and not self.leaky:
            self.peers.discard(peer)
        return httpx.Response(200, json={})


_REAL_CLIENT = httpx.AsyncClient
network = _FakeNetwork()


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    app.state.engine = object()
    manager.runs.clear()
    manager.events.clear()
    manager.subscribers.clear()
    monkeypatch.setattr(
        routes,
        "find_run_targets",
        lambda e, g, c: (
            {"group-4": 1, "group-5": 2}.get(g),
            "10.0.0.4",
            1 if c == "week-0/first-peer" else None,
        ),
    )
    monkeypatch.setattr(
        "dsm_testsuite.steps.actions.asyncio", types.SimpleNamespace(sleep=_no_sleep)
    )
    network.reset()
    monkeypatch.setattr(
        runs.httpx,
        "AsyncClient",
        lambda **kw: _REAL_CLIENT(transport=httpx.MockTransport(network), **kw),
    )
    yield
    manager.runs.clear()
    manager.events.clear()
    manager.subscribers.clear()
    del app.state.engine


def test_run_lifecycle_and_ws():
    with TestClient(app) as client:
        resp = client.post("/api/runs", json={"group": "group-4", "challenge": "week-0/first-peer"})
        assert resp.status_code == 202
        run = resp.json()
        assert re.fullmatch(r"net-group-4-1-[A-Za-z0-9]{8}", run["network_id"])
        with client.websocket_connect(f"/api/runs/{run['id']}/ws") as ws:
            events = []
            while True:
                try:
                    events.append(ws.receive_json())
                except Exception:
                    break
        assert events[-1]["data"]["status"] == "passed"
        assert sum(e["type"] == "step" for e in events) == 8
        done = client.get(f"/api/runs/{run['id']}").json()
        assert done["status"] == "passed" and done["finished_at"] and done["network_id"]


@pytest.mark.parametrize("group,challenge", [("g", "week-0/first-peer"), ("group-4", "week-9/x")])
def test_unknown_group_or_challenge(group, challenge):
    with TestClient(app) as client:
        r = client.post("/api/runs", json={"group": group, "challenge": challenge})
        assert r.status_code == 404


@pytest.mark.parametrize("status", [RunStatus.PENDING, RunStatus.RUNNING])
def test_create_run_rejects_active_run_for_group(status):
    active_run = Run(
        group_id=1,
        challenge_id=99,
        status=status,
    )
    manager.runs[active_run.id] = active_run

    with TestClient(app) as client:
        response = client.post(
            "/api/runs",
            json={"group": "group-4", "challenge": "week-0/first-peer"},
        )

    assert response.status_code == 409


def test_active_run_does_not_block_another_group():
    active_run = Run(group_id=1, challenge_id=1, status=RunStatus.RUNNING)
    manager.runs[active_run.id] = active_run

    with TestClient(app) as client:
        response = client.post(
            "/api/runs",
            json={"group": "group-5", "challenge": "week-0/first-peer"},
        )

    assert response.status_code == 202


def test_group_create_validation():
    with TestClient(app) as client:
        assert client.post("/api/groups", json={"name": "g", "vm_ip": "nope"}).status_code == 422
        assert client.post("/api/groups", json={"name": " ", "vm_ip": "10.0.0.1"}).status_code == 422


def test_settings_env_overrides_dotenv(tmp_path, monkeypatch):
    from dsm_testsuite.config import Settings

    (tmp_path / ".env").write_text("PORT=1111\nDATABASE_URL=from-file\nUNKNOWN=x\n")
    monkeypatch.setenv("PORT", "2222")
    s = Settings(_env_file=tmp_path / ".env")
    assert s.port == 2222 and s.database_url == "from-file"


def _run_and_collect(client):
    resp = client.post("/api/runs", json={"group": "group-4", "challenge": "week-0/first-peer"})
    run = resp.json()
    with client.websocket_connect(f"/api/runs/{run['id']}/ws") as ws:
        events = []
        while True:
            try:
                events.append(ws.receive_json())
            except Exception:
                break
    return events


def test_failed_assertion_ends_run():
    network.leaky = True
    with TestClient(app) as client:
        events = _run_and_collect(client)
    assert events[-1]["data"]["status"] == "failed"
    steps = [e["data"] for e in events if e["type"] == "step"]
    assert steps[-1]["status"] == "failed" and steps[-1]["name"] == "peer-not-registered"
    assert len(steps) == 8


def test_unknown_step_rejected():
    from dsm_testsuite.scenario import Scenario

    with pytest.raises(ValueError, match="unknown action"):
        Scenario.model_validate({"name": "x", "steps": [{"action": "nope"}]})


def test_kill_stale_peers(monkeypatch):
    import asyncio

    from dsm_testsuite import cleanup
    from dsm_testsuite.db import StaleRun

    network.peers = {"registered-only"}
    killed = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json=[{"peerId": p} for p in sorted(network.peers)])
        killed.append((request.url.host, request.url.port, json.loads(request.content)))
        return httpx.Response(200, json={})

    monkeypatch.setattr(
        cleanup.httpx, "AsyncClient", lambda **kw: _REAL_CLIENT(transport=httpx.MockTransport(handler), **kw)
    )
    stale = [StaleRun("r1", "net-1", "10.0.0.4", ["started-only"]), StaleRun("r2", None, None, [])]
    asyncio.run(cleanup.kill_stale_peers(stale))
    assert sorted(k[2]["peer_id"] for k in killed) == ["registered-only", "started-only"]
    assert all(k[:2] == ("10.0.0.4", 9090) and k[2]["network_id"] == "net-1" for k in killed)
