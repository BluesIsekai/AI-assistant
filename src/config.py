import os
import sys


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def validate_config() -> None:
    """Validates required environment variables."""
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

# Model & Assistant configuration
MODEL_NAME = "gemini-3.6-flash"
LOCAL_MODEL = "qwen3.5:4b"
SYSTEM_INSTRUCTION = (
    "You are a personal desktop AI assistant. "
    "Your job is to help the user interact with their computer and get things done. "
    "You have access to tools that allow you to perform actions on the user's computer. "
    "Use tools when an action is requested instead of merely explaining how to do it. "
    "Never claim that an action was completed unless the corresponding tool confirms it. "
    "Keep responses concise and conversational. "
    "Do not unnecessarily use phrases like 'Certainly' or 'Of course'."
)