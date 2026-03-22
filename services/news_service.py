"""NewsData.io + Gemini sentiment."""

import logging
from urllib.parse import quote

import requests

from config import get_newsdata_api_key, skip_gemini_for_sentiment
from services import gemini_service
from utils.rate_limit import looks_like_upstream_rate_limit

logger = logging.getLogger(__name__)


def _keyword_sentiment(headlines: list[str]) -> str:
    """Cheap fallback when Gemini is skipped or unavailable (no API call)."""
    text = " ".join(headlines).lower()
    pos_hits = sum(
        1
        for w in (
            "surge",
            "rally",
            "gain",
            "profit",
            "growth",
            "beat",
            "record",
            "high",
            "upgrade",
            "bull",
        )
        if w in text
    )
    neg_hits = sum(
        1
        for w in (
            "fall",
            "crash",
            "loss",
            "decline",
            "probe",
            "fraud",
            "cut",
            "downgrade",
            "bear",
            "slump",
        )
        if w in text
    )
    if pos_hits > neg_hits and pos_hits > 0:
        return f"Positive — quick scan of {len(headlines)} headlines (keywords)."
    if neg_hits > pos_hits and neg_hits > 0:
        return f"Negative — quick scan of {len(headlines)} headlines (keywords)."
    return f"Neutral — mixed or soft wording across {len(headlines)} headlines (keywords)."


def fetch_news_sentiment(stock_name: str, fallback_term: str = "Indian Stock Market"):
    """Return (sentiment_text, headlines). Logs API failures."""
    api_key = get_newsdata_api_key()
    if not api_key:
        logger.error("fetch_news_sentiment: NEWSDATA_API_KEY is not set")
        return "News unavailable (API key missing)", []

    try:
        q = quote(stock_name)
        url = (
            f"https://newsdata.io/api/1/news?apikey={api_key}&q={q}&country=in&language=en"
        )
        res = requests.get(url, timeout=15)
        if res.status_code == 429:
            logger.warning("NewsData rate limited for q=%s", stock_name)
            return (
                "News temporarily unavailable (provider rate limit). Treating sentiment as neutral.",
                [],
            )
        res.raise_for_status()
        data = res.json()
        headlines = [
            article["title"]
            for article in data.get("results", [])
            if article.get("title")
        ][:5]

        if not headlines:
            url2 = (
                f"https://newsdata.io/api/1/news?apikey={api_key}"
                f"&q={quote(fallback_term)}&country=in&language=en"
            )
            res2 = requests.get(url2, timeout=15)
            if res2.status_code == 429:
                logger.warning("NewsData rate limited fallback query")
                return (
                    "News temporarily unavailable (provider rate limit). Treating sentiment as neutral.",
                    [],
                )
            res2.raise_for_status()
            data2 = res2.json()
            headlines = [
                article["title"]
                for article in data2.get("results", [])
                if article.get("title")
            ][:5]

        if not headlines:
            return "No news available", []

        if skip_gemini_for_sentiment():
            logger.info("SKIP_GEMINI_SENTIMENT: keyword sentiment for %s", stock_name)
            return _keyword_sentiment(headlines), headlines

        joined = "\n- ".join(headlines)
        prompt = f"""
You are a financial news analyst. Given these headlines related to {stock_name}, determine the overall market sentiment.

Headlines:
- {joined}

Classify sentiment as one of the following:
1. Positive
2. Negative
3. Neutral

Write the sentiment as a one-word summary first, followed by a brief reason based on patterns in the headlines.
"""
        try:
            sentiment = gemini_service.generate_text(
                prompt, context="fetch_news_sentiment"
            ).strip()
        except Exception as e:
            logger.exception("Sentiment Gemini call failed: %s", e)
            if looks_like_upstream_rate_limit(e):
                return _keyword_sentiment(headlines), headlines
            return f"Sentiment analysis error: {e}", headlines

        return sentiment, headlines
    except Exception as e:
        logger.exception("fetch_news_sentiment failed: %s", e)
        return f"News fetch error: {e}", []
