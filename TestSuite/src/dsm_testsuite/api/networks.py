from fastapi import APIRouter, HTTPException, Request

from .helper import get_engine
from ..db import (
    NetworkExists,
    create_network,
    list_groups,
    list_networks,
)
from ..schemas import Network, NetworkCreate

router = APIRouter(prefix="/groups/{group_id}/networks", tags=["networks"])


@router.get("", response_model=list[Network])
def get_networks(group_id: int, request: Request):
    return list_networks(get_engine(request), group_id)


@router.post("", response_model=Network, status_code=201)
def post_network(group_id: int, payload: NetworkCreate, request: Request):
    engine = get_engine(request)
    if not any(group.id == group_id for group in list_groups(engine)):
        raise HTTPException(404, f"Group {group_id} not found")
    try:
        return create_network(
            engine,
            group_id,
            payload.network_id,
            payload.orchestrator_version.value,
            payload.replication_factor,
        )
    except NetworkExists:
        raise HTTPException(
            409, f"Network '{payload.network_id}' already exists with different settings"
        )
