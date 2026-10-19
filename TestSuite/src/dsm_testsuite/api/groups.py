from fastapi import APIRouter, Request, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone, timedelta

from .helper import get_engine
from ..db import GroupExists, create_group, list_group_health, list_group_health_history, list_groups, delete_group
from ..schemas import Group, GroupCreate, GroupHealthStatus

router = APIRouter(prefix="/groups", tags=["groups"])

@router.get("/health", response_model=list[GroupHealthStatus])
def get_groups_health(request: Request):
    return list_group_health(get_engine(request))
  
@router.websocket("/health/ws")
async def health_updates(websocket: WebSocket) -> None:
    service = getattr(websocket.app.state, "health_service", None)
    if service is None:
        await websocket.close(code=1013)
        return
    await websocket.accept()
    queue = service.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_text(event.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        service.unsubscribe(queue)

# Sync handlers run in the threadpool, so blocking DB calls don't stall the event loop.
@router.get("", response_model=list[Group])
def get_groups(request: Request):
    return list_groups(get_engine(request))

@router.post("", response_model=Group, status_code=201)
def post_group(payload: GroupCreate, request: Request):
    try:
        return create_group(get_engine(request), payload.name, payload.vm_ip)
    except GroupExists:
        raise HTTPException(409, f"Group '{payload.name}' already exists")

@router.delete("/{group_id}")
def delete_group_by_id(group_id: int, request: Request):
    return delete_group(get_engine(request), group_id)
    
@router.get("/{group_id}/health", response_model=list[GroupHealthStatus])
def get_group_health(group_id: int, request: Request):
    return list_group_health_history(get_engine(request), group_id, since=datetime.now(timezone.utc) - timedelta(days=1))