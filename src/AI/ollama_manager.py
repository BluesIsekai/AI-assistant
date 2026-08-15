import subprocess
import time
import requests


OLLAMA_HOST = "http://127.0.0.1:11434"

_ollama_process = None


def is_ollama_running() -> bool:
    try:
        response = requests.get(
            f"{OLLAMA_HOST}/api/tags",
            timeout=1,
        )
        return response.ok
    except requests.RequestException:
        return False


def start_ollama() -> bool:
    global _ollama_process

    if is_ollama_running():
        return True

    try:
        _ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except FileNotFoundError:
        print("❌ Ollama was not found in PATH.")
        return False

    for _ in range(20):
        if is_ollama_running():
            return True

        time.sleep(0.5)

    print("❌ Ollama server failed to start.")
    return False


def stop_ollama() -> None:
    global _ollama_process

    # We didn't start Ollama, so don't touch it.
    if _ollama_process is None:
        return

    try:
        subprocess.run(
            [
                "taskkill",
                "/PID",
                str(_ollama_process.pid),
                "/T",
                "/F",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    finally:
        _ollama_process = None