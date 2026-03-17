from datetime import datetime, timezone

from app.models.summary import Summary
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class SummariesRepository:
    def get_by_cache_key(
        self,
        db: Session,
        *,
        transcript_id: int,
        model: str,
        prompt_version: str,
    ) -> Summary | None:
        # A summary cache hit depends on the transcript, model, and prompt version
        statement = select(Summary).where(
            Summary.transcript_id == transcript_id,
            Summary.model == model,
            Summary.prompt_version == prompt_version,
        )
        return db.scalar(statement)

    def save_summary(
        self,
        db: Session,
        *,
        transcript_id: int,
        summary_text: str,
        model: str,
        prompt_version: str,
    ) -> Summary:
        # Save one summary variant per transcript and summarization configuration
        summary = Summary(
            transcript_id=transcript_id,
            summary_text=summary_text,
            model=model,
            prompt_version=prompt_version,
        )
        db.add(summary)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            saved_record = self.get_by_cache_key(
                db,
                transcript_id=transcript_id,
                model=model,
                prompt_version=prompt_version,
            )
            if saved_record is None:
                raise RuntimeError("Failed to persist summary cache entry") from None
            return saved_record

        db.refresh(summary)
        return summary

    def update_last_accessed(self, db: Session, *, summary_id: int) -> None:
        # Track when a summary cache entry was last reused
        summary = db.get(Summary, summary_id)
        if summary is None:
            return

        summary.last_accessed_at = datetime.now(timezone.utc)
        db.commit()
