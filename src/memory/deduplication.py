import json


def resolve_memory(
    candidate: dict,
    existing_memories: list[dict],
    llm,
) -> dict:
    if not existing_memories:
        return {
            "decision": "new",
            "target_id": None,
            "reason": "No existing memories were found.",
        }

    memories_text = "\n".join(
        f"ID {memory['id']}: {memory['content']}"
        for memory in existing_memories
    )

    prompt = f"""
You are a memory management system.

Determine how a newly extracted memory relates to existing memories.

Candidate memory:
{candidate["content"]}

Candidate type:
{candidate["memory_type"]}

Candidate category:
{candidate.get("category")}

Existing memories:
{memories_text}

Choose exactly one decision:

- "new": The candidate contains information that should be stored as a new memory.
- "duplicate": The candidate expresses essentially the same information as an existing memory.
- "conflict": The candidate contradicts an existing memory.

If the decision is "duplicate" or "conflict", return the ID of the most relevant existing memory.

Return ONLY valid JSON in this format:

{{
  "decision": "new",
  "target_id": null,
  "reason": "brief explanation"
}}

Do not include markdown.
"""

    response = llm(prompt)

    try:
        result = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Memory LLM returned invalid JSON: {response}"
        ) from exc

    decision = result.get("decision")
    target_id = result.get("target_id")

    if decision not in {"new", "duplicate", "conflict"}:
        raise ValueError(f"Invalid memory decision: {decision}")

    if decision == "new":
        target_id = None
    elif target_id is None:
        raise ValueError(
            f"Memory decision '{decision}' requires target_id."
        )

    return {
        "decision": decision,
        "target_id": target_id,
        "reason": result.get("reason", ""),
    }