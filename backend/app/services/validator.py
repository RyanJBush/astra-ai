class ValidationLayer:
    def filter_sources(self, sources: list[dict[str, str]]) -> list[dict[str, str]]:
        validated: list[dict[str, str]] = []
        for source in sources:
            content = source.get("content", "")
            if len(content) >= 100 and source.get("url", "").startswith("http"):
                validated.append(source)
        return validated
