import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DATABASE_PATH", db_path)
    return db_path


@pytest.fixture
def client(tmp_db):
    from src.main import app
    with TestClient(app) as c:
        yield c
