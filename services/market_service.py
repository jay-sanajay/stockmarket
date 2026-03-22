"""NSE and market data helpers."""

import logging

import requests

logger = logging.getLogger(__name__)

UNAVAILABLE = "Market data unavailable"


def fetch_market_triggers() -> str:
    """
    FII/DII snapshot from NSE. On any failure returns a stable unavailable message
    (no stack traces to clients).
    """
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com/",
        }
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=8)
        res = session.get(url, timeout=8)
        res.raise_for_status()
        try:
            data = res.json()
        except ValueError as e:
            logger.warning("fetch_market_triggers: invalid JSON from NSE: %s", e)
            return UNAVAILABLE

        if not isinstance(data, dict) or "data" not in data or not data["data"]:
            logger.warning("fetch_market_triggers: unexpected NSE payload structure")
            return UNAVAILABLE

        latest = data["data"][-1]
        date = latest.get("date")
        fii_buy = latest.get("buyValue", "N/A")
        fii_sell = latest.get("sellValue", "N/A")
        dii_buy = latest.get("buyValueDii", "N/A")
        dii_sell = latest.get("sellValueDii", "N/A")

        def fmt(v):
            try:
                return f"{float(v):,.0f}"
            except (TypeError, ValueError):
                return str(v)

        return (
            f"📅 {date} | FII: Buy ₹{fmt(fii_buy)} Cr / Sell ₹{fmt(fii_sell)} Cr | "
            f"DII: Buy ₹{fmt(dii_buy)} Cr / Sell ₹{fmt(dii_sell)} Cr"
        )
    except Exception as e:
        logger.exception("fetch_market_triggers failed: %s", e)
        return UNAVAILABLE
