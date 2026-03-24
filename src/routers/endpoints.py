from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from src.database import create_endpoint, get_endpoint, list_endpoints, update_endpoint, delete_endpoint

router = APIRouter(prefix="/endpoints")


class EndpointCreate(BaseModel):
    name: str
    parser_type: str = "generic"
    parser_name: str = ""
    apprise_tag: str = ""
    secret: str | None = None


class EndpointUpdate(BaseModel):
    name: str | None = None
    parser_type: str | None = None
    parser_name: str | None = None
    apprise_tag: str | None = None
    secret: str | None = None
    enabled: bool | None = None


@router.get("")
async def list_all(request: Request):
    db = request.app.state.db
    return await list_endpoints(db)


@router.post("", status_code=201)
async def create(request: Request, body: EndpointCreate):
    db = request.app.state.db
    return await create_endpoint(db, name=body.name, parser_type=body.parser_type, parser_name=body.parser_name, apprise_tag=body.apprise_tag, secret=body.secret)


@router.get("/{endpoint_id}")
async def get_one(endpoint_id: str, request: Request):
    db = request.app.state.db
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        return Response(status_code=404, content="Not found")
    return endpoint


@router.put("/{endpoint_id}")
async def update(endpoint_id: str, request: Request, body: EndpointUpdate):
    db = request.app.state.db
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        return Response(status_code=404, content="Not found")
    return await update_endpoint(db, endpoint_id, **body.model_dump(exclude_none=True))


@router.delete("/{endpoint_id}", status_code=204)
async def delete(endpoint_id: str, request: Request):
    db = request.app.state.db
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        return Response(status_code=404, content="Not found")
    await delete_endpoint(db, endpoint_id)
