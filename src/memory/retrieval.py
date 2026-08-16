import math
import re

from .database import get_connection, VECTOR_DIMENSION
from .embeddings import embed
import sqlite_vec


STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were",
    "do", "does", "did", "what", "who", "where", "when",
    "why", "how", "which", "my", "me", "i", "you", "your",
    "of", "to", "for", "in", "on", "at", "and", "or",
    "about", "tell", "can", "could", "would", "should",
    "have", "has", "had"
}


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


def meaningful_tokens(text: str) -> set[str]:
    return tokenize(text) - STOP_WORDS


def normalize_token(token: str) -> str:
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]

    return token


def normalized_tokens(text: str) -> set[str]:
    return {
        normalize_token(token)
        for token in meaningful_tokens(text)
    }


def calculate_idf(
    connection,
    tokens: set[str],
) -> dict[str, float]:
    if not tokens:
        return {}

    memories = connection.execute(
        """
        SELECT content
        FROM memories
        WHERE status = 'active'
        """
    ).fetchall()

    total_memories = len(memories)

    if total_memories == 0:
        return {}

    document_frequency = {
        token: 0
        for token in tokens
    }

    for memory in memories:
        memory_tokens = normalized_tokens(memory["content"])

        for token in tokens & memory_tokens:
            document_frequency[token] += 1

    return {
        token: math.log(
            (total_memories + 1)
            / (frequency + 1)
        ) + 1
        for token, frequency in document_frequency.items()
    }


def keyword_overlap(
    query_tokens: set[str],
    content_tokens: set[str],
    idf: dict[str, float],
) -> float:
    if not query_tokens:
        return 0.0

    matched_tokens = query_tokens & content_tokens

    if not matched_tokens:
        return 0.0

    total_weight = sum(
        idf.get(token, 1.0)
        for token in query_tokens
    )

    matched_weight = sum(
        idf.get(token, 1.0)
        for token in matched_tokens
    )

    return matched_weight / total_weight


def category_relevance(
    query_tokens: set[str],
    category: str | None,
) -> float:
    if not category:
        return 0.0

    category_tokens = normalized_tokens(
        category.replace("_", " ")
    )

    if not category_tokens:
        return 0.0

    overlap = query_tokens & category_tokens

    if not overlap:
        return 0.0

    return len(overlap) / len(category_tokens)


def phrase_overlap(
    query: str,
    content: str,
) -> float:
    query_tokens = normalized_tokens(query)

    if not query_tokens:
        return 0.0

    content_tokens = normalized_tokens(content)

    return len(query_tokens & content_tokens) / len(query_tokens)


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

    query_tokens = normalized_tokens(query)

    candidate_limit = max(10, limit * 3)

    with get_connection() as connection:
        idf = calculate_idf(
            connection,
            query_tokens,
        )

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

            content_tokens = normalized_tokens(
                memory["content"]
            )

            lexical_score = keyword_overlap(
                query_tokens,
                content_tokens,
                idf,
            )

            category_score = category_relevance(
                query_tokens,
                memory["category"],
            )

            phrase_score = phrase_overlap(
                query,
                memory["content"],
            )

            relevance_score = (
                similarity * 0.70
                + lexical_score * 0.15
                + category_score * 0.10
                + phrase_score * 0.05
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
                    "_relevance_score": relevance_score,
                }
            )

        candidates.sort(
            key=lambda memory: memory["_relevance_score"],
            reverse=True,
        )

        return candidates[:limit]