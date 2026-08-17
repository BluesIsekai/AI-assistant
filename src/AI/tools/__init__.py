from .system_tools import (
    SYSTEM_TOOLS,
    get_current_time,
    open_website,
    open_app,
    web_search,
)

from ..spotify import ALL_SPOTIFY_TOOLS
from ..skill_manager import SkillManager


skill_manager = SkillManager()

skill_manager.register_skill(
    "system",
    SYSTEM_TOOLS,
)

skill_manager.register_skill(
    "spotify",
    ALL_SPOTIFY_TOOLS,
)


ALL_TOOLS = skill_manager.get_tools()
TOOLS_MAP = skill_manager.get_tool_map()


__all__ = [
    "skill_manager",
    "ALL_TOOLS",
    "TOOLS_MAP",
    "ALL_SPOTIFY_TOOLS",
    "get_current_time",
    "open_website",
    "open_app",
    "web_search",
]