from fastapi import APIRouter
from . import health, groups, runs, challenges

router = APIRouter()
for module in (health, groups, runs, challenges):
    router.include_router(module.router)