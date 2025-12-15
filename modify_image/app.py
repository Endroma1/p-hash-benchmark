from fastapi import FastAPI
from . import router

app = FastAPI(title="Image Modifier")

app.include_router(router.router)
