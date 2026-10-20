from dsm_db import RunAssertion
from sqlalchemy import select
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
