# Multi-Agent Research Tool

A pipeline that answers a research question from live web sources. It searches the web, scrapes the pages, writes a cited answer, and has a second model fact-check that answer against the same sources, revising it when problems are found.


## How it works

```
question
   │
   ▼
[1] Search     Tavily returns ranked results (title, URL, snippet)
   │
   ▼
[2] Scrape     BeautifulSoup fetches and cleans each page, in parallel
   │
   ▼
[3] Write      LCEL chain drafts an answer with numbered citations [1], [2]
   │
   ▼
[4] Critique   LCEL chain returns a structured verdict: approve or revise
   │
   ├── revise ──► feedback goes back to the writer (maximum 2 rounds)
   │
   ▼
cited answer + verdict + source list
```

| Stage | Implementation | Uses an LLM? |
|---|---|---|
| Search | Tavily API wrapped in a typed function | No |
| Scrape | `requests` + BeautifulSoup, thread pool | No |
| Writer | LangChain Expression Language (LCEL) chain | Yes |
| Critic | LCEL chain with structured (Pydantic) output | Yes |

Only the two stages that require judgment call a model. Retrieval and parsing are deterministic, which makes them cheaper, faster and testable.

## Features

- **Grounded answers.** The writer may use only the supplied sources and must cite each claim by source number.
- **Independent fact-check.** The critic receives the sources and the draft, then returns a validated `Critique` object (`verdict`, `issues`, `feedback`) that drives the revision loop.
- **Bounded revision loop.** A hard cap on revision rounds guarantees termination and protects API quota.
- **Polite scraping.** Honours `robots.txt`, identifies itself with a User-Agent, applies timeouts, caps text length, and rejects non-HTML content.
- **Graceful degradation.** If a page cannot be scraped, the search snippet is used instead and the failure is reported, never hidden.
- **Prompt-injection defences.** Sources are delimited, declared untrusted, and the model is instructed never to follow instructions found inside them.
- **Resilience.** Network failures to the LLM are retried with exponential backoff; Tavily calls are retried separately.
- **Observability.** Structured logging of result counts, revisions, verdict and elapsed time. Keys and page contents are never logged.
- **Honest outcomes.** Returns an explicit `no_sources` verdict rather than inventing an answer when search finds nothing.

## Tech stack

| Package | Purpose |
|---|---|
| `langchain-core` | LCEL: prompts, parsers, the `\|` chain operator |
| `langchain-google-genai` | Gemini chat model integration |
| `tavily-python` | Web search client |
| `requests`, `beautifulsoup4`, `lxml` | Fetching and parsing pages |
| `pydantic` | Typed contracts between stages and structured LLM output |
| `tenacity` | Retry with exponential backoff |
| `python-dotenv` | Loading secrets from `.env` in development |

## Project structure

```
research_tool/
├── app/
│   ├── __init__.py
│   ├── config.py       # environment loading and fail-fast validation
│   ├── schemas.py      # SearchResult, ScrapedPage, Critique
│   ├── search.py       # stage 1: Tavily search with URL de-duplication
│   ├── scraper.py      # stage 2: robots-aware parallel scraper
│   ├── llm.py          # model factory and LLM retry policy
│   ├── writer.py       # stage 3: writer chain
│   ├── critic.py       # stage 4: critic chain
│   └── pipeline.py     # orchestrator and revision loop
├── .env.example        # required variable names (no values)
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting started

### Prerequisites

- Python 3.12
- A [Tavily](https://tavily.com) API key
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com)

### Installation

```bash
git clone https://github.com/0checkMate/research_tool
cd research_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in the values:

```
GOOGLE_API_KEY=your-gemini-key
TAVILY_API_KEY=your-tavily-key
LLM_MODEL=a-gemini-model-name-available-to-your-key
```

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini API key |
| `TAVILY_API_KEY` | Yes | Tavily search API key |
| `LLM_MODEL` | Yes | Gemini model identifier |

The application validates these at startup and stops with a clear message if any are missing. **Never commit `.env`.**

### Usage

Create a script in the project root:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    force=True,
)

from app.config import validate_settings
from app.pipeline import run_pipeline

validate_settings()

result = run_pipeline('What are the latest developments in LangChain?')

print(result['answer'])
print('Verdict:', result['verdict'], '| Revisions:', result['revisions'])
```

Configure logging before calling the pipeline, otherwise informational messages are discarded.

### Result format

`run_pipeline` returns a dictionary:

| Key | Description |
|---|---|
| `question` | The question asked |
| `answer` | The final cited answer |
| `verdict` | `approve`, `revise` (cap reached with issues outstanding) or `no_sources` |
| `remaining_issues` | Problems the critic still reports, if any |
| `revisions` | Number of revision rounds performed |
| `sources` | List of `{title, url, scraped}` |
| `elapsed_seconds` | Total run time |

## Design decisions

- **LLMs only where judgment is needed.** Search and scraping are plain functions.
- **Typed boundaries.** Each stage consumes and returns Pydantic models, so a malformed handoff fails at the boundary where it happened.
- **Vendor wrapped behind own functions.** Swapping the search provider or LLM touches one module.
- **Failures as data.** A failed scrape is an expected outcome, returned as a `ScrapedPage` with `ok=False`, not an exception.
- **Retries at the smallest unit.** Only the failing remote call is retried, never the whole pipeline.
- **Fail fast.** Missing configuration stops the application at startup, not mid-request.
- **Loop bounded.** `MAX_REVISIONS` caps paid model calls; the worst case is six per run.

## Known limitations

- **JavaScript-rendered pages** return little or no text to BeautifulSoup; the snippet fallback covers these.
- **Same-family critic.** A critic from the same model family as the writer shares its blind spots and can favour its own style. It reduces errors but does not eliminate them; verify important claims against the cited sources.
- **Free-tier quotas.** Gemini and Tavily free tiers enforce rate and monthly limits. Exceeding the per-minute limit returns an error that is not yet retried automatically.
- **Heuristic text extraction.** Page cleaning removes common boilerplate but cannot be perfect on every site.
- **Fixed-sampling models.** Some Gemini models ignore the `temperature` setting.

## Responsible use

- Intended for modest, personal-scale research using publicly available pages.
- The scraper honours `robots.txt` and declines sites that disallow automated access. Respect each site's terms of service.
- Do not republish scraped content wholesale; the tool returns summaries with source links.
- Free-tier model terms may allow submitted content to be used to improve the provider's products. Do not send confidential or proprietary material through this tool.

## Roadmap

- [x] Configuration with fail-fast validation
- [x] Tavily search stage with de-duplication
- [x] Robots-aware parallel scraper
- [x] Writer and critic LCEL chains with structured critique
- [x] Bounded revision loop, logging and retry handling
- [x] FastAPI backend (validated request, typed response, CORS, health check)
- [x] Web frontend
- [x] Deployment on Render (API as web service, frontend as static site)
- [x] Per-client rate limiting to protect API quota in production

## License

To be decided. Add a `LICENSE` file before publishing the repository.