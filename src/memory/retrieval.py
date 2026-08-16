from .database import get_connection, VECTOR_DIMENSION
from .embeddings import embed
import sqlite_vec
import re


def _tokenize(text: str) -> set[str]:
    stop_words = {
        "the",
        "user",
        "does",
        "have",
        "has",
        "what",
        "which",
        "who",
        "how",
        "why",
        "when",
        "where",
        "their",
        "they",
        "them",
        "this",
        "that",
        "about",
        "with",
        "from",
        "for",
        "and",
        "are",
        "was",
        "were",
        "is",
        "my",
        "your",
        "you",
        "me",
    }

    return {
        word
        for word in re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        if len(word) > 2 and word not in stop_words
    }


def _keyword_overlap(query: str, content: str) -> float:
    query_words = _tokenize(query)
    content_words = _tokenize(content)

    if not query_words:
        return 0.0

    overlap = query_words & content_words
    return len(overlap) / len(query_words)


def _relevance_score(
    similarity: float,
    keyword_overlap: float,
    importance: float,
    confidence: float,
) -> float:
    return (
        similarity * 0.80
        + keyword_overlap * 0.15
        + importance * 0.03
        + confidence * 0.02
    )


def search(
    query: str,
    limit: int = 5,
    min_similarity: float = 0.3,
    memory_type: str | None = None,
    category: str | None = None,
) -> list[dict]:

    query_embedding = embed(query)

    if len(query_embedding) != VECTOR_DIMENSION:
        raise ValueError(
            f"Expected {VECTOR_DIMENSION}-dimensional embedding, "
            f"got {len(query_embedding)}"
        )

    # Retrieve more candidates than we ultimately return.
    candidate_limit = max(limit * 2, 10)

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
                candidate_limit,
            ),
        ).fetchall()

        candidates = []

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

            overlap = _keyword_overlap(
                query,
                memory["content"],
            )

            relevance = _relevance_score(
                similarity=similarity,
                importance=memory["importance"],
                confidence=memory["confidence"],
                keyword_overlap=overlap,
            )

            candidates.append(
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
                    "_relevance_score": relevance,
                }
            )

    candidates.sort(
        key=lambda item: item["_relevance_score"],
        reverse=True,
    )

    return candidates[:limit]