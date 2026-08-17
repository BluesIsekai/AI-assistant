from .database import (
    add_memory,
    delete_memory,
    get_memory,
    list_memories,
    store_embedding,
    update_memory,
)
from .embeddings import embed
from .retrieval import search
from queue import Queue
from threading import Thread


class MemoryManager:
    def add(
        self,
        content: str,
        memory_type: str,
        category: str | None = None,
        importance: float = 0.5,
        confidence: float = 0.5,
        source: str = "conversation",
    ) -> int:
        memory_id = add_memory(
            content=content,
            memory_type=memory_type,
            category=category,
            importance=importance,
            confidence=confidence,
            source=source,
        )

        try:
            embedding = embed(content)
            store_embedding(memory_id, embedding)
        except Exception:
            delete_memory(memory_id)
            raise

        return memory_id

    def get(self, memory_id: int):
        return get_memory(memory_id)

    def search(
        self,
        query: str,
        limit: int = 5,
        min_relevance: float = 0.45,
        memory_type: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        return search(
            query=query,
            limit=limit,
            min_relevance=min_relevance,
            memory_type=memory_type,
            category=category,
        )

    def update(
        self,
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
        updated = update_memory(
            memory_id,
            content=content,
            memory_type=memory_type,
            category=category,
            importance=importance,
            confidence=confidence,
            source=source,
            status=status,
        )

        if not updated:
            return False

        if content is not None:
            store_embedding(memory_id, embed(content))

        return True

    def delete(self, memory_id: int) -> bool:
        return delete_memory(memory_id)

    def list(
        self,
        *,
        memory_type: str | None = None,
        category: str | None = None,
        status: str = "active",
    ):
        return list_memories(
            memory_type=memory_type,
            category=category,
            status=status,
        )


memory = MemoryManager()