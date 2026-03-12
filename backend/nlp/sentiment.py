"""Animal-welfare-aware sentiment via zero-shot classification (BART-MNLI).

Instead of generic Twitter sentiment, we use zero-shot classification with
animal-welfare-specific candidate labels so the model evaluates text
*through the lens of animal welfare*.

Output score is **directional** on a 0–1 scale:
    1.0 = very positive for animal welfare
    0.5 = neutral
    0.0 = very negative for animal welfare

This means ``AVG(score)`` in the daily-summary RPC is a meaningful aggregate.
"""

import logging

from nlp.hf_api import hf_infer

logger = logging.getLogger(__name__)

# Same model we already use for topic classification — no extra dependency.
_MODEL = "facebook/bart-large-mnli"

_CANDIDATE_LABELS = [
    "positive for animal welfare",
    "negative for animal welfare",
    "neutral regarding animal welfare",
]


def analyze_sentiment(text: str) -> dict:
    """Analyse sentiment of article text from an animal welfare perspective.

    Input : text — cleaned article text
    Output: {"label": "positive"|"negative"|"neutral", "score": float 0–1}
              where score is a directional value (1 = very positive, 0 = very negative)
    Error : returns {"label": "neutral", "score": 0.5} on any failure
    """
    try:
        result = hf_infer(
            _MODEL,
            {
                "inputs": text[:500],
                "parameters": {"candidate_labels": _CANDIDATE_LABELS},
            },
            timeout=120,
        )

        # HF API may return either format:
        #   dict:  {"labels": [...], "scores": [...]}
        #   list:  [{"label": ..., "score": ...}, ...]
        if isinstance(result, list):
            scores = {item["label"]: item["score"] for item in result}
        else:
            scores = dict(zip(result["labels"], result["scores"]))
        p_pos = scores.get("positive for animal welfare", 0)
        p_neg = scores.get("negative for animal welfare", 0)
        p_neu = scores.get("neutral regarding animal welfare", 0)

        # Directional score: 0 = very negative, 0.5 = neutral, 1.0 = very positive
        # Formula: weighted expectation across the three classes
        directional = round(p_pos * 1.0 + p_neu * 0.5 + p_neg * 0.0, 4)

        # Label = whichever class had the highest probability
        if p_pos >= p_neg and p_pos >= p_neu:
            label = "positive"
        elif p_neg >= p_pos and p_neg >= p_neu:
            label = "negative"
        else:
            label = "neutral"

        return {"label": label, "score": directional}

    except Exception as e:
        logger.error("Sentiment analysis failed: %s", e)
        return {"label": "neutral", "score": 0.5}
