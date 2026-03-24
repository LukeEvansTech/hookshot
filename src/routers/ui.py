from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database import get_endpoint, list_endpoints
from src.services.activity import get_activity, get_activity_count

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = request.app.state.db
    endpoints = await list_endpoints(db)
    recent = await get_activity(db, limit=10)
    total = await get_activity_count(db)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "endpoint_count": len(endpoints),
        "total_activity": total,
        "last_received": recent[0]["received_at"][:19] if recent else None,
        "recent_entries": recent,
    })


@router.get("/ui/endpoints", response_class=HTMLResponse)
async def endpoints_page(request: Request):
    db = request.app.state.db
    endpoints = await list_endpoints(db)
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse("endpoints.html", {
        "request": request,
        "endpoints": endpoints,
        "base_url": base_url,
    })


@router.get("/ui/endpoints/{endpoint_id}", response_class=HTMLResponse)
async def endpoint_detail_page(endpoint_id: str, request: Request):
    db = request.app.state.db
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        return HTMLResponse(content="Not found", status_code=404)
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse("endpoint_detail.html", {
        "request": request,
        "endpoint": endpoint,
        "base_url": base_url,
    })


@router.get("/ui/activity", response_class=HTMLResponse)
async def activity_page(request: Request):
    db = request.app.state.db
    endpoint_id = request.query_params.get("endpoint_id")
    status = request.query_params.get("status")
    entries = await get_activity(db, endpoint_id=endpoint_id, status=status, limit=100)
    return templates.TemplateResponse("activity.html", {
        "request": request,
        "entries": entries,
    })
