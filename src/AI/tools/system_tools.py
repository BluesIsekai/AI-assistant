import os
import subprocess
import webbrowser
from ddgs import DDGS
from datetime import datetime
from .aliases import APP_ALIASES
from tavily import TavilyClient
from config import TAVILY_API_KEY

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


#----------------------------------------------------------------------------------------

def web_search(query: str) -> str:
    """
    Search the internet for information that requires current, external,
    or explicitly requested web information.

    IMPORTANT:
    Do NOT use this tool for ordinary programming questions or code generation.
    If the user asks for code for a standard algorithm, data structure,
    programming concept, or common language feature, answer directly from
    your existing knowledge.

    Examples that MUST NOT use this tool:
    - "give me DFS code in C++"
    - "write binary search in Python"
    - "implement a linked list in C++"
    - "explain recursion"
    - "what is a DFA?"
    - "write an SQL JOIN example"

    Use this tool for:
    - current or recent news
    - current events
    - latest releases
    - current prices or availability
    - current software/library/API documentation
    - information that may have changed recently
    - niche information you genuinely do not know
    - explicit requests to search the web or look something up online

    Do not use this tool merely because a web result or example could
    improve an otherwise answerable response.

    Never claim that you searched the web unless this tool was actually
    executed during the current response.

    When searching, preserve the user's terminology and intent.
    Do not silently replace the user's topic with a different concept.

    After searching, base the answer on the retrieved information.
    If the query is ambiguous, explain the distinction instead of
    confidently assuming what the user meant.
    """
    if not query:
        return "Please provide a search query."

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
        )

        results = response.get("results", [])

        if results:
            output = []

            for result in results:
                output.append(
                    f"Title: {result.get('title', '')}\n"
                    f"URL: {result.get('url', '')}\n"
                    f"Content: {result.get('content', '')}"
                )

            return "\n\n".join(output)

    except Exception as e:
        print(f"⚠️ Tavily search failed: {e}")
        print("↪ Falling back to DuckDuckGo...")

    try:
        results = DDGS().text(
            query,
            max_results=5,
        )

        if not results:
            return "No search results found."

        output = []

        for result in results:
            output.append(
                f"Title: {result.get('title', '')}\n"
                f"URL: {result.get('href', '')}\n"
                f"Content: {result.get('body', '')}"
            )

        return "\n\n".join(output)

    except Exception as e:
        return f"Web search failed. Tavily and DuckDuckGo were unavailable: {e}"


ALL_TOOLS = [
    get_current_time,
    open_website,
    open_app,
    web_search,
]

TOOLS_MAP = {func.__name__: func for func in ALL_TOOLS}

