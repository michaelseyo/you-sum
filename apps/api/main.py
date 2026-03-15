import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    return {"summary": "Hello world"}
