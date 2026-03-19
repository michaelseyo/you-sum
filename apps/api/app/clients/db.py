from collections.abc import Generator

from app.config import get_database_url as get_configured_database_url
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_ENGINES: dict[str, Engine] = {}
_SESSION_FACTORIES: dict[str, sessionmaker[Session]] = {}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def get_database_url() -> str:
    """Return the configured database URL for the current environment."""
    return get_configured_database_url()


def _engine_options(database_url: str) -> dict:
    options: dict = {"future": True}

    # SQLite needs an extra flag so the same database can be reused across threads in tests
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}

    return options


def get_engine() -> Engine:
    """Create or reuse an engine for the active database URL."""
    database_url = get_database_url()
    engine = _ENGINES.get(database_url)
    if engine is None:
        engine = create_engine(database_url, **_engine_options(database_url))
        _ENGINES[database_url] = engine

    return engine


def get_session_factory() -> sessionmaker[Session]:
    """Create or reuse the session factory bound to the active engine."""
    database_url = get_database_url()
    session_factory = _SESSION_FACTORIES.get(database_url)
    if session_factory is None:
        session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            future=True,
        )
        _SESSION_FACTORIES[database_url] = session_factory

    return session_factory


def get_session() -> Session:
    """Open a plain SQLAlchemy session for repository and test usage."""
    return get_session_factory()()


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped session for FastAPI routes."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all ORM tables for the current database URL."""
    from app.models.summary import Summary  # noqa: F401
    from app.models.transcript import Transcript  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
