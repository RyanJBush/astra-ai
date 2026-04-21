import re

from langchain_core.prompts import ChatPromptTemplate


class PlannerAgent:
    def __init__(self) -> None:
        self.prompt = ChatPromptTemplate.from_template(
            "Break the query into two research steps: {query}"
        )

    def plan(self, query: str, breadth: int = 3) -> list[str]:
        _ = self.prompt.invoke({"query": query})
        normalized_query = re.sub(r"\s+", " ", query).strip()
        if not normalized_query:
            return []
        candidate_parts = re.split(r"\band\b|,|;", normalized_query, flags=re.IGNORECASE)
        sub_questions = [part.strip(" .") for part in candidate_parts if part.strip(" .")]
        if not sub_questions:
            sub_questions = [normalized_query]
        plan_steps = [normalized_query]
        for sub_question in sub_questions[:breadth]:
            if sub_question.lower() != normalized_query.lower():
                plan_steps.append(sub_question)
        return list(dict.fromkeys(plan_steps))

    def generate_search_queries(self, step: str, recency_days: int | None = None) -> list[str]:
        variations = [
            step,
            f"{step} evidence",
            f"{step} official report",
            f"{step} latest updates",
        ]
        if recency_days:
            variations.append(f"{step} last {recency_days} days")
        return list(dict.fromkeys(variations))

    def generate_follow_up_queries(
        self,
        query: str,
        unsupported_claims: list[str],
    ) -> list[str]:
        follow_ups = [f"{query} contradictory evidence", f"{query} primary sources"]
        for claim in unsupported_claims[:3]:
            follow_ups.append(f"{claim} supporting evidence")
        return list(dict.fromkeys(follow_ups))
