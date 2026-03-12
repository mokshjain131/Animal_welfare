"""Trending keywords — compares today's keyphrase frequency to 7-day baseline.

Only keyphrases that relate to animals or animal welfare are included.
Generic phrases (place names, company names, etc.) are filtered out.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from supabase import Client

from config.settings import settings
from config.keywords import get_all_keywords

logger = logging.getLogger(__name__)

# ── Animal-welfare relevance vocabulary ──────────────────────────
# A broad set of words that signal "this phrase is about animals / welfare".
# A keyphrase must contain at least one of these tokens to be kept.
_ANIMAL_TERMS: set[str] = {
    # General
    "animal", "animals", "creature", "creatures", "species",
    "wildlife", "wild", "habitat", "ecosystem",
    # Domestic
    "pet", "pets", "dog", "dogs", "cat", "cats", "puppy", "puppies",
    "kitten", "kittens", "horse", "horses", "livestock",
    # Farm
    "pig", "pigs", "cow", "cows", "calf", "calves", "cattle",
    "chicken", "chickens", "hen", "hens", "poultry", "broiler",
    "sheep", "lamb", "goat", "goats", "farm", "farming", "slaughter",
    "dairy", "meat", "egg", "eggs",
    # Wildlife
    "elephant", "rhino", "tiger", "lion", "whale", "dolphin",
    "shark", "bird", "birds", "fish", "penguin", "penguins",
    "primate", "ape", "monkey", "bear", "wolf", "wolves",
    "fox", "deer", "turtle", "tortoise", "reptile", "amphibian",
    "insect", "bee", "bees", "coral", "marine", "ocean",
    "endangered", "extinct", "extinction", "biodiversity",
    "poaching", "ivory", "trophy",
    # Welfare & policy
    "welfare", "cruelty", "abuse", "neglect", "suffering",
    "rescue", "shelter", "adoption", "euthanasia", "euthanize",
    "vegan", "veganism", "plant-based", "cruelty-free",
    "cage", "caged", "captive", "captivity", "zoo",
    "testing", "vivisection", "laboratory", "lab",
    "conservation", "protect", "protection", "ban",
    "rights", "humane", "inhumane",
}

# Also include every token in the existing topic keyword list
for _kw in get_all_keywords():
    for _token in _kw.lower().split():
        _ANIMAL_TERMS.add(_token)


def _is_animal_relevant(phrase: str) -> bool:
    """Return True if the phrase contains at least one animal-welfare term."""
    tokens = set(phrase.lower().split())
    return bool(tokens & _ANIMAL_TERMS)


def _get_phrase_counts(sb: Client, since: datetime) -> Counter:
    """Count keyphrase occurrences from articles published after `since`."""
    result = sb.rpc("rpc_keyphrase_counts", {
        "p_since": since.isoformat(),
    }).execute()

    return Counter({row["phrase"]: int(row["cnt"]) for row in result.data})


def compute_trending_keywords(sb: Client) -> None:
    """Compute which keyphrases are spiking recently vs the 7-day baseline.

    Uses a 3-day "recent" window (not just 24 hours) so that the table never
    goes stale when no new articles arrive.  Writes top results to the
    ``trending_keywords`` table.
    """
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=3)
    baseline_start = now - timedelta(days=7)

    recent_counts = _get_phrase_counts(sb, recent_start)
    baseline_counts = _get_phrase_counts(sb, baseline_start)

    # Always clear old rows first — prevents stale data from lingering
    sb.table("trending_keywords").delete().neq("id", 0).execute()

    if not recent_counts:
        logger.info("Trending keywords: no keyphrases in last 3 days, table cleared")
        return

    scored: list[dict] = []

    for phrase, recent_count in recent_counts.items():
        # Skip phrases that have nothing to do with animals / welfare
        if not _is_animal_relevant(phrase):
            continue

        baseline_total = baseline_counts.get(phrase, 0)
        baseline_avg = baseline_total / 7

        spike_score = recent_count / max(baseline_avg, 1)

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
            "article_count": recent_count,
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
