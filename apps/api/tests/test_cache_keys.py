import unittest

from app.services.cache_keys import (
    build_transcript_fingerprint,
    normalize_transcript_text,
)


class CacheKeysTestCase(unittest.TestCase):
    def test_normalize_transcript_text_strips_empty_lines_and_whitespace(self) -> None:
        transcript_text = "  Hello world  \n\n  This is a test.   \n"

        normalized_text = normalize_transcript_text(transcript_text)

        self.assertEqual(normalized_text, "Hello world\nThis is a test.")

    def test_build_transcript_fingerprint_uses_normalized_content(self) -> None:
        left = "Hello world\nThis is a test."
        right = "  Hello world  \n\nThis is a test.  \n"

        self.assertEqual(
            build_transcript_fingerprint(left),
            build_transcript_fingerprint(right),
        )
