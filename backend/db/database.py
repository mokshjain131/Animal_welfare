"""Database clients — Supabase Python SDK and SQLAlchemy engine."""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# ── Supabase lazy singleton ───────────────────────────────────────────
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Create (once) and return the Supabase client.

    Raises ValueError when SUPABASE_URL or SUPABASE_KEY are not configured.
    """
    global _supabase_client
    if _supabase_client is None:
        from config.settings import settings
        if not settings.SUPABASE_URL:
            raise ValueError(
                "SUPABASE_URL is not set. "
                "Add it to your .env file (see .env.example)."
            )
        if not settings.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_KEY is not set. "
                "Add it to your .env file (see .env.example)."
            )
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


# ── SQLAlchemy lazy singleton ─────────────────────────────────────────
_engine = None


def get_engine():
    """Create (once) and return the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        from config.settings import settings
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
            if settings.DATABASE_URL.startswith("sqlite")
            else {},
        )
    return _engine


def create_all_tables() -> None:
    """Create all tables defined in db/models.py (idempotent)."""
    from db.models import Base
    Base.metadata.create_all(get_engine())


def get_session_factory():
    """Return a SQLAlchemy sessionmaker bound to the engine."""
    return sessionmaker(bind=get_engine())

