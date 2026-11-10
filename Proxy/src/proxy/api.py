"""REST (status, peers) and WebSocket (live message feed) endpoint."""
import asyncio
import json
import time
from datetime import datetime

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
    
    @app.get("/api/messages")
    async def messages(network_id: str, src_peer: str | None = None, dst_peer: str | None = None,
                       code: int | None = None, status: str | None = "forwarded",
                       since: datetime | None = None, limit: int = 100):
        """Recorded messages of a network, including events still queued for Postgres."""
        limit = min(max(limit, 1), 1000)

        def match(r: dict) -> bool:
            return (r["network_id"] == network_id
                    and (src_peer is None or r["src_peer"] == src_peer)
                    and (dst_peer is None or r["dst_peer"] == dst_peer)
                    and (code is None or r["code"] == code)
                    and (status is None or r["status"] == status)
                    and (since is None or r["ts"] >= since))

        # Snapshot memory before reading the DB so a row mid-flush is never missed.
        pending = [r for r in recorder.pending_events() if match(r)]
        async with recorder.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT ts, network_id, src_peer, dst_peer, code, size, status, delay_ms, content "
                "FROM proxy.events WHERE network_id = $1 "
                "AND ($2::text IS NULL OR src_peer = $2) AND ($3::text IS NULL OR dst_peer = $3) "
                "AND ($4::int IS NULL OR code = $4) AND ($5::text IS NULL OR status = $5) "
                "AND ($6::timestamptz IS NULL OR ts >= $6) ORDER BY ts DESC LIMIT $7",
                network_id, src_peer, dst_peer, code, status, since, limit)
        stored = [{**r, "content": json.loads(r["content"]) if r["content"] else None}
                  for r in map(dict, rows)]
        key = lambda r: (r["ts"], r["src_peer"], r["dst_peer"], r["code"])
        seen = {key(r) for r in stored}  # a row can be in both if it was flushed meanwhile
        merged = sorted(stored + [r for r in pending if key(r) not in seen],
                        key=lambda r: r["ts"], reverse=True)[:limit]
        return [{**r, "ts": r["ts"].isoformat()} for r in merged]

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
