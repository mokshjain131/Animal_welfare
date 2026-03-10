from datetime import datetime, date, timezone
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship


def _utcnow():
    return datetime.now(timezone.utc)

Base = declarative_base()


# ── Articles ─────────────────────────────────────────────────────────

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    full_text = Column(Text, nullable=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)          # "rss" | "newsapi"
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    is_processed = Column(Boolean, default=False)

    # relationships
    sentiment = relationship("SentimentScore", back_populates="article", uselist=False)
    topic = relationship("TopicClassification", back_populates="article", uselist=False)
    entities = relationship("Entity", back_populates="article")
    keyphrases = relationship("Keyphrase", back_populates="article")
    flagged = relationship("FlaggedArticle", back_populates="article", uselist=False)


# ── Sentiment ────────────────────────────────────────────────────────

class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    label = Column(String(20), nullable=False)                # positive | negative | neutral
    score = Column(Float, nullable=False)                     # 0–1 confidence
    created_at = Column(DateTime, default=_utcnow)

    article = relationship("Article", back_populates="sentiment")


# ── Topics ───────────────────────────────────────────────────────────

class TopicClassification(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    topic = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    article = relationship("Article", back_populates="topic")


# ── Entities ─────────────────────────────────────────────────────────

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    entity_text = Column(String(500), nullable=False)
    entity_type = Column(String(50), nullable=False)          # ORG | GPE | ANIMAL
    created_at = Column(DateTime, default=_utcnow)

    article = relationship("Article", back_populates="entities")


# ── Flagged Articles ─────────────────────────────────────────────────

class FlaggedArticle(Base):
    __tablename__ = "flagged_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, unique=True)
    suspicion_score = Column(Float, nullable=False)
    flag_reason = Column(String(500), nullable=True)
    is_reviewed = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    article = relationship("Article", back_populates="flagged")


# ── Keyphrases ───────────────────────────────────────────────────────

class Keyphrase(Base):
    __tablename__ = "keyphrases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    phrase = Column(String(500), nullable=False)
    relevance_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    article = relationship("Article", back_populates="keyphrases")


# ── Trending Keywords (overwritten every 30 min) ────────────────────

class TrendingKeyword(Base):
    __tablename__ = "trending_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phrase = Column(String(500), nullable=False)
    score = Column(Float, nullable=False)                     # TF-IDF spike score
    article_count = Column(Integer, nullable=False)
    trend_direction = Column(String(10), nullable=False)      # up | down | new
    topic = Column(String(100), nullable=True)
    computed_at = Column(DateTime, default=_utcnow)


# ── Daily Summaries (pre-computed rollups) ───────────────────────────

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    __table_args__ = (
        UniqueConstraint("date", "topic", name="uq_daily_summary_date_topic"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    topic = Column(String(100), nullable=False)
    article_count = Column(Integer, nullable=False)
    avg_sentiment = Column(Float, nullable=False)
    positive_count = Column(Integer, nullable=False)
    negative_count = Column(Integer, nullable=False)
    neutral_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


# ── Spike Events ────────────────────────────────────────────────────

class SpikeEvent(Base):
    __tablename__ = "spike_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(100), nullable=False)
    spike_date = Column(Date, nullable=False)
    article_count = Column(Integer, nullable=False)
    weekly_avg = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    detected_at = Column(DateTime, default=_utcnow)
