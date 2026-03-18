from datetime import datetime

from app.clients.db import Base
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Summary(Base):
    """Stored summary for one transcript, model, and prompt version."""

    __tablename__ = "summaries"
    __table_args__ = (UniqueConstraint("transcript_id", "model", "prompt_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    transcript_id: Mapped[int] = mapped_column(
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        index=True,
    )
    summary_text: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(255))
    prompt_version: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Link each summary variant back to the transcript it was generated from
    transcript: Mapped["Transcript"] = relationship(back_populates="summaries")  # noqa: F821
