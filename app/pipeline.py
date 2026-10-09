# Orchestrator for the data pipeline

from app.critic import critique_draft
from app.scraper import scrape_pages
from app.search import search_web
from app.writer import write_draft
import logging
import time

logger = logging.getLogger(__name__)

MAX_REVISIONS = 2

def run_pipeline(question: str) -> dict:
    started = time.perf_counter()

    results = search_web(question)
    logger.info('search returned %d results', len(results))

    if not results:
        return {
            'question': question,
            'answer': 'No sources were found for this question, so no answer was written.',
            'verdict': 'no_sources',
            'remaining_issues': [],
            'revisions': 0,
            'sources': [],
            'elapsed_seconds': round(time.perf_counter() - started, 1),
        }

    pages = scrape_pages(results)
    scraped_ok = sum(page.ok for page in pages)
    logger.info('scraped %d of %d pages fully', scraped_ok, len(pages))
    if scraped_ok == 0:
        logger.warning('no page could be scraped; writing from search snippets only')

    draft = write_draft(question, pages)
    critique = critique_draft(question, pages, draft)

    revisions = 0
    while critique.verdict == 'revise' and revisions < MAX_REVISIONS:
        revisions += 1
        logger.info('revision %d requested (%d issues)', revisions, len(critique.issues))
        draft = write_draft(question, pages, previous_draft=draft, feedback=critique.feedback)
        critique = critique_draft(question, pages, draft)

    elapsed = round(time.perf_counter() - started, 1)
    logger.info('finished verdict=%s revisions=%d elapsed=%.1fs', critique.verdict, revisions, elapsed)

    return {
        'question': question,
        'answer': draft,
        'verdict': critique.verdict,
        'remaining_issues': critique.issues,
        'revisions': revisions,
        'sources': [{'title': p.title, 'url': p.url, 'scraped': p.ok} for p in pages],
        'elapsed_seconds': elapsed,
    }