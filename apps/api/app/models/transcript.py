from datetime import datetime

from app.clients.db import Base
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Transcript(Base):
    """Stored transcript for a single YouTube video."""

    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    transcript_text: Mapped[str] = mapped_column(Text)
    transcript_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # A transcript can have multiple summary variants across models and prompt versions
    summaries: Mapped[list["Summary"]] = relationship(  # noqa: F821
        back_populates="transcript",
        cascade="all, delete-orphan",
    )
