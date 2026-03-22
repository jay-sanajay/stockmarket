"""Google Gemini via google.generativeai."""

import logging

import google.generativeai as genai

from config import get_gemini_api_key

logger = logging.getLogger(__name__)

_model: genai.GenerativeModel | None = None


def _ensure_configured() -> genai.GenerativeModel:
    global _model
    if _model is not None:
        return _model
    key = get_gemini_api_key()
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")
    try:
        genai.configure(api_key=key)
        _model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Gemini model initialized: gemini-1.5-flash")
        return _model
    except Exception as e:
        logger.exception("Failed to configure Gemini: %s", e)
        raise


def generate_text(prompt: str, context: str = "generate_text") -> str:
    """Generate text; logs failures with context."""
    try:
        model = _ensure_configured()
        response = model.generate_content(prompt)
        text = ""
        try:
            text = (response.text or "").strip()
        except (ValueError, AttributeError) as e:
            logger.warning("Gemini response.text unavailable (%s): %s", context, e)
        if not text and getattr(response, "candidates", None):
            parts = []
            for c in response.candidates:
                if c.content and c.content.parts:
                    for p in c.content.parts:
                        if hasattr(p, "text") and p.text:
                            parts.append(p.text)
            text = "\n".join(parts).strip()
        return text or "No response text from Gemini."
    except Exception as e:
        logger.exception("Gemini generate_content failed (%s): %s", context, e)
        raise
