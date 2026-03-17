import os
import tempfile
import unittest

from app.clients.db import get_session, init_db
from app.repositories.summaries_repository import SummariesRepository
from app.repositories.transcripts_repository import TranscriptsRepository


class SummariesRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "summaries.db")
        self.original_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{self.database_path}"
        init_db()
        self.transcripts_repository = TranscriptsRepository()
        self.repository = SummariesRepository()

    def tearDown(self) -> None:
        if self.original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.original_database_url
        self.temp_dir.cleanup()

    def test_save_summary_returns_saved_record(self) -> None:
        with get_session() as db:
            transcript = self.transcripts_repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello",
                transcript_fingerprint="fingerprint-1",
            )
            record = self.repository.save_summary(
                db,
                transcript_id=transcript.id,
                summary_text="summary",
                model="gpt-5-mini",
                prompt_version="v1",
            )

            self.assertEqual(record.transcript_id, transcript.id)
            self.assertEqual(record.summary_text, "summary")

    def test_save_summary_respects_unique_cache_key(self) -> None:
        with get_session() as db:
            transcript = self.transcripts_repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello",
                transcript_fingerprint="fingerprint-1",
            )
            first = self.repository.save_summary(
                db,
                transcript_id=transcript.id,
                summary_text="summary-1",
                model="gpt-5-mini",
                prompt_version="v1",
            )
            second = self.repository.save_summary(
                db,
                transcript_id=transcript.id,
                summary_text="summary-2",
                model="gpt-5-mini",
                prompt_version="v1",
            )

            self.assertEqual(first.id, second.id)
            self.assertEqual(second.summary_text, "summary-1")

    def test_update_last_accessed_updates_timestamp(self) -> None:
        with get_session() as db:
            transcript = self.transcripts_repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello",
                transcript_fingerprint="fingerprint-1",
            )
            record = self.repository.save_summary(
                db,
                transcript_id=transcript.id,
                summary_text="summary",
                model="gpt-5-mini",
                prompt_version="v1",
            )

            self.repository.update_last_accessed(db, summary_id=record.id)
            refreshed = self.repository.get_by_cache_key(
                db,
                transcript_id=transcript.id,
                model="gpt-5-mini",
                prompt_version="v1",
            )

            self.assertIsNotNone(refreshed)
