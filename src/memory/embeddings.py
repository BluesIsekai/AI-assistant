import ollama


EMBEDDING_MODEL = "qwen3-embedding:0.6b"


def embed(text: str) -> list[float]:
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response["embeddings"][0]