import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AI.agent.ollama import send_message, unload_model
from AI.tools import skill_manager
from AI.ollama_manager import start_ollama, stop_ollama
from utils import init_memory_tracker, print_memory_stats
from config import NAME
import config


def main():
    init_memory_tracker()

    if not start_ollama():
        return

    voice = None

    if config.VOICE_ENABLED:
        from voice import VoiceInterface, CrispASRListener
        from voice.tts import create_tts

        voice = VoiceInterface(
            stt=CrispASRListener(
                crispasr_exe=config.CRISPASR_EXE,
                model_path=config.STT_MODEL_PATH,
                backend=config.STT_BACKEND,
                language=config.STT_LANGUAGE,
                stream_step_ms=config.STT_STREAM_STEP_MS,
                stream_keep_ms=config.STT_STREAM_KEEP_MS,
            ),
            tts=create_tts(config),
        )

        voice.start()

    print("🤖 AI Assistant Initialized.\n")
    print("Loaded skills:", skill_manager.list_skills())

    try:
        if voice is not None:
            print(
                "🎙️ Voice mode active. "
                "Speak to the assistant. "
                "Say 'exit' or 'quit' to stop.\n"
            )

            while True:
                user_input = voice.listen()

                if not user_input:
                    continue

                print(f"You: {user_input}")

                if user_input.lower().strip() in {"exit", "quit"}:
                    print(f"{NAME}: See you later!")
                    break

                response = send_message(
                    user_input,
                    skill_manager.get_tools(),
                    skill_manager.get_tool_map(),
                )

                print(f"\n{NAME}: {response}\n")

                voice.speak(response)

                print_memory_stats()

        else:
            print("Type 'exit' or 'quit' to stop.\n")

            while True:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in {"exit", "quit"}:
                    print(f"{NAME}: See you later!")
                    break

                response = send_message(
                    user_input,
                    skill_manager.get_tools(),
                    skill_manager.get_tool_map(),
                )

                print(f"\n{NAME}: {response}\n")

                print_memory_stats()

    except KeyboardInterrupt:
        print("\nStopping...")

    except Exception as e:
        print(f"An error occurred: {e}\n")

    finally:
        if voice is not None:
            voice.stop()

        unload_model()
        stop_ollama()


if __name__ == "__main__":
    main()