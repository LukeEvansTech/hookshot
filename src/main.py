from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import settings
from src.database import init_db
from src.routers.hooks import router as hooks_router
from src.routers.endpoints import router as endpoints_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with init_db(settings.database_path) as db:
        app.state.db = db
        yield


app = FastAPI(title="hookshot", description="Generic webhook receiver and notification forwarder", lifespan=lifespan)

app.include_router(hooks_router)
app.include_router(endpoints_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
