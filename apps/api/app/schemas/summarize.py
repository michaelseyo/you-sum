from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    video_id: str


class SummarizeResponse(BaseModel):
    summary: str

