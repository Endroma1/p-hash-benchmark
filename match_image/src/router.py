from dataclasses import dataclass
from re import Match
from fastapi import APIRouter
from pydantic import BaseModel
from . import lib
from enum import Enum
from .lib import logger

import asyncio

class MatchState(str, Enum):
    DONE = "done"
    IN_PROGRESS = "in progress"
    FAILED = "failed"
    STOPPED = "stopped"

class MatchStatus(BaseModel):
    state: MatchState
    processed: int


router = APIRouter()

state =  MatchStatus(state=MatchState.STOPPED, processed=0)

@router.post("/match/start")
async def match_hashes():
    global state

    if state.state == MatchState.IN_PROGRESS:
        return {"state": state}

    async def run_match():
        try:
            state.state = MatchState.IN_PROGRESS
            loader = lib.Matcher
            async for _ in loader.start_iter():
                state.processed += 1

        except Exception as e:
            state.state = MatchState.FAILED
            logger.error(e)
            return

        state.state = MatchState.DONE

    asyncio.create_task(run_match())
    return {"state": state}

@router.post("/match/status")
async def match_status():
    global state

    return {"state": state}


@router.get("/match/health")
def health():
    return {"status": "ok"}
