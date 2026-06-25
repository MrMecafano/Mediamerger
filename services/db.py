import aiosqlite
from config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT NOT NULL,
                file_id     TEXT NOT NULL,
                uploader_id INTEGER NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_document(name: str, description: str, file_id: str, uploader_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO documents (name, description, file_id, uploader_id) VALUES (?, ?, ?, ?)",
            (name, description, file_id, uploader_id),
        )
        await db.commit()


async def search_documents(query: str) -> list[dict]:
    pattern = f"%{query}%"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT name, description, file_id, created_at
            FROM documents
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (pattern, pattern),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def recent_documents(limit: int = 5) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, description, file_id, created_at FROM documents ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
