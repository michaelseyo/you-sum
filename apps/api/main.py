import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi

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


class SummarizeRequest(BaseModel):
    video_id: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/summarize")
async def summarize(payload: SummarizeRequest):
    logger.info("Summarize requested", extra={"video_id": payload.video_id})

    api = YouTubeTranscriptApi()
    fetched_transcript = api.fetch(payload.video_id)
    transcript_list = fetched_transcript.to_raw_data()
    formatted_transcript = "\n".join([entry["text"] for entry in transcript_list])

    return {"summary": formatted_transcript}
