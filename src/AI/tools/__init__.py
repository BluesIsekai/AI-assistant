from ..skill_manager import SkillManager


skill_manager = SkillManager()

skill_manager.load_skills("AI.skills")


ALL_TOOLS = skill_manager.get_tools()
TOOLS_MAP = skill_manager.get_tool_map()


__all__ = [
    "skill_manager",
    "ALL_TOOLS",
    "TOOLS_MAP",
]