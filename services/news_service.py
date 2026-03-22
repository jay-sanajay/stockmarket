"""NewsData.io + Gemini sentiment."""

import logging
from urllib.parse import quote

import requests

from config import get_newsdata_api_key
from services import gemini_service

logger = logging.getLogger(__name__)


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
            res2.raise_for_status()
            data2 = res2.json()
            headlines = [
                article["title"]
                for article in data2.get("results", [])
                if article.get("title")
            ][:5]

        if not headlines:
            return "No news available", []

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
            return f"Sentiment analysis error: {e}", headlines

        return sentiment, headlines
    except Exception as e:
        logger.exception("fetch_news_sentiment failed: %s", e)
        return f"News fetch error: {e}", []
