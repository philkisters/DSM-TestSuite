from datetime import datetime

from dsm_db import GroupHealth
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


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
