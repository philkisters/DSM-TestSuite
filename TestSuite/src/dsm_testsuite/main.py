from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .api import router
from .config import settings
from .runs import RunManager
from .cleanup import kill_stale_peers
from .health_service import HealthService
from .db import fail_stale_runs, make_engine, sync_challenges

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url:
        engine = make_engine(settings.database_url)
        sync_challenges(engine)
        stale = fail_stale_runs(engine)
        await kill_stale_peers(stale)
        app.state.engine = engine
        app.state.run_manager = RunManager(engine)
        app.state.health_service = HealthService(engine)
        await app.state.health_service.start()
    yield
    if getattr(app.state, "health_service", None):
        await app.state.health_service.stop()
    if getattr(app.state, "run_manager", None):
        await app.state.run_manager.shutdown()


app = FastAPI(title="DSM TestSuite", lifespan=lifespan)
app.include_router(router, prefix="/api")


def main() -> None:
    uvicorn.run("dsm_testsuite.main:app", host=settings.host, port=settings.port)
