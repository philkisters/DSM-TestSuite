from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from dsm_testsuite.api import groups
from dsm_testsuite.db.health import calculate_group_uptime


def test_calculate_group_uptime_multiplies_sample_counts_by_interval():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    since, uptime, downtime = calculate_group_uptime(4, 3, start)

    assert since == start
    assert uptime == 20
    assert downtime == 15


def test_calculate_group_uptime_handles_empty_history_and_naive_timestamps():
    assert calculate_group_uptime(0, 0, None) == (None, 0.0, 0.0)
    since, _, _ = calculate_group_uptime(1, 0, datetime(2026, 1, 1))
    assert since == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_group_uptime_endpoint_returns_durations_and_percentages(monkeypatch):
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(groups, "get_engine", lambda _request: "engine")
    monkeypatch.setattr(
        groups,
        "list_group_uptime",
        lambda _engine, _group_id, _as_of: (since, 90.0, 10.0),
    )

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    result = groups.get_group_uptime(7, request)

    assert result.group_id == 7
    assert result.since == since
    assert result.uptime_seconds == 90
    assert result.downtime_seconds == 10
    assert result.uptime_percentage == 90
    assert result.downtime_percentage == 10



def test_group_uptime_endpoint_prefers_in_memory_counters(monkeypatch):
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(groups, "get_engine", lambda _request: "engine")
    service = SimpleNamespace(get_uptime=lambda _group_id: (since, 30.0, 10.0))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(health_service=service)))

    result = groups.get_group_uptime(7, request)

    assert result.uptime_seconds == 30
    assert result.downtime_seconds == 10
