import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AI.agent.ollama import send_message, unload_model
from AI.tools import ALL_TOOLS, TOOLS_MAP
from AI.ollama_manager import start_ollama, stop_ollama
from utils import init_memory_tracker, print_memory_stats
from config import NAME


def main():
    init_memory_tracker()

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
                    print(f"{NAME}: See you later!")
                    break

                response = send_message(user_input, ALL_TOOLS, TOOLS_MAP)
                print(f"{NAME}: {response}\n")

                print_memory_stats()

            except Exception as e:
                print(f"An error occurred: {e}\n")

    finally:
        unload_model()
        stop_ollama()



if __name__ == "__main__":
    main()