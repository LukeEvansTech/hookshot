import hashlib
import secrets
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.config import settings
from src.database import init_db
from src.routers.hooks import router as hooks_router
from src.routers.endpoints import router as endpoints_router
from src.routers.ui import router as ui_router

OPEN_PATHS = ("/hook/", "/health", "/login")


def _session_token() -> str:
    return hashlib.sha256(f"hookshot:{settings.admin_password}".encode()).hexdigest()[:32]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with init_db(settings.database_path) as db:
        app.state.db = db
        yield


app = FastAPI(title="hookshot", description="Generic webhook receiver and notification forwarder", lifespan=lifespan)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not settings.admin_password:
        return await call_next(request)

    path = request.url.path
    if any(path.startswith(p) for p in OPEN_PATHS):
        return await call_next(request)

    session = request.cookies.get("hookshot_session")
    if session and secrets.compare_digest(session, _session_token()):
        return await call_next(request)

    return RedirectResponse(url=f"/login?next={path}", status_code=302)


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>hookshot — Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-gray-900 border border-gray-800 rounded-lg p-8 w-full max-w-sm">
        <h1 class="text-xl font-bold text-blue-400 mb-6 text-center">hookshot</h1>
        {error}
        <form method="post" action="/login">
            <input type="hidden" name="next" value="{next}">
            <div class="mb-4">
                <label class="block text-sm text-gray-400 mb-1">Password</label>
                <input name="password" type="password" required autofocus
                    class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            </div>
            <button type="submit"
                class="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded text-sm">
                Log in
            </button>
        </form>
    </div>
</body>
</html>"""


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    return HTMLResponse(LOGIN_PAGE.format(error="", next=next))


@app.post("/login")
async def login_submit(password: str = Form(...), next: str = Form("/")):
    if secrets.compare_digest(password, settings.admin_password):
        response = RedirectResponse(url=next, status_code=302)
        response.set_cookie(
            key="hookshot_session",
            value=_session_token(),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 7 days
        )
        return response
    return HTMLResponse(
        LOGIN_PAGE.format(
            error='<div class="mb-4 text-sm text-red-400 text-center">Invalid password</div>',
            next=next,
        ),
        status_code=401,
    )


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("hookshot_session")
    return response


app.include_router(hooks_router)
app.include_router(endpoints_router)
app.include_router(ui_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
