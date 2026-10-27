from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from dsm_testsuite.api import groups
from dsm_testsuite.db.health import calculate_group_uptime


def _sample(sample_id: int, state: str, timestamp: datetime):
    return SimpleNamespace(id=sample_id, state=state, timestamp=timestamp)


def test_calculate_group_uptime_weights_each_health_state_by_sample_interval():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [
        _sample(1, "ONLINE", start),
        _sample(2, "NOT_RESPONDING", start + timedelta(seconds=10)),
        _sample(3, "OFFLINE", start + timedelta(seconds=20)),
    ]

    since, uptime, downtime = calculate_group_uptime(rows, start + timedelta(seconds=35))

    assert since == start
    assert uptime == 20
    assert downtime == 15


def test_calculate_group_uptime_handles_empty_history_and_naive_timestamps():
    as_of = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)

    assert calculate_group_uptime([], as_of) == (None, 0.0, 0.0)
    since, uptime, downtime = calculate_group_uptime(
        [_sample(1, "OFFLINE", datetime(2026, 1, 1))], as_of
    )
    assert since == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert uptime == 0
    assert downtime == 10


def test_calculate_group_uptime_does_not_count_time_before_first_sample():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [_sample(1, "OFFLINE", start + timedelta(seconds=20))]

    since, uptime, downtime = calculate_group_uptime(rows, start + timedelta(seconds=30))

    assert since == start + timedelta(seconds=20)
    assert uptime == 0
    assert downtime == 10


def test_calculate_group_uptime_ignores_samples_after_calculation_time():
    as_of = datetime(2026, 1, 1, tzinfo=timezone.utc)

    since, uptime, downtime = calculate_group_uptime(
        [_sample(1, "ONLINE", as_of + timedelta(seconds=1))], as_of
    )

    assert since is None
    assert uptime == 0
    assert downtime == 0


def test_group_uptime_endpoint_returns_durations_and_percentages(monkeypatch):
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(groups, "get_engine", lambda _request: "engine")
    monkeypatch.setattr(
        groups,
        "list_group_uptime",
        lambda _engine, _group_id, _as_of: (since, 90.0, 10.0),
    )

    result = groups.get_group_uptime(7, None)

    assert result.group_id == 7
    assert result.since == since
    assert result.uptime_seconds == 90
    assert result.downtime_seconds == 10
    assert result.uptime_percentage == 90
    assert result.downtime_percentage == 10
