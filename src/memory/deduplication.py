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

Choose exactly ONE decision:

1. "new"
Use "new" when the candidate contains information that is not already
represented by the existing memories.

2. "duplicate"
Use "duplicate" when the candidate expresses essentially the same
information as an existing memory.

3. "conflict"
Use "conflict" ONLY when the candidate directly contradicts an
existing memory.

IMPORTANT:
- If the decision is "duplicate", target_id MUST be the ID of the
  existing memory that is a duplicate.
- If the decision is "conflict", target_id MUST be the ID of the
  existing memory that is contradicted.
- NEVER return "duplicate" or "conflict" with target_id set to null.
- If you are unsure whether something is a conflict, use "new".
- Do not invent an ID.
- target_id must be one of the existing memory IDs listed above.
- For "new", target_id MUST be null.

Examples:

Existing:
ID 10: The user has a cat named Simba.

Candidate:
The user has a cat named Simba.

Output:
{{"decision":"duplicate","target_id":10,"reason":"Same information."}}

Existing:
ID 10: The user has a cat named Simba.

Candidate:
The user's cat is named Luna.

Output:
{{"decision":"conflict","target_id":10,"reason":"The cat's name contradicts the existing memory."}}

Existing:
ID 10: The user has a cat named Simba.

Candidate:
The user has an RTX 4060 laptop.

Output:
{{"decision":"new","target_id":null,"reason":"Different information."}}

Return ONLY valid JSON.

Required format:
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

    valid_ids = {memory["id"] for memory in existing_memories}

    if decision == "new":
        target_id = None

    else:
        if target_id is None:
            raise ValueError(
                f"Memory decision '{decision}' requires target_id."
            )

        if target_id not in valid_ids:
            raise ValueError(
                f"Memory decision '{decision}' returned invalid "
                f"target_id: {target_id}"
            )

    return {
        "decision": decision,
        "target_id": target_id,
        "reason": result.get("reason", ""),
    }