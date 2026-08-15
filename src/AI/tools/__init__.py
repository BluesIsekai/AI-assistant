from .system_tools import (
    ALL_TOOLS as SYSTEM_TOOLS,
    get_current_time,
    open_website,
    open_app,
    web_search,
)

from ..spotify import ALL_SPOTIFY_TOOLS


ALL_TOOLS = [
    *SYSTEM_TOOLS,
    *ALL_SPOTIFY_TOOLS,
]

TOOLS_MAP = {
    func.__name__: func
    for func in ALL_TOOLS
}


__all__ = [
    "ALL_TOOLS",
    "TOOLS_MAP",
    "ALL_SPOTIFY_TOOLS",
    "get_current_time",
    "open_website",
    "open_app",
    "web_search",
]