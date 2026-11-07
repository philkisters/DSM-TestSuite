"""REST (status, peers) and WebSocket (live message feed) endpoint."""
import asyncio
import json
import time

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ConfigDict
from dsm_protocol import Message

from .hub import Hub
from .recorder import Recorder
from .registry import Registry
from .relay import Stats


def create_app(registry: Registry, hub: Hub, recorder: Recorder, stats: Stats) -> FastAPI:
    app = FastAPI(title="DSM Proxy")

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/status")
    async def status():
        return {
            "uptimeSeconds": round(time.time() - stats.started, 1),
            "peers": len(registry.peers()),
            "networks": registry.networks(),
            "messagesRelayed": stats.relayed,
            "messagesFailed": stats.failed,
            "messagesInvalid": stats.invalid,
            "eventsDropped": recorder.dropped,
            "eventsQueued": recorder.queue.qsize(),
        }

    @app.get("/api/peers")
    async def peers(network_id: str | None = None):
        return [p.to_json() for p in registry.peers(network_id)]
    
    @app.get("/api/networks")
    async def networks():
        return registry.networks()

    @app.get("/api/registry-events")
    async def registry_events(network_id: str | None = None, peer_id: str | None = None,
                              limit: int = 100):
        async with recorder.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT ts, network_id, peer_id, event, host, port, peer_data, message FROM proxy.registry_events "
                "WHERE ($1::text IS NULL OR network_id = $1) AND ($2::text IS NULL OR peer_id = $2) "
                "ORDER BY ts DESC LIMIT $3", network_id, peer_id, min(max(limit, 1), 1000))
        return [{**r, "ts": r["ts"].isoformat(),
                 "peer_data": json.loads(r["peer_data"]) if r["peer_data"] else None}
                for r in map(dict, rows)]

    @app.get("/api/networks/{network_id}/peers")
    async def network_peers(network_id: str):
        return [p.to_json() for p in registry.peers(network_id)]
    
    @app.get("/api/message-stats")
    async def message_stats(network_id: str, exclude_sender: str = "TestSuite", status: str = "forwarded"):
        """Count successfully forwarded messages for a network, excluding a sender.
        
        Args:
            network_id: The network to query (required)
            exclude_sender: Exclude messages from this peer sender (default: TestSuite)
            status: Filter by message status (default: forwarded for successful messages)
        
        Returns:
            {"count": int, "network_id": str}
        """
        if not network_id:
            raise HTTPException(status_code=400, detail="network_id is required")
        
        async with recorder.pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM proxy.events "
                "WHERE network_id = $1 AND status = $2 AND src_peer != $3",
                network_id, status, exclude_sender
            )
        return {"count": count or 0, "network_id": network_id}
    
    @app.post("/api/message")
    async def sendMessage(body: Message):
        try:
            response = await registry.send_message(body)
            return response.to_json()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.websocket("/api/ws/{network_id}")
    async def live(ws: WebSocket, network_id: str):
        await ws.accept()
        queue = hub.subscribe(network_id)

        async def watch_disconnect():
            try:
                while True:
                    await ws.receive_text()
            except WebSocketDisconnect:
                pass

        watcher = asyncio.create_task(watch_disconnect())
        try:
            while not watcher.done():
                getter = asyncio.create_task(queue.get())
                await asyncio.wait({getter, watcher}, return_when=asyncio.FIRST_COMPLETED)
                if not getter.done():
                    getter.cancel()
                    break
                await ws.send_json(getter.result())
        except Exception:
            pass
        finally:
            watcher.cancel()
            hub.unsubscribe(network_id, queue)
    return app
