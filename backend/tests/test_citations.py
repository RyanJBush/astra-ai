from app.utils.citations import build_citations


def test_build_citations_adds_indexed_references():
    sources = [
        {"title": "A", "url": "https://a.com", "credibility_score": 0.8},
        {"title": "B", "url": "https://b.com", "credibility_score": 0.7},
    ]
    citations = build_citations(sources)

    assert citations[0]["index"] == 1
    assert citations[1]["index"] == 2
    assert citations[0]["title"] == "A"
