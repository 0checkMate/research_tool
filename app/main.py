
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.config import LLM_MODEL, validate_settings
from app.pipeline import run_pipeline
from app.schemas import SearchRequest, SearchResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    force=True,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()
    logger.info('Configuration validated; using model %s', LLM_MODEL)
    yield
    logger.info('Application shutting down')


app = FastAPI(
    title='Multi-Agent Research Tool',
    description='Research answers grounded in live web sources.',
    version='0.1.0',
    lifespan=lifespan,
)


@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}

@app.post('/search', response_model=SearchResponse)
def search(request: SearchRequest):
    logger.info('Search request received (%d characters)', len(request.question))
    try:
        return run_pipeline(request.question)
    except Exception:
        logger.exception('Pipeline failed')
        raise HTTPException(
            status_code=502,
            detail='The research pipeline failed. Please try again later.',
        )