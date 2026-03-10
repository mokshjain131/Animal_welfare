"""GET /articles/recent and GET /articles/flagged."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import (
    Article, FlaggedArticle, SentimentScore, TopicClassification,
)

router = APIRouter()


@router.get("/recent")
def get_recent_articles(
    limit: int = Query(20, description="Max articles to return"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    sentiment: Optional[str] = Query(None, description="Filter: positive, negative, neutral"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Article,
            SentimentScore.label.label("sentiment_label"),
            SentimentScore.score.label("sentiment_score"),
            TopicClassification.topic.label("topic"),
        )
        .outerjoin(SentimentScore, SentimentScore.article_id == Article.id)
        .outerjoin(TopicClassification, TopicClassification.article_id == Article.id)
        .filter(Article.is_processed == True)
    )

    if topic:
        query = query.filter(TopicClassification.topic == topic)
    if sentiment:
        query = query.filter(SentimentScore.label == sentiment)
    if source:
        query = query.filter(Article.source_name.ilike(f"%{source}%"))

    query = query.order_by(Article.published_at.desc()).limit(limit)
    rows = query.all()

    # Check flagged status
    flagged_ids = set()
    if rows:
        article_ids = [r.Article.id for r in rows]
        flagged_rows = (
            db.query(FlaggedArticle.article_id)
            .filter(FlaggedArticle.article_id.in_(article_ids))
            .all()
        )
        flagged_ids = {f.article_id for f in flagged_rows}

    return {
        "articles": [
            {
                "id": r.Article.id,
                "title": r.Article.title,
                "url": r.Article.url,
                "source_name": r.Article.source_name,
                "published_at": r.Article.published_at.isoformat() if r.Article.published_at else None,
                "topic": r.topic,
                "sentiment_label": r.sentiment_label,
                "sentiment_score": round(float(r.sentiment_score or 0), 4),
                "is_flagged": r.Article.id in flagged_ids,
            }
            for r in rows
        ]
    }


@router.get("/flagged")
def get_flagged_articles(
    limit: int = Query(20, description="Max flagged articles to return"),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(FlaggedArticle, Article)
        .join(Article, Article.id == FlaggedArticle.article_id)
        .filter(FlaggedArticle.is_reviewed == False)
        .order_by(FlaggedArticle.suspicion_score.desc())
        .limit(limit)
        .all()
    )

    return {
        "articles": [
            {
                "id": r.Article.id,
                "title": r.Article.title,
                "url": r.Article.url,
                "source_name": r.Article.source_name,
                "suspicion_score": round(r.FlaggedArticle.suspicion_score, 4),
                "flag_reason": r.FlaggedArticle.flag_reason,
                "published_at": r.Article.published_at.isoformat() if r.Article.published_at else None,
            }
            for r in rows
        ]
    }
