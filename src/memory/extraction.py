import json
from .llm import LLM


EXTRACTION_PROMPT = """
You are a memory extraction system for a personal AI assistant.

Analyze the conversation and identify information about the USER that is
worth remembering for future conversations.

Only extract durable, useful information.

Good memories include:
- Long-term preferences
- Likes and dislikes
- Important habits
- Stable interests
- Personal goals
- Ongoing projects
- Important facts the user explicitly tells the assistant
- Persistent instructions or preferences

Do NOT extract:
- Temporary situations
- Casual conversation
- One-time events
- Things the assistant said
- Questions without useful user information
- Information that is already obvious from the current conversation
- Sensitive personal information unless explicitly required by the application

Return ONLY valid JSON in this exact structure:

{
  "memories": [
    {
      "content": "A concise statement about the user.",
      "memory_type": "preference",
      "category": "general",
      "importance": 0.0,
      "confidence": 0.0
    }
  ]
}

Rules:
- memory_type must be one of:
  preference, semantic, episodic, goal, project, instruction
- importance must be between 0.0 and 1.0
- confidence must be between 0.0 and 1.0
- Write memories in third person.
- Do not include explanations outside the JSON.
- If nothing is worth remembering, return:
  {"memories": []}
"""


def extract_memories(
    user_message: str,
    assistant_response: str,
    llm: LLM,
    conversation_context: str = "",
) -> list[dict]:
    prompt = f"""
{EXTRACTION_PROMPT}

Conversation context:
{conversation_context}

User:
{user_message}

Assistant:
{assistant_response}
"""

    raw_response = llm(prompt)

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, dict):
        return []

    memories = data.get("memories", [])

    if not isinstance(memories, list):
        return []

    validated = []

    valid_types = {
        "preference",
        "semantic",
        "episodic",
        "goal",
        "project",
        "instruction",
    }

    for item in memories:
        if not isinstance(item, dict):
            continue

        content = item.get("content")
        memory_type = item.get("memory_type")
        category = item.get("category", "general")
        importance = item.get("importance")
        confidence = item.get("confidence")

        if not isinstance(content, str) or not content.strip():
            continue

        if memory_type not in valid_types:
            continue

        if not isinstance(category, str):
            category = "general"

        if not isinstance(importance, (int, float)):
            continue

        if not isinstance(confidence, (int, float)):
            continue

        importance = max(0.0, min(1.0, float(importance)))
        confidence = max(0.0, min(1.0, float(confidence)))

        validated.append(
            {
                "content": content.strip(),
                "memory_type": memory_type,
                "category": category.strip() or "general",
                "importance": importance,
                "confidence": confidence,
            }
        )

    return validated