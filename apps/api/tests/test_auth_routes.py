import importlib
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def load_main_module(*, enable_dev_login: bool = False):
    temp_dir = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_dir.name}/app.db"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["GOOGLE_CLIENT_ID"] = "google-client-id"
    os.environ["APP_JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256"
    os.environ["APP_JWT_EXPIRES_MINUTES"] = "60"
    os.environ["ALLOWED_EMAILS"] = "user@example.com"
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"
    os.environ["ENABLE_DEV_LOGIN"] = "true" if enable_dev_login else "false"
    sys.modules.pop("app.dependencies.auth", None)
    sys.modules.pop("main", None)
    module = importlib.import_module("main")
    return temp_dir, module


class AuthRoutesTestCase(unittest.TestCase):
    def tearDown(self) -> None:
        for name in (
            "ALLOWED_EMAILS",
            "ALLOWED_ORIGINS",
            "APP_JWT_EXPIRES_MINUTES",
            "APP_JWT_SECRET",
            "DATABASE_URL",
            "ENABLE_DEV_LOGIN",
            "GOOGLE_CLIENT_ID",
            "OPENAI_API_KEY",
        ):
            os.environ.pop(name, None)
        sys.modules.pop("app.dependencies.auth", None)
        sys.modules.pop("main", None)

    def test_google_auth_returns_access_token_for_allowlisted_user(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            with patch.object(
                main_module.auth_service,
                "verify_google_id_token",
                return_value=type(
                    "Identity",
                    (),
                    {
                        "google_sub": "google-sub-1",
                        "email": "user@example.com",
                        "name": "User One",
                        "picture_url": "https://example.com/avatar.png",
                    },
                )(),
            ):
                response = client.post(
                    "/auth/google", json={"id_token": "google-token"}
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["token_type"], "bearer")
        self.assertEqual(payload["user"]["email"], "user@example.com")
        self.assertTrue(payload["access_token"])
        self.assertNotIn("expires_in", payload)
        self.assertGreaterEqual(
            payload["expires_at"],
            int(datetime.now(timezone.utc).timestamp()),
        )

    def test_google_auth_rejects_invalid_google_token(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        from app.services.auth import AuthenticationError

        with TestClient(main_module.app) as client:
            with patch.object(
                main_module.auth_service,
                "verify_google_id_token",
                side_effect=AuthenticationError("Invalid Google ID token."),
            ):
                response = client.post("/auth/google", json={"id_token": "bad-token"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid Google ID token.")

    def test_google_auth_rejects_non_allowlisted_user(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            with patch.object(
                main_module.auth_service,
                "verify_google_id_token",
                return_value=type(
                    "Identity",
                    (),
                    {
                        "google_sub": "google-sub-2",
                        "email": "other@example.com",
                        "name": None,
                        "picture_url": None,
                    },
                )(),
            ):
                response = client.post(
                    "/auth/google", json={"id_token": "google-token"}
                )

        self.assertEqual(response.status_code, 403)

    def test_me_rejects_missing_token(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            response = client.get("/me")

        self.assertEqual(response.status_code, 401)

    def test_dev_login_route_exists_only_when_enabled(self) -> None:
        temp_dir_disabled, main_disabled = load_main_module(enable_dev_login=False)
        self.addCleanup(temp_dir_disabled.cleanup)
        with TestClient(main_disabled.app) as client:
            disabled_response = client.post("/auth/dev-login", json={})

        self.assertEqual(disabled_response.status_code, 404)

        temp_dir_enabled, main_enabled = load_main_module(enable_dev_login=True)
        self.addCleanup(temp_dir_enabled.cleanup)
        with TestClient(main_enabled.app) as client:
            enabled_response = client.post("/auth/dev-login", json={})

        self.assertEqual(enabled_response.status_code, 200)
        self.assertTrue(enabled_response.json()["access_token"])

    def test_summarize_rejects_missing_token(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            response = client.post("/summarize", json={"video_id": "video-1"})

        self.assertEqual(response.status_code, 401)

    def test_summarize_stream_rejects_missing_token(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            response = client.post("/summarize/stream", json={"video_id": "video-1"})

        self.assertEqual(response.status_code, 401)

    def test_summarize_succeeds_with_valid_dev_token(self) -> None:
        temp_dir, main_module = load_main_module(enable_dev_login=True)
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            login_response = client.post("/auth/dev-login", json={})
            access_token = login_response.json()["access_token"]

            with patch.object(
                main_module.summarize_orchestrator,
                "summarize_video",
                AsyncMock(
                    return_value=type(
                        "Result",
                        (),
                        {
                            "summary": "cached summary",
                            "cached": True,
                            "prompt_version": "v1",
                        },
                    )()
                ),
            ) as summarize_mock:
                response = client.post(
                    "/summarize",
                    json={"video_id": "video-1"},
                    headers={"Authorization": f"Bearer {access_token}"},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"], "cached summary")
        self.assertEqual(summarize_mock.await_count, 1)

    def test_summarize_stream_succeeds_with_valid_dev_token(self) -> None:
        temp_dir, main_module = load_main_module(enable_dev_login=True)
        self.addCleanup(temp_dir.cleanup)

        async def fake_stream(_db, _video_id):
            yield {"type": "delta", "text": "hello"}
            yield {"type": "done", "cached": False, "prompt_version": "v1"}

        with TestClient(main_module.app) as client:
            login_response = client.post("/auth/dev-login", json={})
            access_token = login_response.json()["access_token"]

            with patch.object(
                main_module.summarize_orchestrator,
                "stream_summarize_video",
                fake_stream,
            ):
                response = client.post(
                    "/summarize/stream",
                    json={"video_id": "video-1"},
                    headers={"Authorization": f"Bearer {access_token}"},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["content-type"], "text/event-stream; charset=utf-8"
        )
        self.assertEqual(
            response.text,
            "event: delta\n"
            'data: {"text":"hello"}\n\n'
            "event: done\n"
            'data: {"cached":false,"prompt_version":"v1"}\n\n',
        )
