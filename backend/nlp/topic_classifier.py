"""Zero-shot topic classification using HuggingFace BART-MNLI."""

import logging

from transformers import pipeline as hf_pipeline

from config.keywords import get_topic_labels, detect_topic_from_keywords

logger = logging.getLogger(__name__)

# ── Model loaded once, cached at module level ────────────────────
_topic_model = None


def load_topic_model():
    """Load the zero-shot classification model once and cache it.

    Input : None
    Output: HuggingFace pipeline
    """
    global _topic_model
    if _topic_model is None:
        _topic_model = hf_pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            truncation=True,
        )
        logger.info("Topic model loaded: facebook/bart-large-mnli")
    return _topic_model


def classify_topic(text: str) -> dict:
    """Classify article into an animal welfare topic category.

    Input : text — cleaned article text
    Output: {"topic": str, "confidence": float 0-1}
    Error : falls back to keyword-based detection, then "unknown"
    """
    labels = get_topic_labels()

    try:
        model = load_topic_model()
        # Use human-readable labels for better zero-shot results
        readable_labels = [label.replace("_", " ") for label in labels]
        result = model(text[:500], candidate_labels=readable_labels)
        top_label = result["labels"][0]
        top_score = round(result["scores"][0], 4)

        # Map back to snake_case topic name
        topic = top_label.replace(" ", "_")
        return {"topic": topic, "confidence": top_score}

    except Exception as e:
        logger.error("Topic classification failed: %s — using keyword fallback", e)
        fallback = detect_topic_from_keywords(text)
        return {"topic": fallback or "unknown", "confidence": 0.0}
