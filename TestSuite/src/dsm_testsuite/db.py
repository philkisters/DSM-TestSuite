
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from dsm_db import Challenge, Group, GroupHealth, Run, RunAssertion
from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .scenario import discover_challenges
from .schemas import ChallengeResults, GroupChallengeResult
from .schemas import Run as RunSchema

logger = logging.getLogger(__name__)


class GroupExists(Exception):
    pass


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def sync_challenges(engine: Engine) -> None:
    """Make core.challenges reflect the challenge files.

    New files are inserted, changed ones updated, and challenges whose file is
    gone or marked `archived: true` are archived.
    """
    challenges = discover_challenges()
    with Session(engine) as session, session.begin():
        for key, scenario in challenges.items():
            stmt = insert(Challenge).values(
                key=key,
                title=scenario.name,
                description=scenario.description,
                archived=scenario.archived,
                steps=len(scenario.steps),
            )
            session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[Challenge.key],
                    set_={
                        "title": stmt.excluded.title,
                        "description": stmt.excluded.description,
                        "archived": stmt.excluded.archived,
                        "steps": stmt.excluded.steps,
                    },
                )
            )
        for challenge in session.scalars(select(Challenge)):
            if challenge.key not in challenges:
                challenge.archived = True
    logger.info("Synced %d challenge(s)", len(challenges))


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

def save_assertion(
    engine: Engine, run_id: str, step_index: int, name: str, params: dict, passed: bool,
    message: str | None,
) -> None:
    with Session(engine) as session, session.begin():
        session.add(
            RunAssertion(
                run_id=run_id, step_index=step_index, name=name, params=params,
                passed=passed, message=message,
            )
        )

def get_assertions_for_run(engine: Engine, run_id: str) -> list[RunAssertion]:
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(select(RunAssertion).where(RunAssertion.run_id == run_id).order_by(RunAssertion.step_index)))


def list_groups(engine: Engine) -> list[Group]:
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(select(Group).where(Group.archived == False).order_by(Group.name)))


def create_group(engine: Engine, name: str, vm_ip: str) -> Group:
    group = Group(name=name, vm_ip=vm_ip)
    try:
        with Session(engine, expire_on_commit=False) as session, session.begin():
            session.add(group)
    except IntegrityError:
        raise GroupExists(name)
    return group

def delete_group(engine: Engine, group_id: int) -> None:
    with Session(engine) as session, session.begin():
        session.execute(
            update(Group)
            .where(Group.id == group_id)
            .values(archived = True)
        )

def list_challenges(engine: Engine) -> list[Challenge]:
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(select(Challenge).order_by(Challenge.key)))
    
def get_challenge_results_for_group(
    engine: Engine, challenge_id: int, group_id: int
) -> ChallengeResults:
    """Per-group outcome of a challenge plus all runs of `group_id` for it.

    A group passed with the timestamp of its first passed run; otherwise it is failed
    with the timestamp of its latest failed/errored run (None if there is none).
    """
    with Session(engine) as session:
        groups = session.scalars(select(Group.id).where(Group.archived.is_(False)))
        group_results = {gid: GroupChallengeResult(status="failed") for gid in groups}
        runs = session.scalars(
            select(Run).where(Run.challenge_id == challenge_id).order_by(Run.started_at)
        )
        run_results: list[RunSchema] = []
        for run in runs:
            if run.group_id == group_id:
                run_results.append(RunSchema.model_validate(run))
            result = group_results.get(run.group_id)
            if result is None:
                continue
            when = run.finished_at or run.started_at
            if run.status == "passed":
                if result.status != "passed":
                    group_results[run.group_id] = GroupChallengeResult(
                        status="passed", timestamp=when
                    )
            elif run.status in ("failed", "error") and result.status != "passed":
                result.timestamp = when
        run_results.reverse()
    return ChallengeResults(group_results=group_results, run_results=run_results)



def save_group_health(engine: Engine, rows: list[GroupHealth]) -> None:
    """Append one (group_id, state, failures) history row per group."""
    if not rows:
        return
    now = datetime.now(timezone.utc)
    with Session(engine) as session, session.begin():
        session.add_all(
            rows
        )


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