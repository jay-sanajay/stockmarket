"""Detect upstream (Yahoo, Gemini, etc.) rate-limit style errors from exception chains."""


def exception_chain_text(exc: BaseException, max_depth: int = 8) -> str:
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


def looks_like_upstream_rate_limit(exc: BaseException) -> bool:
    try:
        from google.api_core.exceptions import ResourceExhausted

        if isinstance(exc, ResourceExhausted):
            return True
    except ImportError:
        pass

    s = exception_chain_text(exc)
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
