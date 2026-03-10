from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# ── Lazy globals ─────────────────────────────────────────────────────
_engine = None
_session_factory = None


def get_engine():
    """Create (once) and return the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        from config.settings import settings
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_factory():
    """Create (once) and return a session factory bound to the engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session, closes it after use."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Create every table defined in models.py (if not already present)."""
    from db.models import Base
    Base.metadata.create_all(bind=get_engine())
