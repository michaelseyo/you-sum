from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

import jwt
from app.config import (
    get_allowed_emails,
    get_app_jwt_expires_minutes,
    get_app_jwt_secret,
    get_google_client_id,
    is_dev_login_enabled,
)
from app.models.user import User
from app.repositories.users_repository import UsersRepository
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when the caller has not presented valid authentication."""


class AuthorizationError(Exception):
    """Raised when the caller is authenticated but not allowed to proceed."""


@dataclass(slots=True)
class VerifiedGoogleIdentity:
    google_sub: str
    email: str
    name: str | None
    picture_url: str | None


def normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None

    normalized_value = str(value).strip()
    return normalized_value or None


class AuthService:
    def __init__(
        self,
        *,
        users_repository: UsersRepository,
        google_request: GoogleRequest | None = None,
        token_verifier: Callable[[str, GoogleRequest, str], dict] | None = None,
    ) -> None:
        self.users_repository = users_repository
        self.google_client_id = get_google_client_id()
        self.jwt_secret = get_app_jwt_secret()
        self.jwt_expires_minutes = get_app_jwt_expires_minutes()
        self.allowed_emails = set(get_allowed_emails())
        self.dev_login_enabled = is_dev_login_enabled()
        self.google_request = google_request or GoogleRequest()
        self.token_verifier = token_verifier or google_id_token.verify_oauth2_token

    def verify_google_id_token(self, raw_token: str) -> VerifiedGoogleIdentity:
        try:
            claims = self.token_verifier(
                raw_token,
                self.google_request,
                self.google_client_id,
            )
        except ValueError as exc:
            logger.warning("Google ID token verification failed: %s", exc)
            raise AuthenticationError("Invalid Google ID token.") from exc

        issuer = claims.get("iss")
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            logger.warning("Google ID token rejected due to issuer=%s", issuer)
            raise AuthenticationError("Google token issuer is invalid.")

        google_sub = str(claims.get("sub", "")).strip()
        if not google_sub:
            logger.warning("Google ID token rejected because subject claim is missing")
            raise AuthenticationError("Google token subject is missing.")

        email = str(claims.get("email", "")).strip().lower()
        if not email:
            logger.warning("Google ID token rejected because email claim is missing")
            raise AuthenticationError("Google token email is missing.")

        if claims.get("email_verified") is not True:
            logger.warning(
                "Google ID token rejected because email is not verified for email=%s",
                email,
            )
            raise AuthenticationError("Google account email must be verified.")

        logger.info(
            "Verified Google ID token for email=%s google_sub=%s",
            email,
            google_sub,
        )

        name = claims.get("name")
        picture_url = claims.get("picture")

        return VerifiedGoogleIdentity(
            google_sub=google_sub,
            email=email,
            name=normalize_optional_string(name),
            picture_url=normalize_optional_string(picture_url),
        )

    def authenticate_google_user(self, db: Session, raw_token: str) -> User:
        identity = self.verify_google_id_token(raw_token)
        is_allowed = identity.email in self.allowed_emails
        user = self.users_repository.sync_google_user(
            db,
            google_sub=identity.google_sub,
            email=identity.email,
            name=identity.name,
            picture_url=identity.picture_url,
            is_allowed=is_allowed,
        )

        if not user.is_allowed:
            logger.warning(
                "Rejected Google sign-in for email=%s because it is not in ALLOWED_EMAILS",
                identity.email,
            )
            raise AuthorizationError("This Google account is not allowed to use the app.")

        logger.info("Authenticated Google user email=%s user_id=%s", user.email, user.id)
        return user

    def authenticate_dev_user(self, db: Session, email: str | None = None) -> User:
        if not self.dev_login_enabled:
            raise AuthenticationError("Dev login is disabled.")

        if email is None:
            for allowed_email in self.allowed_emails:
                normalized_email = allowed_email
                break
            else:
                raise AuthenticationError(
                    "ALLOWED_EMAILS must include at least one email when dev login is enabled."
                )
        else:
            normalized_email = email.strip().lower()

        logger.info("Authenticating dev user for email=%s", normalized_email)
        return self.users_repository.sync_google_user(
            db,
            google_sub=f"dev:{normalized_email}",
            email=normalized_email,
            name="Dev User",
            picture_url=None,
            is_allowed=True,
        )

    def issue_access_token(self, user: User) -> str:
        issued_at = datetime.now(timezone.utc)
        # timedelta defines how long the token should remain valid.
        expires_at = issued_at + timedelta(minutes=self.jwt_expires_minutes)
        payload = {
            # JWT standard claims:
            # sub = subject (our local user ID)
            # iat = issued at
            # exp = expiration time
            "sub": str(user.id),
            "email": user.email,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def authenticate_app_token(self, db: Session, token: str) -> User:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except ExpiredSignatureError as exc:
            raise AuthenticationError("App session has expired.") from exc
        except InvalidTokenError as exc:
            raise AuthenticationError("App session token is invalid.") from exc

        raw_subject = payload.get("sub")
        if raw_subject is None:
            raise AuthenticationError("App session token subject is missing.")

        try:
            user_id = int(raw_subject)
        except (TypeError, ValueError) as exc:
            raise AuthenticationError("App session token subject is invalid.") from exc

        user = self.users_repository.get_by_id(db, user_id=user_id)
        if user is None:
            logger.warning("App session token subject=%s did not map to a user", user_id)
            raise AuthenticationError("Authenticated user was not found.")

        if not user.is_allowed:
            logger.warning(
                "Rejected app session for email=%s because the account is not allowed",
                user.email,
            )
            raise AuthorizationError("This account is no longer allowed to use the app.")

        logger.info("Authenticated app session for email=%s user_id=%s", user.email, user.id)
        return user
