import unittest

from app.prompts.summarize import SUMMARY_PROMPT_VERSION
from app.services.cache_keys import build_transcript_fingerprint
from app.services.summarize_orchestrator import SummarizeOrchestrator


class FakeSummaryService:
    def __init__(self) -> None:
        self.model = "gpt-5-mini"
        self.calls = 0

    async def summarize_transcript(self, transcript_text: str) -> str:
        self.calls += 1
        return f"summary:{transcript_text}"


class InMemoryTranscriptsRepository:
    def __init__(self) -> None:
        self.records = {}
        self.next_id = 1
        self.access_updates = 0

    def get_by_video_id(self, db, *, video_id: str):
        return self.records.get(video_id)

    def save_transcript(self, db, **kwargs):
        record = type(
            "Transcript",
            (),
            {
                "id": self.next_id,
                "video_id": kwargs["video_id"],
                "transcript_text": kwargs["transcript_text"],
                "transcript_fingerprint": kwargs["transcript_fingerprint"],
            },
        )()
        self.records[kwargs["video_id"]] = record
        self.next_id += 1
        return record

    def update_last_accessed(self, db, *, transcript_id: int) -> None:
        self.access_updates += 1


class InMemorySummariesRepository:
    def __init__(self) -> None:
        self.record = None
        self.access_updates = 0

    def get_by_cache_key(self, db, **kwargs):
        if self.record is None:
            return None

        cache_key = (
            kwargs["transcript_id"],
            kwargs["model"],
            kwargs["prompt_version"],
        )
        if cache_key == self.record["cache_key"]:
            return self.record["value"]

        return None

    def save_summary(self, db, **kwargs):
        value = type(
            "Summary",
            (),
            {
                "id": 1,
                "transcript_id": kwargs["transcript_id"],
                "summary_text": kwargs["summary_text"],
            },
        )()
        self.record = {
            "cache_key": (
                kwargs["transcript_id"],
                kwargs["model"],
                kwargs["prompt_version"],
            ),
            "value": value,
        }
        return value

    def update_last_accessed(self, db, *, summary_id: int) -> None:
        self.access_updates += 1


class SummarizeOrchestratorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_generates_and_caches_summary_on_first_request(self) -> None:
        summary_service = FakeSummaryService()
        transcripts_repository = InMemoryTranscriptsRepository()
        summaries_repository = InMemorySummariesRepository()
        orchestrator = SummarizeOrchestrator(
            summary_service=summary_service,
            transcripts_repository=transcripts_repository,
            summaries_repository=summaries_repository,
        )

        from unittest.mock import patch

        with patch(
            "app.services.summarize_orchestrator.fetch_transcript_text",
            return_value="hello world",
        ) as fetch_mock:
            result = await orchestrator.summarize_video(object(), "video-1")

        self.assertEqual(result.summary, "summary:hello world")
        self.assertFalse(result.cached)
        self.assertEqual(result.prompt_version, SUMMARY_PROMPT_VERSION)
        self.assertEqual(summary_service.calls, 1)
        self.assertEqual(fetch_mock.call_count, 1)

    async def test_reuses_stored_transcript_and_cached_summary_on_repeat_request(
        self,
    ) -> None:
        summary_service = FakeSummaryService()
        transcripts_repository = InMemoryTranscriptsRepository()
        summaries_repository = InMemorySummariesRepository()
        transcript_text = "hello world"
        transcript = transcripts_repository.save_transcript(
            object(),
            video_id="video-1",
            transcript_text=transcript_text,
            transcript_fingerprint=build_transcript_fingerprint(transcript_text),
        )
        summaries_repository.save_summary(
            object(),
            transcript_id=transcript.id,
            summary_text="cached summary",
            model="gpt-5-mini",
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        orchestrator = SummarizeOrchestrator(
            summary_service=summary_service,
            transcripts_repository=transcripts_repository,
            summaries_repository=summaries_repository,
        )

        from unittest.mock import patch

        with patch(
            "app.services.summarize_orchestrator.fetch_transcript_text",
            side_effect=AssertionError("Transcript fetch should be skipped"),
        ):
            result = await orchestrator.summarize_video(object(), "video-1")

        self.assertEqual(result.summary, "cached summary")
        self.assertTrue(result.cached)
        self.assertEqual(summary_service.calls, 0)
        self.assertEqual(transcripts_repository.access_updates, 1)
        self.assertEqual(summaries_repository.access_updates, 1)
