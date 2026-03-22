"""Optional Perplexity API — only used when PERPLEXITY_API_KEY is set."""

import logging
import time

import requests

from config import get_perplexity_api_key

logger = logging.getLogger(__name__)


def call_perplexity(prompt: str, retries: int = 2) -> str:
    """
    Ask Perplexity. Returns a user-facing message if the key is missing or the call fails.
    """
    key = get_perplexity_api_key()
    if not key:
        logger.info("call_perplexity: PERPLEXITY_API_KEY not set; skipping")
        return "Perplexity is not configured (set PERPLEXITY_API_KEY to enable)."

    url = "https://api.perplexity.ai/v1/ask"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {"question": prompt, "model": "pro"}

    for attempt in range(retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("answer", "No answer from Perplexity")
        except requests.exceptions.Timeout:
            logger.warning("Perplexity timeout attempt %s", attempt)
            if attempt < retries:
                time.sleep(2)
                continue
            return "Timeout: Perplexity API took too long to respond."
        except Exception as e:
            logger.exception("call_perplexity failed: %s", e)
            return f"Error: {e!s}"
    return "Perplexity: max retries exceeded."
