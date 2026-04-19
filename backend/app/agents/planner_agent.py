import re


class PlannerAgent:
    """Builds an initial search plan from a user research query."""

    def plan_queries(self, query: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", query).strip()
        facets = [
            cleaned,
            f"{cleaned} latest developments",
            f"{cleaned} technical analysis",
            f"{cleaned} risks and limitations",
        ]
        return list(dict.fromkeys(facets))
