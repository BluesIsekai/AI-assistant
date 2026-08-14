from ollama import chat
import config


def send_message(user_input: str) -> str:
    response = chat(
        model=config.LOCAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
        think=False,
    )

    return response.message.content


def unload_model() -> None:
    chat(
        model=config.LOCAL_MODEL,
        messages=[],
        keep_alive=0,
    )