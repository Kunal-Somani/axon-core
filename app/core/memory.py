import aiosqlite
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "axon_memory.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                route_taken TEXT,
                sources TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        await db.commit()

async def save_message(session_id: str, role: str, content: str, route_taken: str = None, sources: list = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (session_id, role, content, route_taken, sources, timestamp) VALUES (?,?,?,?,?,?)",
            (session_id, role, content, route_taken, json.dumps(sources or []), datetime.utcnow().isoformat())
        )
        await db.commit()

async def get_history(session_id: str, limit: int = 12) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        )
        rows = await cursor.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

async def get_full_history(session_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content, route_taken, sources, timestamp FROM messages WHERE session_id=? ORDER BY id ASC",
            (session_id,)
        )
        rows = await cursor.fetchall()
    return [{"role": r[0], "content": r[1], "route_taken": r[2], "sources": json.loads(r[3] or "[]"), "timestamp": r[4]} for r in rows]
