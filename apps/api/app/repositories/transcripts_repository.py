from datetime import datetime, timezone

from app.models.transcript import Transcript
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class TranscriptsRepository:
    def get_by_video_id(self, db: Session, *, video_id: str) -> Transcript | None:
        # Reuse a stored transcript so we do not refetch it for known videos
        statement = select(Transcript).where(Transcript.video_id == video_id)
        return db.scalar(statement)

    def save_transcript(
        self,
        db: Session,
        *,
        video_id: str,
        transcript_text: str,
        transcript_fingerprint: str,
    ) -> Transcript:
        # Save the transcript once per video and reuse the canonical row on conflicts
        transcript = Transcript(
            video_id=video_id,
            transcript_text=transcript_text,
            transcript_fingerprint=transcript_fingerprint,
        )
        db.add(transcript)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            saved_record = self.get_by_video_id(db, video_id=video_id)
            if saved_record is None:
                raise RuntimeError("Failed to persist transcript cache entry") from None
            return saved_record

        db.refresh(transcript)
        return transcript

    def update_last_accessed(self, db: Session, *, transcript_id: int) -> None:
        # Track when a transcript cache entry was last reused
        transcript = db.get(Transcript, transcript_id)
        if transcript is None:
            return

        transcript.last_accessed_at = datetime.now(timezone.utc)
        db.commit()
