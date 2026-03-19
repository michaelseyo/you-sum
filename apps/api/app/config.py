import os


def get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear startup error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Configure it before starting the API.")

    return value


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
