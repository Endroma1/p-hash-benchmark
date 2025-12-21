from fastapi import APIRouter
from .lib import run_pipeline , run_matching
import asyncio

router = APIRouter()

@router.post("/admin/start/all")
async def start_all_components():
    """
    starts load, modify, and hash images components
    """
    asyncio.create_task(run_pipeline())
    return {"state": "started"}

@router.post("/admin/start/match")
async def start_matching():
    asyncio.create_task(run_matching())
    return {"state": "started"}

@router.post("/admin/modifications/get")
async def get_modifications():
    asyncio.create_task()
