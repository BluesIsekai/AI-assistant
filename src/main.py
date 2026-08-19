import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AI.agent.ollama import send_message, unload_model
from AI.tools import skill_manager
from AI.ollama_manager import start_ollama, stop_ollama
from utils import init_memory_tracker, print_memory_stats
from config import NAME
import config


def clean_for_tts(text: str) -> str:
    """Remove chat formatting that should not be spoken."""
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"_{1,2}", "", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    return text.strip()


def process_input(user_input: str) -> str:
    """Process user input through the same AI + tool pipeline."""

    return send_message(
        user_input,
        skill_manager.get_tools(),
        skill_manager.get_tool_map(),
    )


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

        # =========================
        # VOICE MODE
        # =========================

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

                user_input = user_input.strip()

                print(f"You: {user_input}")

                command = re.sub(r"[^\w\s]", "", user_input).lower().strip()

                if command in {"exit", "quit"}:
                    print(f"{NAME}: See you later!")
                    break

                # SAME PIPELINE AS TEXT MODE
                response = process_input(user_input)

                print(f"\n{NAME}: {response}\n")

                # Only clean the copy sent to TTS
                voice.speak(clean_for_tts(response))

                print_memory_stats()

        # =========================
        # TEXT MODE
        # =========================

        else:

            print("Type 'exit' or 'quit' to stop.\n")

            while True:

                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in {"exit", "quit"}:
                    print(f"{NAME}: See you later!")
                    break

                # SAME PIPELINE AS VOICE MODE
                response = process_input(user_input)

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