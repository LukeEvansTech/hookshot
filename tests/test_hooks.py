import hashlib
import pytest
from fastapi.testclient import TestClient
from src.database import create_endpoint


@pytest.fixture
async def db_and_client(tmp_db):
    from src.main import app
    with TestClient(app) as client:
        yield app.state.db, client


@pytest.mark.asyncio
async def test_webhook_generic(db_and_client):
    db, client = db_and_client
    endpoint = await create_endpoint(db, name="Generic Test", parser_type="generic", parser_name="", apprise_tag="all")
    response = client.post(f"/hook/{endpoint['id']}", json={"event": "test", "value": 42})
    assert response.status_code == 200
    assert response.json()["status"] == "received"


@pytest.mark.asyncio
async def test_webhook_unknown_endpoint(db_and_client):
    _, client = db_and_client
    response = client.post("/hook/nonexistent-id", json={"test": True})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_webhook_disabled_endpoint(db_and_client):
    db, client = db_and_client
    endpoint = await create_endpoint(db, name="Disabled", parser_type="generic", parser_name="", apprise_tag="all")
    from src.database import update_endpoint
    await update_endpoint(db, endpoint["id"], enabled=False)
    response = client.post(f"/hook/{endpoint['id']}", json={"test": True})
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"


@pytest.mark.asyncio
async def test_ebay_verification_challenge(db_and_client):
    db, client = db_and_client
    secret = "my-ebay-token"
    endpoint = await create_endpoint(db, name="eBay", parser_type="builtin", parser_name="ebay_deletion", apprise_tag="all", secret=secret)
    challenge = "test-challenge-abc"
    response = client.get(f"/hook/{endpoint['id']}", params={"challenge_code": challenge})
    assert response.status_code == 200
    expected_hash = hashlib.sha256(challenge.encode() + secret.encode()).hexdigest()
    assert response.json()["challengeResponse"] == expected_hash
