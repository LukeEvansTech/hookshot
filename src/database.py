import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS endpoints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parser_type TEXT NOT NULL DEFAULT 'generic',
    parser_name TEXT NOT NULL DEFAULT '',
    apprise_tag TEXT NOT NULL DEFAULT '',
    secret TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint_id TEXT NOT NULL,
    received_at TEXT NOT NULL,
    source_ip TEXT NOT NULL DEFAULT '',
    payload TEXT NOT NULL DEFAULT '',
    notification_title TEXT NOT NULL DEFAULT '',
    notification_body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'success',
    apprise_response TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (endpoint_id) REFERENCES endpoints(id) ON DELETE CASCADE
);
"""


def _row_to_dict(row, description):
    return {description[i][0]: row[i] for i in range(len(row))}


@asynccontextmanager
async def init_db(db_path: str):
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.executescript(SCHEMA)
    await db.commit()
    try:
        yield db
    finally:
        await db.close()


async def create_endpoint(db: aiosqlite.Connection, *, name: str, parser_type: str, parser_name: str, apprise_tag: str, secret: str | None = None) -> dict:
    endpoint_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO endpoints (id, name, parser_type, parser_name, apprise_tag, secret, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
        (endpoint_id, name, parser_type, parser_name, apprise_tag, secret, now, now),
    )
    await db.commit()
    return await get_endpoint(db, endpoint_id)


async def get_endpoint(db: aiosqlite.Connection, endpoint_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM endpoints WHERE id = ?", (endpoint_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    result = _row_to_dict(row, cursor.description)
    result["enabled"] = bool(result["enabled"])
    return result


async def list_endpoints(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT * FROM endpoints ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    results = [_row_to_dict(row, cursor.description) for row in rows]
    for r in results:
        r["enabled"] = bool(r["enabled"])
    return results


async def update_endpoint(db: aiosqlite.Connection, endpoint_id: str, **kwargs) -> dict | None:
    allowed = {"name", "parser_type", "parser_name", "apprise_tag", "secret", "enabled"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return await get_endpoint(db, endpoint_id)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [endpoint_id]
    await db.execute(f"UPDATE endpoints SET {set_clause} WHERE id = ?", values)
    await db.commit()
    return await get_endpoint(db, endpoint_id)


async def delete_endpoint(db: aiosqlite.Connection, endpoint_id: str) -> None:
    await db.execute("DELETE FROM endpoints WHERE id = ?", (endpoint_id,))
    await db.commit()
