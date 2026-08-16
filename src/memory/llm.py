from typing import Protocol


class LLM(Protocol):
    def __call__(self, prompt: str) -> str:
        ...