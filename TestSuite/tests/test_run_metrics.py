import asyncio

import httpx
import pytest

from dsm_testsuite import runs
from dsm_testsuite.scenario import Scenario
from dsm_testsuite.schemas import Run, RunStatus


@pytest.mark.parametrize("status", [RunStatus.PASSED, RunStatus.FAILED, RunStatus.ERROR])
def test_message_count_is_fetched_before_client_closes(monkeypatch, status):
    requests = []
    updates = []
    real_client = httpx.AsyncClient

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={"count": 42})

    monkeypatch.setattr(
        runs.httpx, "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs),
    )

    async def execute_scenario(scenario, ctx, report):
        return status

    monkeypatch.setattr(runs, "execute_scenario", execute_scenario)
    manager = runs.RunManager(None)

    async def persist(fn, *args):
        if fn is runs.update_run:
            updates.append((args[0].status, args[1:]))

    monkeypatch.setattr(manager, "_persist", persist)
    run = Run(group_id=1, challenge_id=1, network_id="net-test")

    asyncio.run(manager._execute(run, Scenario(name="test", steps=[]), "127.0.0.1"))

    assert len(requests) == 1
    assert requests[0].url.path == "/api/message-stats"
    assert requests[0].url.params["network_id"] == "net-test"
    assert updates[-1] == (status, (42,))
    assert run.finished_at is not None


@pytest.mark.parametrize("scenario_crashes", [False, True])
def test_message_count_failure_is_logged_and_status_is_preserved(monkeypatch, caplog, scenario_crashes):
    updates = []
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        runs.httpx, "AsyncClient",
        lambda **kwargs: real_client(
            transport=httpx.MockTransport(lambda request: httpx.Response(503)), **kwargs
        ),
    )

    async def execute_scenario(scenario, ctx, report):
        if scenario_crashes:
            raise RuntimeError("scenario crashed")
        return RunStatus.PASSED

    monkeypatch.setattr(runs, "execute_scenario", execute_scenario)
    manager = runs.RunManager(None)

    async def persist(fn, *args):
        if fn is runs.update_run:
            updates.append((args[0].status, args[1:]))

    monkeypatch.setattr(manager, "_persist", persist)
    run = Run(group_id=1, challenge_id=1, network_id="net-test")

    asyncio.run(manager._execute(run, Scenario(name="test", steps=[]), "127.0.0.1"))

    expected_status = RunStatus.ERROR if scenario_crashes else RunStatus.PASSED
    assert updates[-1] == (expected_status, (None,))
    assert "Could not fetch message count" in caplog.text
