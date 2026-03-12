"""Sentiment analysis via HuggingFace Inference API (cardiffnlp model)."""

import logging

from nlp.hf_api import hf_infer

logger = logging.getLogger(__name__)

_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Normalise whatever label the model returns to our three standard values
_LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "label_0": "negative",
    "label_1": "neutral",
    "label_2": "positive",
}


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of article text via HuggingFace Inference API.

    Input : text — cleaned article text
    Output: {"label": "positive"|"negative"|"neutral", "score": float 0-1}
    Error : returns {"label": "neutral", "score": 0.0} on any failure
    """
    try:
        # API returns [[{"label": ..., "score": ...}, ...]] — take the top result
        result = hf_infer(_MODEL, {"inputs": text[:512]})
        top = result[0][0]
        raw_label = top["label"].lower()
        label = _LABEL_MAP.get(raw_label, raw_label)
        return {"label": label, "score": round(top["score"], 4)}
    except Exception as e:
        logger.error("Sentiment analysis failed: %s", e)
        return {"label": "neutral", "score": 0.0}
