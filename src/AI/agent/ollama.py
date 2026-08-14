from ollama import chat
import config


def create_tools(tools: list) -> list:
    tool_definitions = []

    for tool in tools:
        tool_definitions.append({
            "type": "function",
            "function": {
                "name": tool.__name__,
                "description": tool.__doc__ or "",
            },
        })

    return tool_definitions


def send_message(user_input: str, tools: list, tool_map: dict) -> str:
    messages = [
        {
            "role": "system",
            "content": config.SYSTEM_INSTRUCTION,
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    response = chat(
        model=config.LOCAL_MODEL,
        messages=messages,
        tools=tools,
        think=False,
        options={
            "num_ctx": config.CONTEXT_SIZE,
        }
    )

    while response.message.tool_calls:
        messages.append(response.message)

        for call in response.message.tool_calls:
            func_name = call.function.name
            func_args = call.function.arguments

            print(
                f"⚙️ [Executing Tool: {func_name} "
                f"with args {dict(func_args)}...]"
            )

            if func_name not in tool_map:
                tool_result = f"Error: Tool '{func_name}' not found."
            else:
                tool_result = tool_map[func_name](**func_args)

            messages.append(
                {
                    "role": "tool",
                    "name": func_name,
                    "content": str(tool_result),
                }
            )

        response = chat(
            model=config.LOCAL_MODEL,
            messages=messages,
            tools=tools,
            think=False,
            options={
                "num_ctx": config.CONTEXT_SIZE,
            }
        )

    return response.message.content


def unload_model() -> None:
    chat(
        model=config.LOCAL_MODEL,
        messages=[],
        keep_alive=0,
    )