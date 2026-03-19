import os
import unittest

from app.config import (
    get_allowed_origin_regex,
    get_allowed_origins,
    get_database_url,
    get_openai_api_key,
)


class ConfigTestCase(unittest.TestCase):
    def tearDown(self) -> None:
        for name in (
            "ALLOWED_ORIGINS",
            "ALLOWED_ORIGIN_REGEX",
            "DATABASE_URL",
            "OPENAI_API_KEY",
        ):
            os.environ.pop(name, None)

    def test_get_database_url_requires_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is not set"):
            get_database_url()

    def test_get_openai_api_key_requires_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is not set"):
            get_openai_api_key()

    def test_get_allowed_origins_parses_comma_separated_list(self) -> None:
        os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000, chrome-extension://abc"

        self.assertEqual(
            get_allowed_origins(),
            ["http://localhost:3000", "chrome-extension://abc"],
        )

    def test_get_allowed_origin_regex_returns_none_when_unset(self) -> None:
        self.assertIsNone(get_allowed_origin_regex())

    def test_get_allowed_origin_regex_returns_trimmed_value(self) -> None:
        os.environ["ALLOWED_ORIGIN_REGEX"] = " chrome-extension://.* "

        self.assertEqual(get_allowed_origin_regex(), "chrome-extension://.*")
