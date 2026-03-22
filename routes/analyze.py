"""Stock analysis endpoint."""

import logging
import re

from fastapi import APIRouter, HTTPException, Query

from config import get_gemini_api_key, get_newsdata_api_key
from services.analysis_service import run_analysis

router = APIRouter(tags=["analyze"])

logger = logging.getLogger(__name__)

_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9.\-^]+$")


def _exception_chain_text(exc: BaseException, max_depth: int = 8) -> str:
    """Google / yfinance errors are often nested; str(top) may omit the rate-limit phrase."""
    parts: list[str] = []
    cur: BaseException | None = exc
    depth = 0
    while cur is not None and depth < max_depth:
        parts.append(str(cur))
        parts.extend(str(a) for a in getattr(cur, "args", ()) or ())
        for attr in ("message", "details"):
            if hasattr(cur, attr):
                parts.append(str(getattr(cur, attr, "")))
        resp = getattr(cur, "response", None)
        if resp is not None:
            parts.append(str(getattr(resp, "text", "") or ""))
            parts.append(str(getattr(resp, "reason", "") or ""))
        cur = cur.__cause__ or cur.__context__
        depth += 1
    return " ".join(parts).lower()


def _looks_like_upstream_rate_limit(exc: BaseException) -> bool:
    try:
        from google.api_core.exceptions import ResourceExhausted

        if isinstance(exc, ResourceExhausted):
            return True
    except ImportError:
        pass

    s = _exception_chain_text(exc)
    if "429" in s:
        return True
    if "too many" in s or "resource exhausted" in s:
        return True
    if "rate" in s and ("limit" in s or "limited" in s):
        return True
    if "try after" in s and "while" in s:
        return True
    if "quota" in s and ("exceed" in s or "exhaust" in s):
        return True
    return False


_RATE_LIMIT_USER_MSG = (
    "Data providers are busy (Yahoo Finance, Google AI, or news). "
    "Wait 2–3 minutes and try again — free tiers rate-limit shared IPs like Render."
)


def _validate_symbol(raw: str) -> str:
    s = raw.strip().upper()
    if not s:
        raise HTTPException(status_code=400, detail="Stock symbol cannot be empty.")
    if len(s) > 32:
        raise HTTPException(status_code=400, detail="Stock symbol is too long.")
    if not _SYMBOL_PATTERN.match(s):
        raise HTTPException(
            status_code=400,
            detail="Invalid symbol format. Use letters, digits, ., -, or ^ only.",
        )
    return s


@router.get(
    "/analyze",
    responses={
        400: {"description": "Bad request"},
        503: {"description": "Missing configuration or upstream timeout"},
        504: {"description": "Upstream data fetch timed out"},
        200: {
            "description": "Success, or {error: string} for invalid symbol / insufficient data (HTTP 200 so the SPA can read res.data.error without axios 404 noise)",
        },
    },
)
def analyze(
    stock: str = Query(
        ...,
        min_length=1,
        max_length=32,
        description="Ticker symbol, e.g. TCS.NS or RELIANCE.NS",
    ),
):
    """
    Full fundamental + technical + news analysis for a symbol.
    """
    symbol = _validate_symbol(stock)

    if not get_gemini_api_key():
        logger.error("analyze: GEMINI_API_KEY is not configured")
        raise HTTPException(
            status_code=503,
            detail="Server misconfiguration: GEMINI_API_KEY is not set.",
        )
    if not get_newsdata_api_key():
        logger.error("analyze: NEWSDATA_API_KEY is not configured")
        raise HTTPException(
            status_code=503,
            detail="Server misconfiguration: NEWSDATA_API_KEY is not set.",
        )

    try:
        result = run_analysis(symbol)
    except TimeoutError as e:
        logger.exception("analyze: timeout for %s: %s", symbol, e)
        raise HTTPException(
            status_code=504,
            detail="Market data request timed out. Try again in a moment.",
        ) from e
    except Exception as e:
        logger.exception("analyze: unexpected failure for %s: %s", symbol, e)
        if _looks_like_upstream_rate_limit(e):
            # HTTP 200 + {error} so axios succeeds and the SPA shows one clear banner (no console 500)
            return {"error": _RATE_LIMIT_USER_MSG}
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {e!s}",
        ) from e

    if isinstance(result, dict) and result.get("error"):
        logger.warning("analyze: business error for %s: %s", symbol, result["error"])
        # 200 + {error} so axios does not treat this as HTTP error (no console 404 spam)
        return {"error": result["error"]}

    return result
