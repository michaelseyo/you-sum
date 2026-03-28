import os


def get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear startup error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Configure it before starting the API.")

    return value


def get_required_int_env(name: str) -> int:
    """Return a required integer environment variable."""
    value = get_required_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid integer.") from exc


def get_database_url() -> str:
    """Return the database URL used by SQLAlchemy."""
    return get_required_env("DATABASE_URL")


def get_openai_api_key() -> str:
    """Return the OpenAI API key for summary generation."""
    return get_required_env("OPENAI_API_KEY")


def get_openai_model() -> str:
    """Return the configured OpenAI model for summary generation."""
    return os.getenv("OPENAI_MODEL", "gpt-5-mini")


def get_allowed_origins() -> list[str]:
    """Parse a comma-separated allowlist of exact CORS origins."""
    raw_value = os.getenv("ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def get_allowed_origin_regex() -> str | None:
    """Return the regex used for allowed origins such as extension IDs."""
    raw_value = os.getenv("ALLOWED_ORIGIN_REGEX", "").strip()
    return raw_value or None


def get_google_client_id() -> str:
    """Return the Google OAuth client ID used for OIDC verification."""
    return get_required_env("GOOGLE_CLIENT_ID")


def get_app_jwt_secret() -> str:
    """Return the shared secret used to sign app JWTs."""
    return get_required_env("APP_JWT_SECRET")


def get_app_jwt_expires_minutes() -> int:
    """Return the app JWT lifetime in minutes."""
    return get_required_int_env("APP_JWT_EXPIRES_MINUTES")


def get_allowed_emails() -> list[str]:
    """Parse the allowed email allowlist for personal/beta access."""
    raw_value = os.getenv("ALLOWED_EMAILS", "")
    return [email.strip().lower() for email in raw_value.split(",") if email.strip()]


def is_dev_login_enabled() -> bool:
    """Return whether the local dev-login route is enabled."""
    return os.getenv("ENABLE_DEV_LOGIN", "").strip().lower() in {"1", "true", "yes", "on"}
