from ollama import chat
import config
import inspect

_conversation_history: list = []


def clear_history() -> None:
    """Clears the stored conversation history."""
    global _conversation_history
    _conversation_history.clear()


def get_history() -> list:
    """Returns a shallow copy of the stored conversation history."""
    return list(_conversation_history)


def format_message(msg) -> dict:
    """Formats an Ollama Message object or dict into a clean dict for Ollama chat history."""
    if hasattr(msg, "model_dump"):
        d = msg.model_dump(exclude_none=True)
    elif isinstance(msg, dict):
        d = dict(msg)
    else:
        d = {
            "role": str(getattr(msg, "role", "assistant")),
            "content": str(getattr(msg, "content", "")),
        }

    # Exclude internal reasoning/thinking output from message history to stay token-efficient
    d.pop("thinking", None)
    return d


def _trim_history(history: list, max_messages: int) -> list:
    """Trims message history to at most max_messages while ensuring it begins with a user message."""
    if len(history) <= max_messages:
        return history

    trimmed = history[-max_messages:]
    while trimmed and trimmed[0].get("role") != "user":
        trimmed.pop(0)

    return trimmed


def create_tools(tools: list) -> list:
    tool_definitions = []

    for tool in tools:
        signature = inspect.signature(tool)

        properties = {}
        required = []

        for name, parameter in signature.parameters.items():
            properties[name] = {
                "type": "string",
                "description": f"Parameter for {name}",
            }

            if parameter.default is inspect.Parameter.empty:
                required.append(name)

        tool_definitions.append({
            "type": "function",
            "function": {
                "name": tool.__name__,
                "description": tool.__doc__ or "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        })

    return tool_definitions


def send_message(
    user_input: str,
    tools: list,
    tool_map: dict,
    history: list = None,
) -> str:
    """Sends a user message to Ollama with multi-turn conversation context and tool support.

    If history is provided (as a list), it will be used and updated in-place.
    Otherwise, the module-level conversation history is maintained across calls.
    """
    global _conversation_history

    target_history = history if history is not None else _conversation_history

    # Append user input to history
    target_history.append({
        "role": "user",
        "content": user_input,
    })

    max_history = getattr(config, "MAX_HISTORY_MESSAGES", 20)
    trimmed_history = _trim_history(target_history, max_history)

    # Build active context payload for Ollama
    messages = [
        {
            "role": "system",
            "content": config.SYSTEM_INSTRUCTION,
        },
        *[format_message(m) for m in trimmed_history]
    ]

    keep_alive_val = getattr(config, "KEEP_ALIVE", "5m")

    response = chat(
        model=config.LOCAL_MODEL,
        messages=messages,
        tools=tools,
        think=False,
        keep_alive=keep_alive_val,
        options={
            "num_ctx": config.CONTEXT_SIZE,
        }
    )

    tool_iterations = 0
    max_tool_iterations = getattr(config, "MAX_TOOL_ITERATIONS", 10)

    while response.message.tool_calls and tool_iterations < max_tool_iterations:
        tool_iterations += 1
        assistant_msg = format_message(response.message)
        target_history.append(assistant_msg)
        messages.append(assistant_msg)

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
                try:
                    tool_result = tool_map[func_name](**func_args)
                except Exception as e:
                    tool_result = f"Error executing tool '{func_name}': {e}"

            tool_msg = {
                "role": "tool",
                "name": func_name,
                "content": str(tool_result),
            }
            target_history.append(tool_msg)
            messages.append(tool_msg)

        response = chat(
            model=config.LOCAL_MODEL,
            messages=messages,
            tools=tools,
            think=False,
            keep_alive=keep_alive_val,
            options={
                "num_ctx": config.CONTEXT_SIZE,
            }
        )


    if tool_iterations >= max_tool_iterations:
        print(f"⚠️ Warning: Reached maximum tool iteration limit ({max_tool_iterations}).")

    final_assistant_msg = format_message(response.message)
    target_history.append(final_assistant_msg)

    # If using module history, enforce sliding window trim
    if history is None:
        _conversation_history[:] = _trim_history(_conversation_history, max_history)

    return response.message.content or ""


def unload_model() -> None:
    """Unloads the local Ollama model from RAM/VRAM by sending keep_alive=0."""
    try:
        chat(
            model=config.LOCAL_MODEL,
            messages=[],
            keep_alive=0,
        )
        print("🧠 Local model unloaded from memory.")
    except Exception as e:
        pass

