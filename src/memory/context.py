from .manager import memory


def build_memory_context(
    query: str,
    limit: int = 5,
    min_similarity: float = 0.6,
) -> str:
    memories = memory.search(
        query=query,
        limit=limit,
        min_similarity=min_similarity,
    )

    if not memories:
        return ""

    lines = [
        "Relevant memories about the user:",
        "Use these memories when relevant, but do not mention the memory system itself.",
    ]

    for item in memories:
        lines.append(f"- {item['content']}")

    return "\n".join(lines)