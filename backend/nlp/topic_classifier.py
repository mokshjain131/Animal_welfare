"""Zero-shot topic classification via HuggingFace Inference API (BART-MNLI)."""

import logging

from config.keywords import get_topic_labels, detect_topic_from_keywords
from nlp.hf_api import hf_infer

logger = logging.getLogger(__name__)

_MODEL = "facebook/bart-large-mnli"


def classify_topic(text: str) -> dict:
    """Classify article into an animal welfare topic category.

    Calls the HuggingFace zero-shot-classification endpoint with the
    configured topic labels as candidate classes.

    Input : text — cleaned article text
    Output: {"topic": str, "confidence": float 0-1}
    Error : falls back to keyword-based detection, then "unknown"
    """
    labels = get_topic_labels()
    readable_labels = [label.replace("_", " ") for label in labels]

    try:
        # API may return dict {"labels": [...], "scores": [...]}
        # or list [{"label": ..., "score": ...}, ...]
        result = hf_infer(
            _MODEL,
            {"inputs": text[:500], "parameters": {"candidate_labels": readable_labels}},
        )

        if isinstance(result, list):
            top_label = result[0]["label"]
            top_score = round(result[0]["score"], 4)
        else:
            top_label = result["labels"][0]
            top_score = round(result["scores"][0], 4)

        topic = top_label.replace(" ", "_")
        return {"topic": topic, "confidence": top_score}

    except Exception as e:
        logger.error("Topic classification failed: %s — using keyword fallback", e)
        fallback = detect_topic_from_keywords(text)
        return {"topic": fallback or "unknown", "confidence": 0.0}
