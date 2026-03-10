"""Keyphrase extraction using KeyBERT."""

import logging

from keybert import KeyBERT

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Model loaded once, cached at module level ────────────────────
_keybert_model: KeyBERT | None = None


def load_keybert_model() -> KeyBERT:
    """Load KeyBERT model once and cache it.

    Input : None
    Output: KeyBERT instance (uses sentence-transformers under the hood)
    """
    global _keybert_model
    if _keybert_model is None:
        _keybert_model = KeyBERT()
        logger.info("KeyBERT model loaded")
    return _keybert_model


def extract_keyphrases(text: str) -> list[dict]:
    """Extract top keyphrases from article text.

    Input : text — cleaned article text
    Output: list of {"phrase": str, "relevance_score": float 0-1}
    Error : returns [] if text too short or on any failure
    """
    if len(text) < 50:
        logger.debug("Text too short for keyphrase extraction (%d chars)", len(text))
        return []

    try:
        model = load_keybert_model()
        keywords = model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=settings.KEYBERT_TOP_N,
        )
        return [
            {"phrase": kw[0], "relevance_score": round(kw[1], 4)}
            for kw in keywords
        ]
    except Exception as e:
        logger.error("Keyphrase extraction failed: %s", e)
        return []
