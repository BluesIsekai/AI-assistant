from .manager import memory


def build_memory_context(
    query: str,
    limit: int = 5,
    min_relevance: float = 0.40,
) -> str:
    memories = memory.search(
        query=query,
        limit=10,
    )

    memories = [
        item
        for item in memories
        if item.get("_relevance_score", 0.0) >= min_relevance
    ]

    if not memories:
        return ""

    lines = [
        "Relevant memories about the user:",
        "Use these memories when relevant, but do not mention the memory system itself.",
    ]

    for item in memories:
        lines.append(f"- {item['content']}")

    return "\n".join(lines)