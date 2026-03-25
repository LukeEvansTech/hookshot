import base64
import secrets
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response

from src.config import settings
from src.database import init_db
from src.routers.hooks import router as hooks_router
from src.routers.endpoints import router as endpoints_router
from src.routers.ui import router as ui_router

OPEN_PATHS = ("/hook/", "/health")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with init_db(settings.database_path) as db:
        app.state.db = db
        yield


app = FastAPI(title="hookshot", description="Generic webhook receiver and notification forwarder", lifespan=lifespan)


@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    if not settings.admin_password:
        return await call_next(request)

    path = request.url.path
    if any(path.startswith(p) for p in OPEN_PATHS):
        return await call_next(request)

    auth = request.headers.get("authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            _, password = decoded.split(":", 1)
            if secrets.compare_digest(password, settings.admin_password):
                return await call_next(request)
        except Exception:
            pass

    return Response(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="hookshot"'},
        content="Unauthorized",
    )


app.include_router(hooks_router)
app.include_router(endpoints_router)
app.include_router(ui_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
