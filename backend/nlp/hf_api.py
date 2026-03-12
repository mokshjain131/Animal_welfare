"""Shared HuggingFace Inference API client.

Handles auth, cold-start retries (HTTP 503), and consistent error logging.
All NLP modules import `hf_infer` from here instead of managing their own sessions.
"""

import logging
import time

import requests

from config.settings import settings

logger = logging.getLogger(__name__)

_HF_BASE = "https://router.huggingface.co/hf-inference/models"

# How long to wait between retries when the model is still loading
_RETRY_WAIT_SECONDS = 20
_MAX_RETRIES = 3


def hf_infer(model_id: str, payload: dict, timeout: int = 30) -> dict | list:
    """POST to the HuggingFace Inference API and return the parsed JSON response.

    Retries automatically on HTTP 503 (model loading / cold start).

    Input : model_id — e.g. "cardiffnlp/twitter-roberta-base-sentiment-latest"
            payload  — dict sent as JSON body ({"inputs": ..., "parameters": ...})
            timeout  — request timeout in seconds
    Output: parsed JSON — list or dict depending on the model type
    Raises: RuntimeError if all retries are exhausted or a non-retryable error occurs
    """
    url = f"{_HF_BASE}/{model_id}"
    headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.Timeout:
            raise RuntimeError(f"HF API timeout after {timeout}s for model {model_id}")
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"HF API request failed for model {model_id}: {exc}") from exc

        if response.status_code == 200:
            return response.json()

        # 503 = model is loading (cold start) — wait and retry
        if response.status_code == 503:
            estimated = response.json().get("estimated_time", _RETRY_WAIT_SECONDS)
            wait = min(float(estimated), 60.0)
            logger.warning(
                "HF model %s is loading (attempt %d/%d) — waiting %.0fs",
                model_id, attempt, _MAX_RETRIES, wait,
            )
            time.sleep(wait)
            continue

        # Any other non-200 status — fail immediately
        raise RuntimeError(
            f"HF API returned HTTP {response.status_code} for model {model_id}: {response.text[:200]}"
        )

    raise RuntimeError(f"HF model {model_id} still not ready after {_MAX_RETRIES} retries")
