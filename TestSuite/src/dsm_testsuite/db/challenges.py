import logging

from dsm_db import Challenge, Group, Run
from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ..scenario import discover_challenges
from ..schemas import ChallengeResults, GroupChallengeResult, GroupChallengeStats, GroupChallengeStatsResults
from ..schemas import Run as RunSchema

logger = logging.getLogger(__name__)


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


def group_challenge_stats(engine: Engine, group_id: int) -> GroupChallengeStatsResults:
    """Per challenge key: tries, successes, first_pass and last_fail for the given group.

    Every challenge is included, even if the group never ran it.
    """
    ended = func.coalesce(Run.finished_at, Run.started_at)
    with Session(engine) as session:
        rows = session.execute(
            select(
                Challenge.key,
                Challenge.title,
                func.count(Run.id).label("tries"),
                func.count(Run.id).filter(Run.status == "passed").label("successes"),
                func.min(case((Run.status == "passed", ended))).label("first_pass"),
                func.max(case((Run.status == "failed", ended))).label("last_fail"),
            )
            .select_from(Challenge)
            .outerjoin(Run, (Run.challenge_id == Challenge.id) & (Run.group_id == group_id))
            .group_by(Challenge.key, Challenge.title)
        ).all()
    return GroupChallengeStatsResults(
        group_id=group_id,
        stats=[
            GroupChallengeStats(
                key=r.key,
                week=r.key.split('/')[0],
                title=r.title,
                tries=r.tries,
                successes=r.successes,
                first_pass=r.first_pass,
                last_fail=r.last_fail,
            )
            for r in rows
        ]
    )