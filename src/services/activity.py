from datetime import datetime, timezone
import aiosqlite


async def log_activity(db: aiosqlite.Connection, *, endpoint_id: str, source_ip: str, payload: str, notification_title: str, notification_body: str, status: str, apprise_response: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO activity (endpoint_id, received_at, source_ip, payload, notification_title, notification_body, status, apprise_response) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (endpoint_id, now, source_ip, payload, notification_title, notification_body, status, apprise_response),
    )
    await db.commit()


async def get_activity(db: aiosqlite.Connection, *, endpoint_id: str | None = None, status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    query = "SELECT a.*, e.name as endpoint_name FROM activity a LEFT JOIN endpoints e ON a.endpoint_id = e.id"
    conditions = []
    params = []
    if endpoint_id:
        conditions.append("a.endpoint_id = ?")
        params.append(endpoint_id)
    if status:
        conditions.append("a.status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.received_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [{cursor.description[i][0]: row[i] for i in range(len(row))} for row in rows]


async def get_activity_count(db: aiosqlite.Connection) -> int:
    cursor = await db.execute("SELECT COUNT(*) FROM activity")
    row = await cursor.fetchone()
    return row[0] if row else 0


async def prune_activity(db: aiosqlite.Connection, max_entries: int = 10000) -> None:
    await db.execute(
        "DELETE FROM activity WHERE id NOT IN (SELECT id FROM activity ORDER BY received_at DESC LIMIT ?)",
        (max_entries,),
    )
    await db.commit()
