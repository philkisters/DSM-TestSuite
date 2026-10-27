from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from .helper import get_engine
from ..clients import ORCHESTRATOR_PORT
from ..db import list_groups

router = APIRouter(prefix="/groups/{group_id}/orchestrator", tags=["orchestrator"])

# Forwards the browser's control calls to the group's orchestrator (same-origin, no CORS).
# The target is resolved from the stored group, never from the request, to avoid SSRF.
@router.post("/{action}")
async def forward_to_orchestrator(
    group_id: int,
    action: Literal["start", "join", "leave", "kill"],
    request: Request,
) -> Response:
    group = next((g for g in list_groups(get_engine(request)) if g.id == group_id), None)
    if group is None:
        raise HTTPException(404, f"Group {group_id} not found")

    url = f"http://{group.vm_ip}:{ORCHESTRATOR_PORT}/{action}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            upstream = await http.post(
                url,
                content=await request.body(),
                headers={"Content-Type": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Orchestrator of group {group_id} unreachable: {exc!r}")

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
