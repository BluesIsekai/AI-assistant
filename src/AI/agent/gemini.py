import config
from google import genai
from google.genai import types


def get_client() -> genai.Client:
    """Initialized and returns a Gemini client instance."""
    return genai.Client()


def create_assistant_chat(client: genai.Client, tools: list):
    """Create a chat session configured with system instructions, tools, and temperature."""
    chat_config = types.GenerateContentConfig(
        system_instruction=config.SYSTEM_INSTRUCTION,
        tools=tools,
    )

    return client.chats.create(model=config.MODEL_NAME, config=chat_config)


def send_message_and_handle_tools(chat, user_input: str, tool_map: dict):
    """Send a message to the assistant and handle any function calls returned by the model."""
    response = chat.send_message(user_input)

    while response.function_calls:
        for call in response.function_calls:
            func_name = call.name
            func_args = call.args

            print(f"⚙️ [Executing Tool: {func_name} with args {dict(func_args)}...]")

            if func_name in tool_map:
                tool_result = tool_map[func_name](**func_args)
                response = chat.send_message(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": tool_result}
                    )
                )
            else:
                print(f"Error: Tool '{func_name}' not found.")
                break

    return response