"""Trending keywords — compares today's keyphrase frequency to 7-day baseline."""

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from supabase import Client

from config.settings import settings

logger = logging.getLogger(__name__)


def _get_phrase_counts(sb: Client, since: datetime) -> Counter:
    """Count keyphrase occurrences from articles published after `since`."""
    result = sb.rpc("rpc_keyphrase_counts", {
        "p_since": since.isoformat(),
    }).execute()

    return Counter({row["phrase"]: int(row["cnt"]) for row in result.data})


def compute_trending_keywords(sb: Client) -> None:
    """Compute which keyphrases are spiking today vs the 7-day baseline.

    Writes top results to the `trending_keywords` table.
    """
    now = datetime.now(timezone.utc)
    today_start = now - timedelta(hours=24)
    baseline_start = now - timedelta(days=7)

    today_counts = _get_phrase_counts(sb, today_start)
    baseline_counts = _get_phrase_counts(sb, baseline_start)

    if not today_counts:
        logger.info("Trending keywords: no keyphrases from today, skipping")
        return

    scored: list[dict] = []

    for phrase, today_count in today_counts.items():
        baseline_total = baseline_counts.get(phrase, 0)
        baseline_avg = baseline_total / 7

        spike_score = today_count / max(baseline_avg, 1)

        if baseline_total == 0:
            trend = "new"
        elif spike_score > 1.5:
            trend = "up"
        elif spike_score < 0.5:
            trend = "down"
        else:
            trend = "stable"

        scored.append({
            "phrase": phrase,
            "score": round(spike_score, 4),
            "article_count": today_count,
            "trend_direction": trend,
        })

    # Sort by spike_score descending, take top N
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[: settings.TRENDING_KEYWORDS_TOP_N]

    # Replace all existing rows
    sb.table("trending_keywords").delete().neq("id", 0).execute()

    if top:
        sb.table("trending_keywords").insert(top).execute()

    logger.info("Trending keywords: wrote %d phrases", len(top))
