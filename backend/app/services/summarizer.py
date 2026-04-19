class SummarizationAgent:
    def summarize(self, query: str, sources: list[dict[str, str]]) -> str:
        lines = [f"Research topic: {query}"]
        for idx, source in enumerate(sources, start=1):
            excerpt = source["content"][:180]
            lines.append(f"- [{idx}] {source['title']}: {excerpt}")
        return "\n".join(lines)
