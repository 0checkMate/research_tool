
from pydantic import BaseModel

# SearchResult schema for the search results returned by the search engine.
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    score: float = 0.0

# ScrapedPage schema for the pages scraped from the web.
class ScrapedPage(BaseModel):
    url: str
    title: str
    text: str
    ok: bool = True
    error: str = ''