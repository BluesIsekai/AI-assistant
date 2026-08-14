import os
import subprocess
import webbrowser
from datetime import datetime
from .aliases import APP_ALIASES

def get_current_time() -> str:
    """Returns the current date and time.
    ONLY use this tool when the user explicitly asks for the current
    time, date, day, or a time/date-related calculation. Do not use
    this tool just because the conversation mentions a time of day,
    tonight, today, morning, evening, etc.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#--------------------------------------------------------------------------------------

def open_website(url: str) -> str:
    """Opens a website URL in the user's web browser.
    Use this ONLY when the user provides or requests a specific website URL (e.g. google.com, youtube.com, github.com).
    Do NOT use this tool to launch desktop applications such as Chrome, Firefox, Notepad, VS Code, or Spotify.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Successfully opened {url} in your browser."

#--------------------------------------------------------------------------------------

def open_app(app_name: str) -> str:
    """Launches a desktop application installed on the user's Windows computer.
    Use this ONLY when the user asks to launch, open, or start a desktop application.
    Examples of applications: Chrome, Google Chrome, Firefox, Edge, Discord, VS Code, Spotify, Notepad, Calculator.
    Do NOT use this tool for opening websites or URLs.
    """
    if not app_name:
        return "Please provide an application name."

    cleaned_name = app_name.strip().lower()
    target_app = APP_ALIASES.get(cleaned_name, app_name.strip())

    # Try Windows ShellExecute via os.startfile first
    if hasattr(os, "startfile"):
        try:
            os.startfile(target_app)
            return f"Successfully opened {app_name}"
        except OSError:
            pass

    # Fallback to subprocess Popen
    try:
        subprocess.Popen(
            [target_app],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Successfully opened {app_name}"

    except FileNotFoundError:
        try:
            subprocess.Popen(
                f'start "" "{target_app}"',
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return f"Successfully opened {app_name}"

        except Exception as e:
            return f"Error: Could not find or launch application '{app_name}'. Error details: {e}"

    except Exception as e:
        return f"An unexpected error occurred while launching '{app_name}': {e}"


ALL_TOOLS = [
    get_current_time,
    open_website,
    open_app,
]

TOOLS_MAP = {func.__name__: func for func in ALL_TOOLS}

