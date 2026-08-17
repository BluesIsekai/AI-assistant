from ..skill_manager import SkillManager

from ..skills.system import SKILL_NAME as SYSTEM_NAME
from ..skills.system import SKILL_TOOLS as SYSTEM_TOOLS

from ..skills.spotify import SKILL_NAME as SPOTIFY_NAME
from ..skills.spotify import SKILL_TOOLS as SPOTIFY_TOOLS


skill_manager = SkillManager()

skill_manager.register_skill(
    SYSTEM_NAME,
    SYSTEM_TOOLS,
)

skill_manager.register_skill(
    SPOTIFY_NAME,
    SPOTIFY_TOOLS,
)


ALL_TOOLS = skill_manager.get_tools()
TOOLS_MAP = skill_manager.get_tool_map()


__all__ = [
    "skill_manager",
    "ALL_TOOLS",
    "TOOLS_MAP",
]