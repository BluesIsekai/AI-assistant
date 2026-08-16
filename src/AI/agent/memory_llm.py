from ollama import chat
import config


def ollama_memory_llm(prompt: str) -> str:
    response = chat(
        model=config.LOCAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        think=False,
        keep_alive=config.KEEP_ALIVE,
        options={
            "num_ctx": config.CONTEXT_SIZE,
        },
    )

    return response.message.content or ""