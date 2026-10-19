import asyncio
import logging
import os

import uvicorn
from dsm_protocol import MAX_LINE_BYTES

from .api import create_app
from .hub import Hub
from .liveness import liveness_loop
from .recorder import Recorder
from .register import make_register_handler
from .registry import Registry
from .relay import Stats, make_relay_handler

log = logging.getLogger("proxy")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    hub = Hub()
    recorder = Recorder(os.environ["DATABASE_URL"], on_event=hub.publish)
    await recorder.start()
    registry, stats = Registry(), Stats()
    host = "0.0.0.0"

    relay = await asyncio.start_server(make_relay_handler(registry, recorder, stats), host,
                                       int(os.getenv("PROXY_PORT", "9000")), limit=MAX_LINE_BYTES)
    reg = await asyncio.start_server(make_register_handler(registry, hub, recorder), host,
                                     int(os.getenv("REGISTER_PORT", "9002")))
    api = uvicorn.Server(uvicorn.Config(create_app(registry, hub, recorder, stats), host=host,
                                        port=int(os.getenv("ADMIN_PORT", "9001")), log_level="info"))
    log.info("proxy listening")
    liveness = asyncio.create_task(liveness_loop(registry, hub, recorder))
    try:
        async with relay, reg:
            await api.serve()
    finally:
        liveness.cancel()
        await recorder.stop()
