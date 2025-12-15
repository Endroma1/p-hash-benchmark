from fastapi import FastAPI
from . import router

app = FastAPI(title="Image Hasher")

app.include_router(router)


