"""GET /entities/top — top organizations, locations, and animals."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from db.database import get_supabase

router = APIRouter()


def _top_by_type(entity_type: str, since: datetime, limit: int):
    """Return top entities of a given type via RPC."""
    sb = get_supabase()
    result = sb.rpc("rpc_top_entities", {
        "p_type": entity_type,
        "p_since": since.isoformat(),
        "p_limit": limit,
    }).execute()
    return [{"name": r["name"], "count": r["count"]} for r in result.data]


@router.get("/top")
def get_top_entities(
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(5, description="Top N per entity type"),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    return {
        "organizations": _top_by_type("ORG", since, limit),
        "locations": _top_by_type("GPE", since, limit),
        "animals": _top_by_type("ANIMAL", since, limit),
    }
