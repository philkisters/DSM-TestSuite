from fastapi import APIRouter, Request, HTTPException, WebSocket, WebSocketDisconnect

from pydantic import ValidationError

from ..db import (
    find_run_targets, get_assertions_for_run, list_runs as list_runs_from_db, get_run as get_run_from_db, list_runs_for_challenge, list_runs_for_group
)
from .helper import get_engine, get_run_manager
from ..runs import ActiveRunExists
from ..scenario import ChallengeNotFound, load_scenario
from ..schemas import Run, RunCreate, RunStatus, RunAssertion, RunEvent

router = APIRouter(prefix="/runs", tags=["runs"])
TERMINAL = {RunStatus.PASSED, RunStatus.FAILED, RunStatus.ERROR}

@router.post("", response_model=Run, status_code=202)
async def create_run(payload: RunCreate, request: Request) -> Run:
    engine = get_engine(request)
    manager = get_run_manager(request)
    group_id, group_name, vm_ip, challenge_id, challenge_key = find_run_targets(engine, payload.group_id, payload.challenge_id)
    if group_id is None:
        raise HTTPException(404, f"Group '{payload.group_id}' not found")
    if not vm_ip:
        raise HTTPException(409, f"Group '{group_name}' has no vm_ip")
    if challenge_id is None:
        raise HTTPException(404, f"Challenge '{payload.challenge_id}' not found")
    try:
        scenario = load_scenario(challenge_key)
    except ChallengeNotFound:
        raise HTTPException(404, f"No configuration for '{challenge_key}' found")
    except ValidationError as exc:
        raise HTTPException(500, f"Invalid challenge file: {exc.errors(include_url=False)}")
    try:
        return manager.create(group_id, group_name, vm_ip, challenge_id, scenario)
    except ActiveRunExists:
        raise HTTPException(409, f"Group '{group_name}' already has an active run")


@router.get("", response_model=list[Run])
async def list_runs(request: Request) -> list[Run]:
    return list_runs_from_db(get_engine(request))


@router.get("/challenge/{challenge_id}", response_model=list[Run])
async def get_runs_by_challenge(challenge_id: int, request: Request) -> list[Run]:
    engine = get_engine(request)
    return list_runs_for_challenge(engine, challenge_id)

@router.get("/group/{group_id}", response_model=list[Run])
async def get_runs_by_group(group_id: int, request: Request) -> list[Run]:
    engine = get_engine(request)
    return list_runs_for_group(engine, group_id)

@router.get("/{run_id}", response_model=Run)
async def get_run(run_id: str, request: Request) -> Run:
    manager = get_run_manager(request)
    run = manager.runs.get(run_id) or get_run_from_db(get_engine(request), run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run

@router.get("/{run_id}/events", response_model=list[RunAssertion])
async def get_run_events(run_id: str, request: Request) -> list[RunAssertion]:
    engine = get_engine(request)
    return get_assertions_for_run(engine, run_id)

@router.websocket("/{run_id}/ws")
async def run_updates(websocket: WebSocket, run_id: str) -> None:
    manager = get_run_manager(websocket)
    if run_id in manager.runs:
        queue = manager.subscribe(run_id)
    else:
        run = get_run_from_db(get_engine(websocket), run_id)
        if run is None:
            await websocket.close(code=4404)
            return
        await websocket.accept()
        await websocket.send_text(
            RunEvent(run_id=run_id, type="status", data={"status": run.status}).model_dump_json()
        )
        await websocket.close()
        return
    await websocket.accept()
    try:
        while True:
            event = await queue.get()
            await websocket.send_text(event.model_dump_json())
            if event.type == "status" and event.data.get("status") in TERMINAL:
                break
        await websocket.close()
    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(run_id, queue)
