import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.prompts.summarize import SUMMARY_PROMPT_VERSION
from app.repositories.summaries_repository import SummariesRepository
from app.repositories.transcripts_repository import TranscriptsRepository
from app.services.cache_keys import (
    build_transcript_fingerprint,
    normalize_transcript_text,
)
from app.services.summary import SummaryService
from app.services.transcript import fetch_transcript_text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

StreamEvent = dict[str, str | bool]


@dataclass(slots=True)
class SummarizeResult:
    """Result returned to the API route after cache lookup or generation."""

    summary: str
    cached: bool
    prompt_version: str


class SummarizeOrchestrator:
    """Coordinates transcript reuse, summary reuse, and OpenAI generation."""

    def __init__(
        self,
        *,
        summary_service: SummaryService,
        transcripts_repository: TranscriptsRepository,
        summaries_repository: SummariesRepository,
    ) -> None:
        self.summary_service = summary_service
        self.transcripts_repository = transcripts_repository
        self.summaries_repository = summaries_repository

    async def summarize_video(self, db: Session, video_id: str) -> SummarizeResult:
        # Check transcript storage first so known videos skip the transcript provider
        transcript = self.transcripts_repository.get_by_video_id(db, video_id=video_id)

        if transcript is None:
            logger.info("Transcript cache miss for video_id=%s", video_id)
            # Normalize before hashing so equivalent transcript formatting reuses the same row
            transcript_text = normalize_transcript_text(
                fetch_transcript_text(video_id=video_id)
            )
            transcript = self.transcripts_repository.save_transcript(
                db,
                video_id=video_id,
                transcript_text=transcript_text,
                transcript_fingerprint=build_transcript_fingerprint(transcript_text),
            )
        else:
            logger.info("Transcript cache hit for video_id=%s", video_id)
            self.transcripts_repository.update_last_accessed(
                db, transcript_id=transcript.id
            )

        # Summary reuse depends on the stored transcript plus the active model and prompt version
        cached_record = self.summaries_repository.get_by_cache_key(
            db,
            transcript_id=transcript.id,
            model=self.summary_service.model,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )

        if cached_record is not None:
            logger.info("Summary cache hit for video_id=%s", video_id)
            self.summaries_repository.update_last_accessed(
                db,
                summary_id=cached_record.id,
            )
            return SummarizeResult(
                summary=cached_record.summary_text,
                cached=True,
                prompt_version=SUMMARY_PROMPT_VERSION,
            )

        logger.info("Summary cache miss for video_id=%s", video_id)
        # Only call OpenAI when no matching summary variant exists yet
        summary_text = await self.summary_service.summarize_transcript(
            transcript.transcript_text
        )
        saved_record = self.summaries_repository.save_summary(
            db,
            transcript_id=transcript.id,
            summary_text=summary_text,
            model=self.summary_service.model,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )

        return SummarizeResult(
            summary=saved_record.summary_text,
            cached=False,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )

    async def stream_summarize_video(
        self, db: Session, video_id: str
    ) -> AsyncIterator[StreamEvent]:
        # Keep transcript reuse aligned with the non-streaming path.
        transcript = self.transcripts_repository.get_by_video_id(db, video_id=video_id)

        if transcript is None:
            logger.info("Transcript cache miss for video_id=%s", video_id)
            yield {"type": "status", "message": "Fetching transcript..."}
            transcript_text = normalize_transcript_text(
                fetch_transcript_text(video_id=video_id)
            )
            transcript = self.transcripts_repository.save_transcript(
                db,
                video_id=video_id,
                transcript_text=transcript_text,
                transcript_fingerprint=build_transcript_fingerprint(transcript_text),
            )
        else:
            logger.info("Transcript cache hit for video_id=%s", video_id)
            self.transcripts_repository.update_last_accessed(
                db, transcript_id=transcript.id
            )

        yield {"type": "status", "message": "Checking cache..."}
        cached_record = self.summaries_repository.get_by_cache_key(
            db,
            transcript_id=transcript.id,
            model=self.summary_service.model,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )

        if cached_record is not None:
            logger.info("Summary cache hit for video_id=%s", video_id)
            self.summaries_repository.update_last_accessed(
                db,
                summary_id=cached_record.id,
            )
            yield {"type": "delta", "text": cached_record.summary_text}
            yield {
                "type": "done",
                "cached": True,
                "prompt_version": SUMMARY_PROMPT_VERSION,
            }
            return

        logger.info("Summary cache miss for video_id=%s", video_id)
        yield {"type": "status", "message": "Writing summary..."}
        summary_chunks = []
        async for chunk in self.summary_service.stream_summary_transcript(
            transcript.transcript_text
        ):
            summary_chunks.append(chunk)
            yield {"type": "delta", "text": chunk}

        summary_text = "".join(summary_chunks)
        self.summaries_repository.save_summary(
            db,
            transcript_id=transcript.id,
            summary_text=summary_text,
            model=self.summary_service.model,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        yield {
            "type": "done",
            "cached": False,
            "prompt_version": SUMMARY_PROMPT_VERSION,
        }
