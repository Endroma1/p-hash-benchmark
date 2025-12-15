from fastapi import FastAPI
from . import router

app = FastAPI(title="Image Loader")

app.include_router(router.router)

