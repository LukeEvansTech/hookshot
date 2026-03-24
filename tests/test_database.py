import pytest
from src.database import init_db, create_endpoint, get_endpoint, list_endpoints, update_endpoint, delete_endpoint


@pytest.fixture
async def db(tmp_db):
    async with init_db(tmp_db) as db:
        yield db


@pytest.mark.asyncio
async def test_create_and_get_endpoint(db):
    endpoint = await create_endpoint(db, name="Test Hook", parser_type="generic", parser_name="", apprise_tag="all")
    assert endpoint["name"] == "Test Hook"
    assert endpoint["parser_type"] == "generic"
    assert endpoint["enabled"] is True

    fetched = await get_endpoint(db, endpoint["id"])
    assert fetched["name"] == "Test Hook"


@pytest.mark.asyncio
async def test_list_endpoints(db):
    await create_endpoint(db, name="Hook 1", parser_type="generic", parser_name="", apprise_tag="all")
    await create_endpoint(db, name="Hook 2", parser_type="builtin", parser_name="github", apprise_tag="dev")
    endpoints = await list_endpoints(db)
    assert len(endpoints) == 2


@pytest.mark.asyncio
async def test_update_endpoint(db):
    endpoint = await create_endpoint(db, name="Old Name", parser_type="generic", parser_name="", apprise_tag="all")
    updated = await update_endpoint(db, endpoint["id"], name="New Name")
    assert updated["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_endpoint(db):
    endpoint = await create_endpoint(db, name="To Delete", parser_type="generic", parser_name="", apprise_tag="all")
    await delete_endpoint(db, endpoint["id"])
    fetched = await get_endpoint(db, endpoint["id"])
    assert fetched is None


@pytest.mark.asyncio
async def test_get_nonexistent_endpoint(db):
    fetched = await get_endpoint(db, "nonexistent-id")
    assert fetched is None
