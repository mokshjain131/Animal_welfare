"""Centralised configuration — all env vars, defaults, and thresholds."""

from pathlib import Path

from pydantic_settings import BaseSettings

# .env can live at backend/.env or project root — try both
_ENV_FILE_BACKEND = Path(__file__).resolve().parent.parent / ".env"
_ENV_FILE_ROOT = Path(__file__).resolve().parent.parent.parent / ".env"
_ENV_FILE = str(_ENV_FILE_BACKEND) if _ENV_FILE_BACKEND.exists() else str(_ENV_FILE_ROOT)


class Settings(BaseSettings):
    # ── Supabase ─────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # ── SQLAlchemy (local / test database) ───────────────────────
    DATABASE_URL: str = "sqlite:///./animal_welfare.db"

    # ── NewsAPI ──────────────────────────────────────────────────
    NEWSAPI_KEY: str = ""

    # ── RSS feeds to monitor ─────────────────────────────────────
    RSS_FEEDS: list[str] = [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://www.theguardian.com/environment/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Environment.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ]

    # ── NLP thresholds ───────────────────────────────────────────
    MISINFO_THRESHOLD: float = 0.65
    FALLBACK_TEXT_LENGTH: int = 150
    KEYBERT_TOP_N: int = 5
    TRENDING_KEYWORDS_TOP_N: int = 10

    # ── Spike detection ──────────────────────────────────────────
    SPIKE_MULTIPLIER: float = 2.0

    # ── Scheduler ────────────────────────────────────────────────
    PIPELINE_INTERVAL_MINUTES: int = 30

    # ── General ──────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
