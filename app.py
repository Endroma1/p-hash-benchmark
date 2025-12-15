from fastapi import FastAPI

from asyncio import Queue
from load_image.router import router as load_router
from modify_image.router import router as mod_router
from hash_image.router import router as hash_router
from match_image.router import router as match_router

app = FastAPI(title="P-Hash Benchmark")

app.include_router(load_router)
app.include_router(mod_router)
app.include_router(hash_router)
app.include_router(match_router)

app.get("/")
async def root():
    return {"message": "P-Hash Benchmark"}

class Pipeline:
    def __init__(self) -> None:
        self.load_q = Queue
        self.mod_q = Queue()
        self.hash_q = Queue()

