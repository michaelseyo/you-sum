import logging
from contextlib import asynccontextmanager
from pathlib import Path

from app.clients.db import get_db, init_db
from app.clients.openai_client import create_openai_client
from app.config import get_allowed_origin_regex, get_allowed_origins
from app.repositories.summaries_repository import SummariesRepository
from app.repositories.transcripts_repository import TranscriptsRepository
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services.summarize_orchestrator import SummarizeOrchestrator
from app.services.summary import SummaryService
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import APIStatusError, RateLimitError
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent / ".env")

summary_service = SummaryService(client=create_openai_client())
transcripts_repository = TranscriptsRepository()
summaries_repository = SummariesRepository()
summarize_orchestrator = SummarizeOrchestrator(
    summary_service=summary_service,
    transcripts_repository=transcripts_repository,
    summaries_repository=summaries_repository,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Ensure the database schema exists before serving requests
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=get_allowed_origin_regex() or r"chrome-extension://.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
) -> SummarizeResponse:
    logger.info("Summarize requested for video_id=%s", payload.video_id)
    try:
        # Keep the route thin and delegate cache-or-generate logic to the orchestrator
        result = await summarize_orchestrator.summarize_video(db, payload.video_id)
    except RateLimitError as exc:
        logger.warning("OpenAI rate limit or quota issue: %s", exc)
        raise HTTPException(
            status_code=429,
            detail="Summary generation is temporarily unavailable due to an OpenAI quota or rate limit issue.",
        ) from exc
    except APIStatusError as exc:
        logger.exception("OpenAI API status error")
        raise HTTPException(
            status_code=502,
            detail="Summary generation failed because the upstream AI service returned an error.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected summary generation failure")
        raise HTTPException(
            status_code=500,
            detail="Summary generation failed unexpectedly.",
        ) from exc

    return SummarizeResponse(
        summary=result.summary,
        cached=result.cached,
        prompt_version=result.prompt_version,
    )
