import pytest
from fastapi.testclient import TestClient
from src.database import init_db


@pytest.fixture
async def db_and_client(tmp_db):
    async with init_db(tmp_db) as db:
        from src.main import app
        app.state.db = db
        with TestClient(app) as client:
            yield db, client


@pytest.mark.asyncio
async def test_create_endpoint(db_and_client):
    _, client = db_and_client
    response = client.post("/endpoints", json={"name": "My Hook", "parser_type": "generic", "apprise_tag": "all"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Hook"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_endpoints(db_and_client):
    _, client = db_and_client
    client.post("/endpoints", json={"name": "Hook 1", "parser_type": "generic", "apprise_tag": "all"})
    client.post("/endpoints", json={"name": "Hook 2", "parser_type": "generic", "apprise_tag": "dev"})
    response = client.get("/endpoints")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_endpoint(db_and_client):
    _, client = db_and_client
    create_resp = client.post("/endpoints", json={"name": "Detail", "parser_type": "generic", "apprise_tag": "all"})
    endpoint_id = create_resp.json()["id"]
    response = client.get(f"/endpoints/{endpoint_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Detail"


@pytest.mark.asyncio
async def test_update_endpoint(db_and_client):
    _, client = db_and_client
    create_resp = client.post("/endpoints", json={"name": "Old", "parser_type": "generic", "apprise_tag": "all"})
    endpoint_id = create_resp.json()["id"]
    response = client.put(f"/endpoints/{endpoint_id}", json={"name": "New"})
    assert response.status_code == 200
    assert response.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_endpoint(db_and_client):
    _, client = db_and_client
    create_resp = client.post("/endpoints", json={"name": "Delete Me", "parser_type": "generic", "apprise_tag": "all"})
    endpoint_id = create_resp.json()["id"]
    response = client.delete(f"/endpoints/{endpoint_id}")
    assert response.status_code == 204
    get_resp = client.get(f"/endpoints/{endpoint_id}")
    assert get_resp.status_code == 404
