from .deduplication import resolve_memory
from .manager import memory
from .extraction import extract_memories


def process_conversation(
    user_message: str,
    assistant_response: str,
    llm,
) -> list[int]:
    candidates = extract_memories(
        user_message,
        assistant_response,
        llm,
    )

    created_ids = []

    for candidate in candidates:
        existing = memory.search(
            candidate["content"],
            limit=5,
            min_similarity=0.65,
        )

        decision = resolve_memory(
            candidate,
            existing,
            llm,
        )

        if decision["decision"] == "new":
            memory_id = memory.add(
                content=candidate["content"],
                memory_type=candidate["memory_type"],
                category=candidate.get("category"),
                importance=candidate.get("importance", 0.5),
                confidence=candidate.get("confidence", 0.5),
                source="conversation",
            )

            created_ids.append(memory_id)

        elif decision["decision"] == "duplicate":
            continue

        elif decision["decision"] == "conflict":
            target_id = decision["target_id"]

            memory.update(
                target_id,
                content=candidate["content"],
                memory_type=candidate["memory_type"],
                category=candidate.get("category"),
                importance=candidate.get("importance", 0.5),
                confidence=candidate.get("confidence", 0.5),
                source="conversation",
            )

    return created_ids