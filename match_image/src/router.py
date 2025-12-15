from dataclasses import dataclass
from re import Match
from fastapi import APIRouter
from pydantic import BaseModel
from . import lib
from enum import Enum

import asyncio

class MatchState(str, Enum):
    DONE = "done"
    IN_PROGRESS = "in progress"
    FAILED = "failed"

class MatchStatus(BaseModel):
    state: MatchState
    processed: int


router = APIRouter()

state =  MatchStatus(state=MatchState.IN_PROGRESS, processed=0)

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

        except Exception:
            state.state = MatchState.FAILED
            return

        state.state = MatchState.DONE

    loop = asyncio.get_event_loop()
    match_task = loop.create_task(run_match())
    return {"state": state}

@router.post("/match/status")
async def match_status():
    global state

    return {"state": state}


@router.get("/match/health")
def health():
    return {"status": "ok"}
