class ToolRegistry:
    STAGE_TO_TOOLS = {
        "planning": {"planner"},
        "searching": {"search"},
        "extracting": {"scraper"},
        "validating": {"validator"},
        "synthesizing": {"reporting"},
    }

    ROLE_POLICIES = {
        "admin": {"planner", "search", "scraper", "validator", "reporting", "citations"},
        "researcher": {"planner", "search", "scraper", "validator", "reporting", "citations"},
        "viewer": set(),
        "user": {"planner", "search", "scraper", "validator", "reporting", "citations"},
    }

    def allowed_tools_for_role(self, role: str) -> set[str]:
        return self.ROLE_POLICIES.get(role.lower(), set())

    def ensure_stage_allowed(self, role: str, stage: str) -> None:
        allowed = self.allowed_tools_for_role(role)
        required = self.STAGE_TO_TOOLS.get(stage, set())
        missing = required - allowed
        if missing:
            missing_tools = ", ".join(sorted(missing))
            raise PermissionError(
                f"Role '{role}' cannot execute stage '{stage}'. "
                f"Missing tools: {missing_tools}"
            )
