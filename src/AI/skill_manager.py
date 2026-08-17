import importlib
from pathlib import Path


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
            if tool.__name__ in self.tool_map:
                raise ValueError(
                    f"Tool '{tool.__name__}' is already registered."
                )

            self.tools[tool.__name__] = tool
            self.tool_map[tool.__name__] = tool

    def load_skills(self, package: str):
        package_module = importlib.import_module(package)

        package_path = Path(package_module.__file__).parent

        for file in package_path.glob("*.py"):

            if file.name == "__init__.py":
                continue

            module_name = file.stem

            module = importlib.import_module(
                f"{package}.{module_name}"
            )

            skill_name = getattr(module, "SKILL_NAME", None)
            skill_tools = getattr(module, "SKILL_TOOLS", None)

            if skill_name is None or skill_tools is None:
                continue

            self.register_skill(
                skill_name,
                skill_tools,
            )

    def get_tools(self) -> list:
        return list(self.tools.values())

    def get_tool_map(self) -> dict:
        return dict(self.tool_map)

    def get_skill(self, name: str):
        return self.skills.get(name)

    def list_skills(self) -> list:
        return list(self.skills.keys())