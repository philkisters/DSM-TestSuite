from fastapi import APIRouter
from . import health, groups, runs, challenges, orchestrator

router = APIRouter()
for module in (health, groups, runs, challenges, orchestrator):
    router.include_router(module.router)