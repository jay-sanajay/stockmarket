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
    In development, allow any port on localhost / 127.0.0.1 (Vite may use 5174+).
    Disabled when CORS_ORIGINS is set (explicit list) or in production.
    Starlette compiles this string and uses fullmatch() on the Origin header.
    """
    if is_production():
        return None
    if os.getenv("CORS_ORIGINS", "").strip():
        return None
    return r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod")


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()
