import fastapi
from .router import router
app = fastapi.FastAPI(title="P-Hash Orchestrator")

app.include_router(router)
