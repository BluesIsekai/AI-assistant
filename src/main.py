import sys
from pathlib import Path

# Add src folder to sys.path so imports work consistently regardless of invocation path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import validate_config
from AI.tools import ALL_TOOLS, TOOLS_MAP
from AI.agent.gemini import get_client, create_assistant_chat, send_message_and_handle_tools

def main():
    # 1. Validate environment configuration
    validate_config()

    # 2. Initialize Gemini Client & Chat Session with tools
    client = get_client()
    chat = create_assistant_chat(client, tools=ALL_TOOLS)

    print("🤖 AI Assistant Initialized. Type 'exit' or 'quit' to stop.\n")

    # 3. Interaction loop
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("AI: Goodbye!")
                break

            response = send_message_and_handle_tools(chat, user_input, TOOLS_MAP)
            print(f"AI: {response.text}\n")

        except Exception as e:
            print(f"An error occurred: {e}\n")

if __name__ == "__main__":
    main()
