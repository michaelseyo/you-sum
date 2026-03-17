import os
import tempfile
import unittest

from app.clients.db import get_session, init_db
from app.repositories.transcripts_repository import TranscriptsRepository


class TranscriptsRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "summaries.db")
        self.original_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{self.database_path}"
        init_db()
        self.repository = TranscriptsRepository()

    def tearDown(self) -> None:
        if self.original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.original_database_url
        self.temp_dir.cleanup()

    def test_save_transcript_returns_saved_record(self) -> None:
        with get_session() as db:
            record = self.repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello",
                transcript_fingerprint="fingerprint-1",
            )

            self.assertEqual(record.video_id, "video-1")
            self.assertEqual(record.transcript_text, "hello")

    def test_save_transcript_respects_unique_video_id(self) -> None:
        with get_session() as db:
            first = self.repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello",
                transcript_fingerprint="fingerprint-1",
            )
            second = self.repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello updated",
                transcript_fingerprint="fingerprint-2",
            )

            self.assertEqual(first.id, second.id)
            self.assertEqual(second.transcript_text, "hello")

    def test_update_last_accessed_updates_timestamp(self) -> None:
        with get_session() as db:
            record = self.repository.save_transcript(
                db,
                video_id="video-1",
                transcript_text="hello",
                transcript_fingerprint="fingerprint-1",
            )

            self.repository.update_last_accessed(db, transcript_id=record.id)
            refreshed = self.repository.get_by_video_id(db, video_id="video-1")

            self.assertIsNotNone(refreshed)
