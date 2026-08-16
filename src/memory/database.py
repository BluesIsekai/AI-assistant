from pathlib import Path
import sqlite3

import sqlite_vec


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "memory.db"

VECTOR_DIMENSION = 1024


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    connection.enable_load_extension(False)

    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                category TEXT,
                importance REAL NOT NULL DEFAULT 0.5,
                confidence REAL NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT 'conversation',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_accessed TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors
            USING vec0(
                memory_id INTEGER PRIMARY KEY,
                embedding float[{VECTOR_DIMENSION}] distance_metric=cosine
            )
            """
        )

        connection.commit()


def add_memory(
    content: str,
    memory_type: str,
    category: str | None = None,
    importance: float = 0.5,
    confidence: float = 0.5,
    source: str = "conversation",
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO memories (
                content,
                memory_type,
                category,
                importance,
                confidence,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                content,
                memory_type,
                category,
                importance,
                confidence,
                source,
            ),
        )

        connection.commit()

        return cursor.lastrowid


def get_memory(memory_id: int) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()


def update_memory(
    memory_id: int,
    *,
    content: str | None = None,
    memory_type: str | None = None,
    category: str | None = None,
    importance: float | None = None,
    confidence: float | None = None,
    source: str | None = None,
    status: str | None = None,
) -> bool:
    fields = []
    values = []

    updates = {
        "content": content,
        "memory_type": memory_type,
        "category": category,
        "importance": importance,
        "confidence": confidence,
        "source": source,
        "status": status,
    }

    for field, value in updates.items():
        if value is not None:
            fields.append(f"{field} = ?")
            values.append(value)

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")

    values.append(memory_id)

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE memories
            SET {", ".join(fields)}
            WHERE id = ?
            """,
            values,
        )

        connection.commit()

        return cursor.rowcount > 0


def delete_memory(memory_id: int) -> bool:
    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM memory_vectors
            WHERE memory_id = ?
            """,
            (memory_id,),
        )

        cursor = connection.execute(
            """
            DELETE FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )

        connection.commit()

        return cursor.rowcount > 0


def list_memories(
    *,
    memory_type: str | None = None,
    category: str | None = None,
    status: str = "active",
) -> list[sqlite3.Row]:
    conditions = ["status = ?"]
    values = [status]

    if memory_type is not None:
        conditions.append("memory_type = ?")
        values.append(memory_type)

    if category is not None:
        conditions.append("category = ?")
        values.append(category)

    with get_connection() as connection:
        return connection.execute(
            f"""
            SELECT *
            FROM memories
            WHERE {" AND ".join(conditions)}
            ORDER BY importance DESC, created_at DESC
            """,
            values,
        ).fetchall()


def store_embedding(memory_id: int, embedding: list[float]) -> None:
    if len(embedding) != VECTOR_DIMENSION:
        raise ValueError(
            f"Expected {VECTOR_DIMENSION}-dimensional embedding, "
            f"got {len(embedding)}"
        )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO memory_vectors (
                memory_id,
                embedding
            )
            VALUES (?, ?)
            """,
            (
                memory_id,
                sqlite_vec.serialize_float32(embedding),
            ),
        )

        connection.commit()