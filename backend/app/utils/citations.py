def build_citations(sources: list[dict]) -> list[dict]:
    citations = []
    for idx, source in enumerate(sources, start=1):
        citations.append(
            {
                "index": idx,
                "title": source["title"],
                "url": source["url"],
                "credibility_score": source["credibility_score"],
            }
        )
    return citations
