"""Google Gemini via google.generativeai."""

import logging
import time

import google.generativeai as genai

from config import get_gemini_api_key, get_gemini_model_preference

logger = logging.getLogger(__name__)

# Cache the last model name that worked (avoid retrying fallbacks every request).
_cached_model_name: str | None = None

# Order: newer first. Old `gemini-1.5-flash` often 404s on current API — do not use.
_MODEL_FALLBACKS = (
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash-8b",
)


def _model_candidates() -> list[str]:
    pref = get_gemini_model_preference()
    out: list[str] = []
    if pref:
        out.append(pref)
    for m in _MODEL_FALLBACKS:
        if m not in out:
            out.append(m)
    return out


def _should_try_next_model(exc: BaseException) -> bool:
    s = str(exc).lower()
    return (
        "404" in str(exc)
        or "not found" in s
        or "not supported" in s
        or "invalid model" in s
    )


def _is_rate_limit(exc: BaseException) -> bool:
    s = str(exc).lower()
    if "429" in str(exc) or "too many" in s:
        return True
    if "resource exhausted" in s or "quota" in s:
        return True
    if "rate" in s and ("limit" in s or "limited" in s):
        return True
    try:
        from google.api_core.exceptions import ResourceExhausted

        return isinstance(exc, ResourceExhausted)
    except ImportError:
        return False


_GEMINI_RATE_RETRIES = 4
_GEMINI_RATE_DELAYS = (1.5, 3.0, 6.0, 12.0)


def generate_text(prompt: str, context: str = "generate_text") -> str:
    """Generate text; tries multiple model IDs if Google returns 404 for deprecated names."""
    global _cached_model_name

    key = get_gemini_api_key()
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")

    genai.configure(api_key=key)

    candidates = _model_candidates()
    if _cached_model_name and _cached_model_name in candidates:
        candidates = [_cached_model_name] + [
            c for c in candidates if c != _cached_model_name
        ]

    last_error: BaseException | None = None

    for name in candidates:
        model = genai.GenerativeModel(name)
        for attempt in range(_GEMINI_RATE_RETRIES):
            try:
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

                _cached_model_name = name
                logger.info("Gemini OK (%s) model=%s", context, name)
                return text or "No response text from Gemini."
            except Exception as e:
                last_error = e
                if _is_rate_limit(e):
                    if attempt < _GEMINI_RATE_RETRIES - 1:
                        delay = _GEMINI_RATE_DELAYS[
                            min(attempt, len(_GEMINI_RATE_DELAYS) - 1)
                        ]
                        logger.warning(
                            "Gemini rate limit (%s) model=%s attempt %s/%s, sleep %.1fs",
                            context,
                            name,
                            attempt + 1,
                            _GEMINI_RATE_RETRIES,
                            delay,
                        )
                        time.sleep(delay)
                        continue
                    logger.warning(
                        "Gemini rate limit persists on model=%s (%s), trying next model",
                        name,
                        context,
                    )
                    break
                if _should_try_next_model(e):
                    logger.warning(
                        "Gemini model %s failed (%s), trying next: %s",
                        name,
                        context,
                        e,
                    )
                    break
                logger.exception("Gemini generate_content failed (%s): %s", context, e)
                raise

    logger.exception("All Gemini models exhausted (%s): %s", context, last_error)
    if last_error:
        raise last_error
    raise RuntimeError("No Gemini model available")
