"""Misinformation suspicion scoring via HuggingFace Inference API."""

import logging

from config.settings import settings
from nlp.hf_api import hf_infer

logger = logging.getLogger(__name__)

_MODEL = "mrm8488/bert-tiny-finetuned-fake-news-detection"


def score_misinfo(text: str) -> dict:
    """Score article for misinformation suspicion via HuggingFace Inference API.

    Input : text — cleaned article text
    Output: {
        "suspicion_score": float 0-1,
        "should_flag": bool,
        "flag_reason": str
    }
    Error : returns suspicion_score=0.0, should_flag=False on failure
    """
    try:
        # API returns [[{"label": "FAKE"|"REAL", "score": ...}, ...]]
        result = hf_infer(_MODEL, {"inputs": text[:512]})
        top = result[0][0]
        label = top["label"].upper()
        confidence = top["score"]

        # FAKE → suspicion = confidence; REAL → suspicion = 1 - confidence
        suspicion_score = round(confidence if label == "FAKE" else 1 - confidence, 4)
        should_flag = suspicion_score >= settings.MISINFO_THRESHOLD
        flag_reason = (
            "Flagged for review — model detected potentially misleading content"
            if should_flag else ""
        )

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
