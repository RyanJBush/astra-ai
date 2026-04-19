from pydantic import BaseModel, HttpUrl


class SourceItem(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    relevance_score: float
    credibility_score: float
