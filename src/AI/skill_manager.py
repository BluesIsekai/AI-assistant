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

    def get_tools(self) -> list:
        return list(self.tools.values())

    def get_tool_map(self) -> dict:
        return dict(self.tool_map)

    def get_skill(self, name: str):
        return self.skills.get(name)

    def list_skills(self) -> list:
        return list(self.skills.keys())