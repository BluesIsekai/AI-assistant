from .database import get_connection, VECTOR_DIMENSION
from .embeddings import embed
import sqlite_vec


def search(
    query: str,
    limit: int = 5,
    min_similarity: float = 0.0,
    memory_type: str | None = None,
    category: str | None = None,
) -> list[dict]:
    query_embedding = embed(query)

    if len(query_embedding) != VECTOR_DIMENSION:
        raise ValueError(
            f"Expected {VECTOR_DIMENSION}-dimensional embedding, "
            f"got {len(query_embedding)}"
        )

    with get_connection() as connection:
        vector_rows = connection.execute(
            """
            SELECT memory_id, distance
            FROM memory_vectors
            WHERE embedding MATCH ?
              AND k = ?
            ORDER BY distance
            """,
            (
                sqlite_vec.serialize_float32(query_embedding),
                limit,
            ),
        ).fetchall()

        results = []

        for vector_row in vector_rows:
            similarity = 1.0 - vector_row["distance"]

            if similarity < min_similarity:
                continue

            conditions = [
                "id = ?",
                "status = 'active'",
            ]
            values = [vector_row["memory_id"]]

            if memory_type is not None:
                conditions.append("memory_type = ?")
                values.append(memory_type)

            if category is not None:
                conditions.append("category = ?")
                values.append(category)

            memory = connection.execute(
                f"""
                SELECT *
                FROM memories
                WHERE {" AND ".join(conditions)}
                """,
                values,
            ).fetchone()

            if memory is None:
                continue

            results.append(
                {
                    "id": memory["id"],
                    "content": memory["content"],
                    "memory_type": memory["memory_type"],
                    "category": memory["category"],
                    "importance": memory["importance"],
                    "confidence": memory["confidence"],
                    "source": memory["source"],
                    "status": memory["status"],
                    "created_at": memory["created_at"],
                    "updated_at": memory["updated_at"],
                    "last_accessed": memory["last_accessed"],
                    "similarity": similarity,
                }
            )

        return results