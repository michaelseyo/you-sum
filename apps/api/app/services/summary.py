import os

from app.prompts.summarize import SUMMARY_INSTRUCTIONS, build_summary_prompt
from openai import AsyncOpenAI


class SummaryService:
    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    async def summarize_transcript(self, transcript_text: str) -> str:
        prompt = build_summary_prompt(transcript_text)
        response = await self.client.responses.create(
            model=self.model,
            instructions=SUMMARY_INSTRUCTIONS,
            input=prompt,
        )

        return response.output_text
