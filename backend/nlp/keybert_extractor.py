"""Keyphrase extraction using YAKE (Yet Another Keyword Extractor).

YAKE is a lightweight, statistical, unsupervised method — no model weights,
no GPU, no API calls. Replaces KeyBERT + sentence-transformers + torch.

YAKE scores: lower = more relevant. We invert to a 0-1 relevance scale.
"""

import logging

import yake

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Extractor instantiated once at module level ──────────────────
# n=3  → up to trigram keyphrases
# dedupLim=0.7 → suppress near-duplicate phrases
_extractor = yake.KeywordExtractor(
    lan="en",
    n=3,
    dedupLim=0.7,
    top=settings.KEYBERT_TOP_N,
    features=None,
)


def extract_keyphrases(text: str) -> list[dict]:
    """Extract top keyphrases from article text using YAKE.

    Input : text — cleaned article text
    Output: list of {"phrase": str, "relevance_score": float 0-1}
    Error : returns [] if text too short or on any failure
    """
    if len(text) < 50:
        logger.debug("Text too short for keyphrase extraction (%d chars)", len(text))
        return []

    try:
        raw = _extractor.extract_keywords(text)
        # raw = [(phrase, yake_score), ...] — lower yake_score = more relevant
        if not raw:
            return []
        # Normalise: invert so higher relevance_score = more important
        max_score = max(score for _, score in raw) or 1.0
        return [
            {"phrase": phrase, "relevance_score": round(1 - (score / max_score), 4)}
            for phrase, score in raw
        ]
    except Exception as e:
        logger.error("Keyphrase extraction failed: %s", e)
        return []
