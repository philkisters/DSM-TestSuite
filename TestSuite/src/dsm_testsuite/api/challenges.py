from fastapi import APIRouter, Request
from .helper import get_engine
from ..db import list_challenges, get_challenge_results_for_group, group_challenge_stats
from ..schemas import Challenge, ChallengeResults, GroupChallengeStatsResults

router = APIRouter(prefix="/challenges", tags=["challenges"])

@router.get("", response_model=list[Challenge])
def get_challenges(request: Request):
    return list_challenges(get_engine(request))

@router.get("/{challenge_id}/{group_id}/results", response_model=ChallengeResults)
def get_challenge_results(challenge_id: int, group_id: int, request: Request):
    return get_challenge_results_for_group(get_engine(request), challenge_id, group_id)

@router.get("/{group_id}/stats", response_model=GroupChallengeStatsResults)
def get_group_stats(group_id: int, request: Request):
    return group_challenge_stats(get_engine(request), group_id)