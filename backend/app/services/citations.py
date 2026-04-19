class CitationSystem:
    def build(self, sources: list[dict[str, str]]) -> list[dict[str, str | int]]:
        citations: list[dict[str, str | int]] = []
        for idx, source in enumerate(sources, start=1):
            citations.append(
                {
                    "marker": f"[{idx}]",
                    "excerpt": source["content"][:220],
                    "source_index": idx - 1,
                }
            )
        return citations
