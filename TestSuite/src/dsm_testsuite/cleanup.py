"""Stop peers left behind on the orchestrators by runs of a previous (crashed) process."""
import logging

import httpx

from .clients import OrchestratorClient, ProxyClient
from .config import settings
from .db import StaleRun

logger = logging.getLogger(__name__)


async def kill_stale_peers(stale_runs: list[StaleRun]) -> None:
    async with httpx.AsyncClient(timeout=settings.http_timeout) as http:
        for run in stale_runs:
            if not run.network_id or not run.vm_ip:
                continue
            peers = set(run.peers)
            try:
                registered = await ProxyClient(settings.proxy_admin_url, run.network_id, http).peers()
                peers |= {p["peerId"] for p in registered}
            except Exception:
                logger.warning("Could not list proxy peers of stale run %s", run.run_id, exc_info=True)
            orchestrator = OrchestratorClient(run.vm_ip, run.network_id, http)
            for peer in sorted(peers):
                try:
                    await orchestrator.kill(peer)
                    logger.info("Stopped stale peer %r of run %s", peer, run.run_id)
                except Exception:
                    logger.warning("Could not stop stale peer %r of run %s", peer, run.run_id, exc_info=True)
