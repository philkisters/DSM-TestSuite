import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from dsm_db import Challenge, Group, Run
from sqlalchemy import select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ..schemas import Run as RunSchema

logger = logging.getLogger(__name__)


@dataclass
class StaleRun:
    run_id: str
    network_id: str | None
    vm_ip: str | None
    peers: list[str]


def fail_stale_runs(engine: Engine) -> list[StaleRun]:
    """Mark runs left "pending"/"running" by a previous process as "error" and return them."""
    with Session(engine) as session, session.begin():
        rows = session.execute(
            select(Run.id, Run.network_id, Run.metrics, Group.vm_ip)
            .join(Group, Group.id == Run.group_id)
            .where(Run.status.in_(["pending", "running"]))
        ).all()
        session.execute(
            update(Run)
            .where(Run.id.in_([r.id for r in rows]))
            .values(status="error", finished_at=datetime.now(timezone.utc))
        )
    logger.info("Marked %d stale run(s) as error", len(rows))
    return [
        StaleRun(r.id, r.network_id, r.vm_ip, list((r.metrics or {}).get("peers", [])))
        for r in rows
    ]


def update_run_peers(engine: Engine, run_id: str, peers: list[str]) -> None:
    """Remember which peers a run started, so they can be stopped after a crash."""
    with Session(engine) as session, session.begin():
        session.execute(update(Run).where(Run.id == run_id).values(metrics={"peers": peers}))


def find_run_targets(
    engine: Engine, group_id: int, challenge_id: int
) -> tuple[int | None, str | None, str | None, int | None, str | None]:
    """(group id, group name, group vm_ip, challenge id); None where not found."""
    with Session(engine) as session:
        row = session.execute(select(Group.id, Group.name, Group.vm_ip).where(Group.id == group_id)).first()
        challenge = session.execute(
            select(Challenge.id, Challenge.key).where(
                Challenge.id == challenge_id, Challenge.archived.is_(False)
            )
        ).first()
    return (row.id if row else None), (row.name if row else None), (row.vm_ip if row else None), (challenge.id if challenge else None), (challenge.key if challenge else None)


def insert_run(engine: Engine, run: "RunSchema") -> None:
    with Session(engine) as session, session.begin():
        session.add(
            Run(
                id=run.id,
                group_id=run.group_id,
                challenge_id=run.challenge_id,
                network_id=run.network_id,
                seed=run.seed,
                status=run.status.value,
                started_at=run.started_at,
            )
        )


def update_run(engine: Engine, run: "RunSchema") -> None:
    with Session(engine) as session, session.begin():
        session.execute(
            update(Run)
            .where(Run.id == run.id)
            .values(status=run.status.value, finished_at=run.finished_at)
        )


def get_run(engine: Engine, run_id: str) -> "RunSchema | None":
    with Session(engine) as session:
        row = session.get(Run, run_id)
        return RunSchema.model_validate(row) if row else None


def list_runs(engine: Engine) -> list["RunSchema"]:
    with Session(engine) as session:
        rows = session.scalars(select(Run).order_by(Run.started_at.desc()))
        return [RunSchema.model_validate(row) for row in rows]


def list_runs_for_challenge(engine: Engine, challenge_id: str) -> list["RunSchema"]:
    with Session(engine) as session:
        rows = session.scalars(select(Run).where(Run.challenge_id == challenge_id).order_by(Run.started_at.desc()))
        return [RunSchema.model_validate(row) for row in rows]


def list_runs_for_group(engine: Engine, group_id: int) -> list["RunSchema"]:
    with Session(engine) as session:
        rows = session.scalars(select(Run).where(Run.group_id == group_id).order_by(Run.started_at.desc()))
        return [RunSchema.model_validate(row) for row in rows]
