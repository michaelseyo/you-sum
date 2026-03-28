import os
import unittest

from app.config import (
    get_allowed_origin_regex,
    get_allowed_origins,
    get_allowed_emails,
    get_app_jwt_expires_minutes,
    get_app_jwt_secret,
    get_database_url,
    get_google_client_id,
    get_openai_api_key,
    get_openai_model,
    is_dev_login_enabled,
)


class ConfigTestCase(unittest.TestCase):
    def tearDown(self) -> None:
        for name in (
            "ALLOWED_ORIGINS",
            "ALLOWED_ORIGIN_REGEX",
            "ALLOWED_EMAILS",
            "APP_JWT_EXPIRES_MINUTES",
            "APP_JWT_SECRET",
            "DATABASE_URL",
            "ENABLE_DEV_LOGIN",
            "GOOGLE_CLIENT_ID",
            "OPENAI_API_KEY",
            "OPENAI_MODEL",
        ):
            os.environ.pop(name, None)

    def test_get_database_url_requires_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is not set"):
            get_database_url()

    def test_get_openai_api_key_requires_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is not set"):
            get_openai_api_key()

    def test_get_openai_model_defaults_to_gpt_5_mini(self) -> None:
        self.assertEqual(get_openai_model(), "gpt-5-mini")

    def test_get_openai_model_uses_override(self) -> None:
        os.environ["OPENAI_MODEL"] = "gpt-4.1-mini"

        self.assertEqual(get_openai_model(), "gpt-4.1-mini")

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

    def test_get_google_client_id_requires_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "GOOGLE_CLIENT_ID is not set"):
            get_google_client_id()

    def test_get_app_jwt_secret_requires_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "APP_JWT_SECRET is not set"):
            get_app_jwt_secret()

    def test_get_app_jwt_expires_minutes_requires_integer(self) -> None:
        os.environ["APP_JWT_EXPIRES_MINUTES"] = "abc"

        with self.assertRaisesRegex(
            RuntimeError,
            "APP_JWT_EXPIRES_MINUTES must be a valid integer.",
        ):
            get_app_jwt_expires_minutes()

    def test_get_allowed_emails_parses_comma_separated_list(self) -> None:
        os.environ["ALLOWED_EMAILS"] = " USER@example.com, beta@example.com "

        self.assertEqual(
            get_allowed_emails(),
            ["user@example.com", "beta@example.com"],
        )

    def test_is_dev_login_enabled_defaults_to_false(self) -> None:
        self.assertFalse(is_dev_login_enabled())

    def test_is_dev_login_enabled_parses_truthy_values(self) -> None:
        os.environ["ENABLE_DEV_LOGIN"] = "true"

        self.assertTrue(is_dev_login_enabled())
