"""Technical indicators."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def compute_technicals(hist):
    hist = hist.copy()
    hist["MA50"] = hist["Close"].rolling(window=50).mean()
    hist["MA200"] = hist["Close"].rolling(window=200).mean()

    delta = hist["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    hist["RSI"] = 100 - (100 / (1 + rs))

    ema12 = hist["Close"].ewm(span=12, adjust=False).mean()
    ema26 = hist["Close"].ewm(span=26, adjust=False).mean()
    hist["MACD"] = ema12 - ema26
    hist["Signal"] = hist["MACD"].ewm(span=9, adjust=False).mean()

    hist["BB_MA"] = hist["Close"].rolling(window=20).mean()
    hist["BB_STD"] = hist["Close"].rolling(window=20).std()
    hist["Upper_BB"] = hist["BB_MA"] + 2 * hist["BB_STD"]
    hist["Lower_BB"] = hist["BB_MA"] - 2 * hist["BB_STD"]

    hist["Volume_Trend"] = hist["Volume"].pct_change().rolling(5).mean()
    return hist


def last_numeric(series, label: str) -> float | None:
    """Last valid numeric value from a series."""
    try:
        valid_series = series.dropna()
        if valid_series.empty:
            return None
        return float(valid_series.iloc[-1])
    except Exception as e:
        logger.warning("last_numeric failed for %s: %s", label, e)
        return None
