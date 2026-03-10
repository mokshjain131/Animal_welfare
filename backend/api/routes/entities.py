"""GET /entities/top — top organizations, locations, and animals."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Article, Entity

router = APIRouter()


def _top_by_type(entity_type: str, since: datetime, limit: int, db: Session):
    """Return top entities of a given type."""
    rows = (
        db.query(
            Entity.entity_text,
            func.count(Entity.id).label("count"),
        )
        .join(Article, Article.id == Entity.article_id)
        .filter(
            Entity.entity_type == entity_type,
            Article.published_at >= since,
        )
        .group_by(Entity.entity_text)
        .order_by(func.count(Entity.id).desc())
        .limit(limit)
        .all()
    )
    return [{"name": r.entity_text, "count": r.count} for r in rows]


@router.get("/top")
def get_top_entities(
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(5, description="Top N per entity type"),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    return {
        "organizations": _top_by_type("ORG", since, limit, db),
        "locations": _top_by_type("GPE", since, limit, db),
        "animals": _top_by_type("ANIMAL", since, limit, db),
    }
