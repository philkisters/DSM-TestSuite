from datetime import datetime, timezone

from dsm_db import GroupHealth
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

# The health service probes every group once per interval.
SAMPLE_INTERVAL_SECONDS = 5.0


def calculate_group_uptime(
    online_samples: int,
    offline_samples: int,
    first_sample: datetime | None,
) -> tuple[datetime | None, float, float]:
    """Return first sample time and uptime/downtime seconds from sample counts."""
    if first_sample is None:
        return None, 0.0, 0.0
    return (
        _as_utc(first_sample),
        online_samples * SAMPLE_INTERVAL_SECONDS,
        offline_samples * SAMPLE_INTERVAL_SECONDS,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


def count_group_samples(
    engine: Engine, group_id: int
) -> tuple[int, int, datetime | None]:
    """(non-offline samples, offline samples, first sample time) of a group."""
    offline = GroupHealth.state == "OFFLINE"
    stmt = select(
        func.count().filter(~offline),
        func.count().filter(offline),
        func.min(GroupHealth.timestamp),
    ).where(GroupHealth.group_id == group_id)
    with Session(engine) as session:
        up, down, first = session.execute(stmt).one()
    return up, down, first


def list_group_uptime(
    engine: Engine, group_id: int, as_of: datetime
) -> tuple[datetime | None, float, float]:
    """Estimate uptime/downtime by counting fixed-interval samples in the DB."""
    return calculate_group_uptime(*count_group_samples(engine, group_id))
