from dsm_db import RunError
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def save_error(
    engine: Engine, run_id: str, step_index: int, name: str, params: dict,
    error_code: int | None, error_text: str,
) -> None:
    with Session(engine) as session, session.begin():
        session.add(
            RunError(
                run_id=run_id, step_index=step_index, name=name, params=params,
                error_code=error_code, error_text=error_text,
            )
        )


def get_errors_for_run(engine: Engine, run_id: str) -> list[RunError]:
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(select(RunError).where(RunError.run_id == run_id)))
