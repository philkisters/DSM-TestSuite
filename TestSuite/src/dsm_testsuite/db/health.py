from collections.abc import Sequence
from datetime import datetime, timezone

from dsm_db import GroupHealth
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def calculate_group_uptime(
    rows: Sequence[GroupHealth], as_of: datetime
) -> tuple[datetime | None, float, float]:
    """Return the first sample time and time-weighted uptime/downtime in seconds."""
    as_of = _as_utc(as_of)
    ordered = sorted(rows, key=lambda row: (_as_utc(row.timestamp), row.id))
    relevant = [row for row in ordered if _as_utc(row.timestamp) < as_of]
    if not relevant:
        return None, 0.0, 0.0

    uptime_seconds = 0.0
    downtime_seconds = 0.0
    for index, row in enumerate(relevant):
        started = _as_utc(row.timestamp)
        ended = (
            _as_utc(relevant[index + 1].timestamp)
            if index + 1 < len(relevant)
            else as_of
        )
        ended = min(ended, as_of)
        duration = max(0.0, (ended - started).total_seconds())
        if row.state == "OFFLINE":
            downtime_seconds += duration
        else:
            uptime_seconds += duration

    return _as_utc(relevant[0].timestamp), uptime_seconds, downtime_seconds


def save_group_health(engine: Engine, rows: list[GroupHealth]) -> None:
    """Append one (group_id, state, failures) history row per group."""
    if not rows:
        return
    with Session(engine) as session, session.begin():
        session.add_all(rows)


def list_group_health(engine: Engine) -> list[GroupHealth]:
    """Most recent health row of each group."""
    stmt = (
        select(GroupHealth)
        .distinct(GroupHealth.group_id)
        .order_by(GroupHealth.group_id, GroupHealth.timestamp.desc())
    )
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(stmt))


def list_group_health_history(engine: Engine, group_id: int, since: datetime) -> list[GroupHealth]:
    """All health rows of a specific group, ordered by timestamp descending."""
    stmt = (
        select(GroupHealth)
        .where(GroupHealth.group_id == group_id, GroupHealth.timestamp >= since)
        .order_by(GroupHealth.timestamp.desc())
    )
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(stmt))


def list_group_uptime(
    engine: Engine, group_id: int, as_of: datetime
) -> tuple[datetime | None, float, float]:
    """Calculate all recorded uptime and downtime through `as_of`."""
    stmt = (
        select(GroupHealth)
        .where(GroupHealth.group_id == group_id)
        .order_by(GroupHealth.timestamp, GroupHealth.id)
    )
    with Session(engine, expire_on_commit=False) as session:
        rows = list(session.scalars(stmt))
    return calculate_group_uptime(rows, as_of)