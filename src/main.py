import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AI.agent.ollama import send_message
from AI.tools import ALL_TOOLS, TOOLS_MAP
from AI.ollama_manager import start_ollama, stop_ollama


def main():
    if not start_ollama():
        return

    print("🤖 AI Assistant Initialized. Type 'exit' or 'quit' to stop.\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    print("AI: See you later!")
                    break

                response = send_message(user_input, ALL_TOOLS, TOOLS_MAP)
                print(f"AI: {response}\n")

            except Exception as e:
                print(f"An error occurred: {e}\n")

    finally:
        stop_ollama()


if __name__ == "__main__":
    main()