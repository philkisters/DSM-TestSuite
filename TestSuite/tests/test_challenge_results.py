from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from dsm_db import Challenge, Group, Run
from dsm_testsuite.db.challenges import get_challenge_results_for_group


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(_type, _compiler, **_kwargs):
    return "JSON"


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", execution_options={"schema_translate_map": {"core": None}})
    for table in (Group.__table__, Challenge.__table__, Run.__table__):
        table.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all([
            Group(id=1, name="one", archived=False),
            Group(id=2, name="two", archived=False),
            Group(id=3, name="archived", archived=True),
            Challenge(id=1, key="week/test", title="test", steps=1, archived=False),
            Challenge(id=2, key="week/other", title="other", steps=1, archived=False),
        ])
    yield engine
    engine.dispose()


BASE = datetime(2024, 1, 1, 12)


def make_run(id, start, duration, messages, *, group=1, challenge=1, status="passed"):
    return Run(
        id=id,
        group_id=group,
        challenge_id=challenge,
        status=status,
        started_at=BASE + timedelta(seconds=start),
        finished_at=None if duration is None else BASE + timedelta(seconds=start + duration),
        metrics=None if messages is None else {"message_count": messages},
    )


def test_three_independent_success_tuples_and_run_history(engine):
    with Session(engine) as session, session.begin():
        session.add_all([
            make_run("first", 0, 100, 100),
            make_run("fewest", 110, 80, 5),
            make_run("fastest", 200, 10, 30),
            make_run("failed", 220, 1, 0, status="failed"),
            make_run("other-group", 10, 5, 2, group=2),
            make_run("archived", 10, 2, 1, group=3),
            make_run("other-challenge", 10, 2, 1, challenge=2),
        ])

    results = get_challenge_results_for_group(engine, 1, 1)
    group = results.group_results[1]
    assert group.status == "passed"
    assert group.timestamp == BASE + timedelta(seconds=100)
    assert group.first_success == (100, 100.0, BASE + timedelta(seconds=100))
    assert group.lowest_message_count == (5, 80.0, BASE + timedelta(seconds=190))
    assert group.shortest_duration == (30, 10.0, BASE + timedelta(seconds=210))
    assert results.group_results[2].first_success == (2, 5.0, BASE + timedelta(seconds=15))
    assert 3 not in results.group_results
    assert [run.id for run in results.run_results] == ["failed", "fastest", "fewest", "first"]
    wire = results.model_dump(mode="json")["group_results"]["1"]
    assert wire["lowest_message_count"] == [5, 80.0, "2024-01-01T12:03:10"]
    assert wire["shortest_duration"] == [30, 10.0, "2024-01-01T12:03:30"]


def test_missing_metrics_zero_and_unfinished_runs(engine):
    with Session(engine) as session, session.begin():
        session.add_all([
            make_run("no-metrics", 0, 40, None),
            make_run("no-duration", 50, None, 0),
            make_run("zero-duration", 60, 0, None),
        ])

    group = get_challenge_results_for_group(engine, 1, 1).group_results[1]
    assert group.first_success == (None, 40.0, BASE + timedelta(seconds=40))
    assert group.lowest_message_count == (0, None, BASE + timedelta(seconds=50))
    assert group.shortest_duration == (None, 0.0, BASE + timedelta(seconds=60))


def test_completion_order_ties_and_failed_groups(engine):
    with Session(engine) as session, session.begin():
        session.add_all([
            make_run("slow-first-start", 0, 100, 10),
            make_run("earlier-completion", 10, 20, 10),
            make_run("equal-duration", 100, 20, 20),
            make_run("failed-late", 0, 200, 0, group=2, status="failed"),
            make_run("error-early", 50, 20, 0, group=2, status="error"),
        ])

    results = get_challenge_results_for_group(engine, 1, 1)
    group = results.group_results[1]
    assert group.first_success == (10, 20.0, BASE + timedelta(seconds=30))
    assert group.lowest_message_count == group.first_success
    assert group.shortest_duration == group.first_success
    failed = results.group_results[2]
    assert failed.status == "failed"
    assert failed.timestamp == BASE + timedelta(seconds=200)
    assert failed.first_success is None
    assert failed.lowest_message_count is None
    assert failed.shortest_duration is None


def test_unrun_groups_have_no_results(engine):
    result = get_challenge_results_for_group(engine, 1, 1)
    assert result.run_results == []
    assert result.group_results[1].model_dump() == {
        "status": "failed",
        "timestamp": None,
        "first_success": None,
        "lowest_message_count": None,
        "shortest_duration": None,
    }


def test_success_without_recorded_metrics_has_no_ranked_results(engine):
    with Session(engine) as session, session.begin():
        session.add(make_run("incomplete", 0, None, None))

    group = get_challenge_results_for_group(engine, 1, 1).group_results[1]
    assert group.first_success == (None, None, BASE)
    assert group.lowest_message_count is None
    assert group.shortest_duration is None
