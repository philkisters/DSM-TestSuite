from dsm_db import RunAssertion, RunError
from sqlalchemy import select, union_all, literal, cast, String, Integer, Boolean, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


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


def get_events_for_run(engine: Engine, run_id: str) -> list[dict]:
    """Get both assertions and errors for a run, ordered by step index and created_at."""
    with Session(engine, expire_on_commit=False) as session:
        # Query assertions
        assertions_query = select(
            RunAssertion.id,
            RunAssertion.run_id,
            RunAssertion.step_index,
            RunAssertion.name,
            RunAssertion.params,
            RunAssertion.created_at,
            cast(literal("assertion"), String).label("type"),
            RunAssertion.passed,
            RunAssertion.message,
            cast(literal(None), Integer).label("error_code"),
            cast(literal(None), String).label("error_text"),
        ).where(RunAssertion.run_id == run_id)
        
        # Query errors
        errors_query = select(
            RunError.id,
            RunError.run_id,
            RunError.step_index,
            RunError.name,
            RunError.params,
            RunError.created_at,
            cast(literal("error"), String).label("type"),
            cast(literal(None), Boolean).label("passed"),
            cast(literal(None), String).label("message"),
            RunError.error_code,
            RunError.error_text,
        ).where(RunError.run_id == run_id)
        
        # Union and order by step_index then created_at
        combined = union_all(assertions_query, errors_query).order_by(
            text("step_index"),
            text("created_at")
        )
        
        results = []
        for row in session.execute(combined):
            results.append({
                "id": row[0],
                "run_id": row[1],
                "step_index": row[2],
                "name": row[3],
                "params": row[4],
                "created_at": row[5],
                "type": row[6],
                "passed": row[7],
                "message": row[8],
                "error_code": row[9],
                "error_text": row[10],
            })
        return results
