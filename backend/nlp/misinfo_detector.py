"""Misinformation suspicion scoring using HuggingFace fake-news model."""

import logging

from transformers import pipeline as hf_pipeline

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Model loaded once, cached at module level ────────────────────
_misinfo_model = None


def load_misinfo_model():
    """Load the fake-news detection model once and cache it.

    Input : None
    Output: HuggingFace pipeline
    """
    global _misinfo_model
    if _misinfo_model is None:
        _misinfo_model = hf_pipeline(
            "text-classification",
            model="mrm8488/bert-tiny-finetuned-fake-news-detection",
            truncation=True,
            max_length=512,
        )
        logger.info("Misinfo model loaded: mrm8488/bert-tiny-finetuned-fake-news-detection")
    return _misinfo_model


def score_misinfo(text: str) -> dict:
    """Score article for misinformation suspicion.

    Input : text — cleaned article text
    Output: {
        "suspicion_score": float 0-1,
        "should_flag": bool,
        "flag_reason": str
    }
    Error : returns suspicion_score=0.0, should_flag=False on failure
    """
    try:
        model = load_misinfo_model()
        result = model(text[:512])[0]
        label = result["label"].upper()
        confidence = result["score"]

        # FAKE → suspicion = confidence; REAL → suspicion = 1 - confidence
        if label == "FAKE":
            suspicion_score = round(confidence, 4)
        else:
            suspicion_score = round(1 - confidence, 4)

        should_flag = suspicion_score >= settings.MISINFO_THRESHOLD
        flag_reason = ""
        if should_flag:
            flag_reason = "Flagged for review — model detected potentially misleading content"

        return {
            "suspicion_score": suspicion_score,
            "should_flag": should_flag,
            "flag_reason": flag_reason,
        }

    except Exception as e:
        logger.error("Misinfo detection failed: %s", e)
        return {
            "suspicion_score": 0.0,
            "should_flag": False,
            "flag_reason": "",
        }
