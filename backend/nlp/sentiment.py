"""Sentiment analysis using HuggingFace cardiffnlp model."""

import logging

from transformers import pipeline as hf_pipeline

logger = logging.getLogger(__name__)

# ── Model loaded once, cached at module level ────────────────────
_sentiment_model = None

# Map model labels to our standard labels
_LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    # Some models use LABEL_0/1/2
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}


def load_sentiment_model():
    """Load the sentiment analysis model once and cache it.

    Input : None
    Output: HuggingFace pipeline
    """
    global _sentiment_model
    if _sentiment_model is None:
        _sentiment_model = hf_pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            truncation=True,
            max_length=512,
        )
        logger.info("Sentiment model loaded: cardiffnlp/twitter-roberta-base-sentiment-latest")
    return _sentiment_model


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of article text.

    Input : text — cleaned article text
    Output: {"label": "positive"|"negative"|"neutral", "score": float 0-1}
    Error : returns {"label": "neutral", "score": 0.0} on any failure
    """
    try:
        model = load_sentiment_model()
        result = model(text[:512])[0]
        raw_label = result["label"].lower()
        label = _LABEL_MAP.get(raw_label, raw_label)
        return {"label": label, "score": round(result["score"], 4)}
    except Exception as e:
        logger.error("Sentiment analysis failed: %s", e)
        return {"label": "neutral", "score": 0.0}
