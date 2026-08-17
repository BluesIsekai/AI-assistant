import importlib
import pkgutil


class SkillManager:

    def __init__(self):
        self.skills = {}
        self.tools = {}
        self.tool_map = {}

    def register_skill(self, name: str, tools: list):
        if name in self.skills:
            raise ValueError(f"Skill '{name}' is already registered.")

        self.skills[name] = tools

        for tool in tools:
            tool_name = tool.__name__

            if tool_name in self.tool_map:
                raise ValueError(
                    f"Tool '{tool_name}' is already registered."
                )

            self.tools[tool_name] = tool
            self.tool_map[tool_name] = tool

    def unregister_skill(self, name: str):
        if name not in self.skills:
            return False

        tools = self.skills.pop(name)

        for tool in tools:
            tool_name = tool.__name__
            self.tools.pop(tool_name, None)
            self.tool_map.pop(tool_name, None)

        return True

    def get_tools(self) -> list:
        return list(self.tools.values())

    def get_tool_map(self) -> dict:
        return dict(self.tool_map)

    def get_skill(self, name: str):
        return self.skills.get(name)

    def list_skills(self) -> list:
        return list(self.skills.keys())

    def load_skill(self, module):
        name = getattr(module, "SKILL_NAME", None)
        tools = getattr(module, "SKILL_TOOLS", None)

        if not name:
            raise ValueError(
                f"Skill module '{module.__name__}' is missing SKILL_NAME."
            )

        if tools is None:
            raise ValueError(
                f"Skill module '{module.__name__}' is missing SKILL_TOOLS."
            )

        self.register_skill(name, tools)

    def discover_skills(self):
        import AI.skills

        for module_info in pkgutil.iter_modules(AI.skills.__path__):
            module_name = module_info.name

            if module_name.startswith("_"):
                continue

            module = importlib.import_module(
                f"AI.skills.{module_name}"
            )

            self.load_skill(module)