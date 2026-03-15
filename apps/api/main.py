import logging

from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services.transcription import fetch_transcript_text
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    return SummarizeResponse(summary=transcript_text)
