import logging
from pathlib import Path

from app.clients.openai_client import create_openai_client
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services.summary import SummaryService
from app.services.transcript import fetch_transcript_text
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import APIStatusError, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent / ".env")

summary_service = SummaryService(client=create_openai_client())

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://.*",
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
) -> SummarizeResponse:
    logger.info("Summarize requested for video_id=%s", payload.video_id)
    transcript_text = fetch_transcript_text(video_id=payload.video_id)
    try:
        summary_text = await summary_service.summarize_transcript(transcript_text)
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

    return SummarizeResponse(summary=summary_text)
