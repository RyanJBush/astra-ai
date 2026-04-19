from langchain_core.prompts import ChatPromptTemplate


class PlannerAgent:
    def __init__(self) -> None:
        self.prompt = ChatPromptTemplate.from_template(
            "Break the query into two research steps: {query}"
        )

    def plan(self, query: str) -> list[str]:
        _ = self.prompt.invoke({"query": query})
        return [query, f"{query} latest updates"]
