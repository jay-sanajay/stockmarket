"""Application configuration from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Always load .env from project root (folder containing this file), not only cwd
_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")


def get_gemini_api_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key or None


def get_gemini_model_preference() -> str | None:
    """Optional override, e.g. gemini-2.0-flash — see Google AI Studio model list."""
    m = os.getenv("GEMINI_MODEL", "").strip()
    return m or None


def get_newsdata_api_key() -> str | None:
    key = os.getenv("NEWSDATA_API_KEY", "").strip()
    return key or None


def get_perplexity_api_key() -> str | None:
    key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    return key or None


def get_cors_origins() -> list[str]:
    """Comma-separated origins from CORS_ORIGINS. No wildcards — list explicit hosts."""
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        # Vite default is :5173; CRA often :3000
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    return [o.strip() for o in raw.split(",") if o.strip()]


def get_cors_origin_regex() -> str | None:
    """
    Extra origins beyond allow_origins (OR logic in Starlette).
    - Render: allow all JayQuant Vercel hosts (production + preview), e.g.
      stockmarket-rho.vercel.app and stockmarket-xxx-jays-projects-xxx.vercel.app
    - Local dev: any port on localhost / 127.0.0.1 when CORS_ORIGINS is unset.
    Override with CORS_ORIGIN_REGEX (use \"none\" to disable).
    """
    custom = os.getenv("CORS_ORIGIN_REGEX", "").strip()
    if custom.lower() == "none":
        return None
    if custom:
        return custom

    if is_render_deployment() and os.getenv("CORS_VERCEL_REGEX", "1").lower() not in (
        "0",
        "false",
        "no",
    ):
        # Any *.vercel.app (preview + prod) — not only names starting with "stockmarket"
        return r"^https://[\w-]+\.vercel\.app$"

    if is_production():
        return None
    if os.getenv("CORS_ORIGINS", "").strip():
        return None
    return r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod")


def is_render_deployment() -> bool:
    """Render sets RENDER=true on web services — used for stricter upstream backoff defaults."""
    return os.getenv("RENDER", "").lower() in ("true", "1")


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_analysis_cache_ttl_seconds() -> float:
    """
    Longer TTL on Render reduces repeat Yahoo/Gemini/News hits from the same shared IP.
    Override with ANALYSIS_CACHE_TTL (seconds), e.g. 3600.
    """
    raw = os.getenv("ANALYSIS_CACHE_TTL", "").strip()
    if raw:
        return max(60.0, float(raw))
    return 3600.0 if is_render_deployment() else 300.0  # 1h on Render vs 5 min local


def skip_gemini_for_sentiment() -> bool:
    """
    If true, use keyword heuristic on headlines instead of a Gemini call — halves Gemini usage
    per /analyze (helps free-tier quotas on shared hosting IPs).
    On Render, defaults to **on** unless SKIP_GEMINI_SENTIMENT=0/false/no. Local dev defaults off.
    """
    raw = os.getenv("SKIP_GEMINI_SENTIMENT", "").strip().lower()
    if raw in ("0", "false", "no"):
        return False
    if raw in ("1", "true", "yes"):
        return True
    return is_render_deployment()
