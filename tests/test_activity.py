import pytest
from src.database import init_db, create_endpoint
from src.services.activity import log_activity, get_activity, prune_activity


@pytest.fixture
async def db(tmp_db):
    async with init_db(tmp_db) as db:
        yield db


@pytest.mark.asyncio
async def test_log_and_get_activity(db):
    endpoint = await create_endpoint(db, name="Test", parser_type="generic", parser_name="", apprise_tag="all")
    await log_activity(db, endpoint_id=endpoint["id"], source_ip="1.2.3.4", payload='{"test": true}', notification_title="Title", notification_body="Body", status="success", apprise_response="ok")
    entries = await get_activity(db)
    assert len(entries) == 1
    assert entries[0]["source_ip"] == "1.2.3.4"
    assert entries[0]["status"] == "success"


@pytest.mark.asyncio
async def test_prune_activity(db):
    endpoint = await create_endpoint(db, name="Test", parser_type="generic", parser_name="", apprise_tag="all")
    for i in range(15):
        await log_activity(db, endpoint_id=endpoint["id"], source_ip="1.2.3.4", payload="{}", notification_title=f"Title {i}", notification_body="Body", status="success", apprise_response="ok")
    await prune_activity(db, max_entries=10)
    entries = await get_activity(db, limit=100)
    assert len(entries) == 10


@pytest.mark.asyncio
async def test_get_activity_filtered(db):
    ep1 = await create_endpoint(db, name="EP1", parser_type="generic", parser_name="", apprise_tag="all")
    ep2 = await create_endpoint(db, name="EP2", parser_type="generic", parser_name="", apprise_tag="all")
    await log_activity(db, endpoint_id=ep1["id"], source_ip="1.1.1.1", payload="{}", notification_title="A", notification_body="B", status="success", apprise_response="ok")
    await log_activity(db, endpoint_id=ep2["id"], source_ip="2.2.2.2", payload="{}", notification_title="C", notification_body="D", status="failed", apprise_response="err")
    entries = await get_activity(db, endpoint_id=ep1["id"])
    assert len(entries) == 1
    assert entries[0]["notification_title"] == "A"
