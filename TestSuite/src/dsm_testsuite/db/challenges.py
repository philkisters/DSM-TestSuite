import logging

from dsm_db import Challenge, Group, Run
from sqlalchemy import case, func, select, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ..scenario import discover_challenges
from ..schemas import (
    ChallengeResults, 
    GroupChallengeResult, 
    GroupChallengeStats, 
    GroupChallengeStatsResults,
    CategoryRankings,
    ChallengeCategoryStats,
    GroupChallengeOverview,
)
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

    Each successful result is (message count, duration in seconds, completion
    timestamp). Missing metrics are None. For groups without a success, timestamp
    is the latest failed/errored run's completion time, if any.
    """
    with Session(engine) as session:
        groups = session.scalars(select(Group.id).where(Group.archived.is_(False)))
        group_results = {gid: GroupChallengeResult(status="failed") for gid in groups}
        runs = session.scalars(
            select(Run).where(Run.challenge_id == challenge_id).order_by(Run.started_at, Run.id)
        )
        run_results: list[RunSchema] = []
        for run in runs:
            result = group_results.get(run.group_id)
            run_schema = None
            if run.group_id == group_id or (result is not None and run.status == "passed"):
                run_schema = RunSchema.model_validate(run)
            if run.group_id == group_id:
                assert run_schema is not None
                run_results.append(run_schema)
            if result is None:
                continue
            when = run.finished_at or run.started_at
            if run.status == "passed":
                assert run_schema is not None
                message_count = run_schema.message_count
                duration = run_schema.duration_seconds
                success = (message_count, duration, when)
                result.status = "passed"
                if result.first_success is None or when < result.first_success[2]:
                    result.first_success = success
                    result.timestamp = when
                if message_count is not None and (
                    result.lowest_message_count is None
                    or (message_count, when) < (
                        result.lowest_message_count[0], result.lowest_message_count[2]
                    )
                ):
                    result.lowest_message_count = (message_count, duration, when)
                if duration is not None and (
                    result.shortest_duration is None
                    or (duration, when) < (result.shortest_duration[1], result.shortest_duration[2])
                ):
                    result.shortest_duration = (message_count, duration, when)
            elif run.status in ("failed", "error") and result.status != "passed":
                if result.timestamp is None or when > result.timestamp:
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


def group_challenge_overview(engine: Engine, group_id: int) -> GroupChallengeOverview:
    """Get comprehensive overview of a group's challenge performance including rankings.
    
    Returns:
        - Total number of challenges passed by the group
        - Count of first/second/third places across time, duration, and messages categories
        - Challenge statistics for each challenge
    """
    with Session(engine) as session:
        # Get group name
        group = session.execute(select(Group).where(Group.id == group_id)).scalar_one_or_none()
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        group_name = group.name
        
        # Get all non-archived challenges
        all_challenges = session.scalars(
            select(Challenge).where(Challenge.archived.is_(False)).order_by(Challenge.key)
        ).all()
        
        # Get stats for each challenge for this group
        ended = func.coalesce(Run.finished_at, Run.started_at)
        challenge_stats_rows = session.execute(
            select(
                Challenge.id,
                Challenge.key,
                Challenge.title,
                func.count(Run.id).label("tries"),
                func.count(Run.id).filter(Run.status == "passed").label("successes"),
                func.min(case((Run.status == "passed", ended))).label("first_pass"),
                func.max(case((Run.status == "failed", ended))).label("last_fail"),
            )
            .select_from(Challenge)
            .outerjoin(Run, (Run.challenge_id == Challenge.id) & (Run.group_id == group_id))
            .where(Challenge.archived.is_(False))
            .group_by(Challenge.id, Challenge.key, Challenge.title)
            .order_by(Challenge.key)
        ).all()
        
        challenge_stats = [
            GroupChallengeStats(
                key=r.key,
                week=r.key.split('/')[0],
                title=r.title,
                tries=r.tries,
                successes=r.successes,
                first_pass=r.first_pass,
                last_fail=r.last_fail,
            )
            for r in challenge_stats_rows
        ]
        
        # Count total passed challenges
        total_passed = sum(1 for stat in challenge_stats if stat.successes > 0)
        
        # Get rankings for each category and each challenge
        first_places = {"time": 0, "duration": 0, "messages": 0}
        second_places = {"time": 0, "duration": 0, "messages": 0}
        third_places = {"time": 0, "duration": 0, "messages": 0}
        
        for challenge in all_challenges:
            # Get all passed runs for this challenge
            passed_runs = session.scalars(
                select(Run)
                .where(
                    and_(
                        Run.challenge_id == challenge.id,
                        Run.status == "passed"
                    )
                )
                .order_by(Run.finished_at, Run.id)
            ).all()
            
            if not passed_runs:
                continue
            
            # Determine rankings by time (earliest completion)
            time_ranked = sorted(passed_runs, key=lambda r: r.finished_at or r.started_at)
            for idx, run in enumerate(time_ranked[:3]):
                if run.group_id == group_id:
                    if idx == 0:
                        first_places["time"] += 1
                    elif idx == 1:
                        second_places["time"] += 1
                    elif idx == 2:
                        third_places["time"] += 1
                    break
            
            # Determine rankings by duration (shortest time between start and finish)
            duration_ranked = sorted(
                [r for r in passed_runs if r.finished_at is not None],
                key=lambda r: (r.finished_at - r.started_at).total_seconds()
            )
            for idx, run in enumerate(duration_ranked[:3]):
                if run.group_id == group_id:
                    if idx == 0:
                        first_places["duration"] += 1
                    elif idx == 1:
                        second_places["duration"] += 1
                    elif idx == 2:
                        third_places["duration"] += 1
                    break
            
            # Determine rankings by messages (fewest messages)
            messages_ranked = sorted(
                [r for r in passed_runs if r.metrics and "message_count" in r.metrics],
                key=lambda r: r.metrics.get("message_count", float("inf"))
            )
            for idx, run in enumerate(messages_ranked[:3]):
                if run.group_id == group_id:
                    if idx == 0:
                        first_places["messages"] += 1
                    elif idx == 1:
                        second_places["messages"] += 1
                    elif idx == 2:
                        third_places["messages"] += 1
                    break
        
    return GroupChallengeOverview(
        group_id=group_id,
        group_name=group_name,
        total_passed_challenges=total_passed,
        first_places=first_places,
        second_places=second_places,
        third_places=third_places,
        challenges_by_status=challenge_stats,
    )