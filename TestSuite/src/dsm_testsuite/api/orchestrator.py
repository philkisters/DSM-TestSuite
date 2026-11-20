from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from .helper import get_engine
from ..clients import ORCHESTRATOR_PORT
from ..db import get_network, list_groups

router = APIRouter(prefix="/groups/{group_id}/orchestrator", tags=["orchestrator"])

# Forwards the browser's control calls to the group's orchestrator (same-origin, no CORS).
# The target is resolved from the stored group, never from the request, to avoid SSRF.
@router.post("/{action}")
async def forward_to_orchestrator(
    group_id: int,
    action: Literal["start", "join", "leave", "kill"],
    body: dict[str, Any],
    request: Request,
) -> Response:
    engine = get_engine(request)
    group = next((g for g in list_groups(engine) if g.id == group_id), None)
    if group is None:
        raise HTTPException(404, f"Group {group_id} not found")

    network = get_network(engine, body["network_id"]) if body.get("network_id") else None
    if action == "start" and network is not None:
        if network.orchestrator_version == "v2" and network.replication_factor is not None:
            body["replications"] = network.replication_factor
        else:
            body.pop("replications", None)

    url = f"http://{group.vm_ip}:{ORCHESTRATOR_PORT}/{action}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            upstream = await http.post(
                url,
                json=body,
                headers={"Content-Type": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Orchestrator of group {group_id} unreachable: {exc!r}")

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
