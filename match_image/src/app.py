from fastapi import FastAPI
from . import router

app = FastAPI(title="Hash Matcher")

app.include_router(router.router)



