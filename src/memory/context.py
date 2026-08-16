from .manager import memory


def build_memory_context(
    query: str,
    limit: int = 5,
) -> str:
    memories = memory.search(
        query=query,
        limit=limit,
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