# AI Assistant 🤖

A personal desktop AI assistant built in Python, supporting local LLM inference via **Ollama (Qwen)** and cloud model fallback via **Google Gemini**, complete with tool calling for OS-level control and real-time web search.

---

## ✨ Features

- **💻 Desktop Application Launcher**: Launch desktop applications like Chrome, VS Code, Discord, Spotify, Notepad, Calculator, etc., using smart app alias mapping.
- **🌐 Web Browsing**: Open URLs directly in your system default browser.
- **🔎 Intelligent Web Search**: Perform live web searches powered by **Tavily API** with automatic fallback to **DuckDuckGo**.
- **📅 Time & Date Utilities**: Retrieve real-time clock and calendar details.
- **🤖 Dual Model Support**:
  - **Local Model**: Powered by Ollama (`qwen3.5:9b` by default).
  - **Cloud Model**: Google Gemini (`gemini-3.6-flash`).
- **⚙️ Dynamic Tool Calling**: Auto-discovers Python tool functions and executes tool calls seamlessly during conversation.

---

## 🛠️ Prerequisites

- **Python**: `>= 3.14`
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- **Ollama** (for local LLM mode): Install [Ollama](https://ollama.ai/) and pull the desired model:
  ```bash
  ollama pull qwen3.5:9b
  ```

---

## ⚙️ Configuration & Environment Setup

Create a `.env` file in the root directory of the project:

```env
# Required if using Google Gemini agent
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Tavily Search API key (Falls back to DuckDuckGo if omitted)
TAVILY_API_KEY=your_tavily_api_key_here
```

Model parameters and context sizes can be customized in `src/config.py`.

---

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Run the AI Assistant**:
   ```bash
   uv run .\src\main.py
   ```

3. **Interact with the Assistant**:
   - Type your requests in the interactive terminal prompt (`You: ...`).
   - Example prompts:
     - *"Open VS Code"*
     - *"What's the current date and time?"*
     - *"Open youtube.com"*
     - *"Search for the latest tech news"*
   - Type `exit` or `quit` to end the session.

---