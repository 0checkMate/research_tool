
from typing import Literal
from pydantic import BaseModel, Field

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

# Critique schema for the critique of a draft answer.
class Critique(BaseModel):
    verdict: Literal['approve', 'revise'] = Field(
        description='approve only if the draft is accurate, grounded in the sources and answers the question'
    )
    issues: list[str] = Field(
        description='specific problems found, such as unsupported claims or wrong citations; empty if none'
    )
    feedback: str = Field(
        description='concise, actionable instructions for the writer to fix the issues; empty if approved'
    )