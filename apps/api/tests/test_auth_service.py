import os
import tempfile
import unittest

import jwt
from app.clients.db import init_db
from app.clients.db import get_session as open_session
from app.repositories.users_repository import UsersRepository
from app.services.auth import (
    AuthService,
    AuthenticationError,
    AuthorizationError,
)


class AuthServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.temp_dir.name}/auth.db"
        os.environ["GOOGLE_CLIENT_ID"] = "google-client-id"
        os.environ["APP_JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256"
        os.environ["APP_JWT_EXPIRES_MINUTES"] = "60"
        os.environ["ALLOWED_EMAILS"] = "user@example.com"
        os.environ.pop("ENABLE_DEV_LOGIN", None)
        init_db()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        for name in (
            "ALLOWED_EMAILS",
            "APP_JWT_EXPIRES_MINUTES",
            "APP_JWT_SECRET",
            "DATABASE_URL",
            "ENABLE_DEV_LOGIN",
            "GOOGLE_CLIENT_ID",
        ):
            os.environ.pop(name, None)

    def test_verify_google_id_token_returns_identity_for_valid_claims(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-1",
                "email": "User@example.com",
                "email_verified": True,
                "name": "Test User",
                "picture": "https://example.com/picture.png",
            },
        )

        identity = service.verify_google_id_token("token")

        self.assertEqual(identity.google_sub, "google-sub-1")
        self.assertEqual(identity.email, "user@example.com")
        self.assertEqual(identity.name, "Test User")
        self.assertEqual(identity.picture_url, "https://example.com/picture.png")

    def test_verify_google_id_token_rejects_invalid_issuer(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {
                "iss": "https://example.com",
                "sub": "google-sub-1",
                "email": "user@example.com",
                "email_verified": True,
            },
        )

        with self.assertRaisesRegex(AuthenticationError, "issuer is invalid"):
            service.verify_google_id_token("token")

    def test_verify_google_id_token_rejects_unverified_email(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-1",
                "email": "user@example.com",
                "email_verified": False,
            },
        )

        with self.assertRaisesRegex(AuthenticationError, "must be verified"):
            service.verify_google_id_token("token")

    def test_authenticate_google_user_rejects_non_allowlisted_email(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-2",
                "email": "other@example.com",
                "email_verified": True,
            },
        )

        with open_session() as db:
            with self.assertRaisesRegex(AuthorizationError, "not allowed"):
                service.authenticate_google_user(db, "token")

    def test_issue_access_token_and_authenticate_app_token_round_trip(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-1",
                "email": "user@example.com",
                "email_verified": True,
            },
        )

        with open_session() as db:
            user = service.authenticate_google_user(db, "token")
            issued_token = service.issue_access_token(user)
            authenticated_user = service.authenticate_app_token(
                db, issued_token.access_token
            )

        self.assertEqual(authenticated_user.id, user.id)
        self.assertEqual(authenticated_user.email, "user@example.com")

    def test_authenticate_app_token_rejects_expired_token(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {},
        )
        expired_token = jwt.encode(
            {"sub": "1", "exp": 1},
            os.environ["APP_JWT_SECRET"],
            algorithm="HS256",
        )

        with open_session() as db:
            with self.assertRaisesRegex(AuthenticationError, "has expired"):
                service.authenticate_app_token(db, expired_token)

    def test_authenticate_dev_user_requires_feature_flag(self) -> None:
        service = AuthService(
            users_repository=UsersRepository(),
            token_verifier=lambda _token, _request, _audience: {},
        )

        with open_session() as db:
            with self.assertRaisesRegex(AuthenticationError, "disabled"):
                service.authenticate_dev_user(db)
