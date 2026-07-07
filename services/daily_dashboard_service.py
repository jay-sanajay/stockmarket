"""Aggregated daily market summary with TTL cache in DB."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import yfinance as yf

from models.db_models import DailySummaryCache
from config import get_gemini_api_key
from services import gemini_service, market_service, news_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_CACHE_SECONDS = 30 * 60
_BENCH = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS", "ITC.NS"]


def _utc_day_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _moves_from_yahoo() -> tuple[list[dict], list[dict]]:
    gainers: list[dict] = []
    losers: list[dict] = []
    for sym in _BENCH:
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if h is None or len(h) < 2:
                continue
            c0 = float(h["Close"].iloc[-2])
            c1 = float(h["Close"].iloc[-1])
            pct = (c1 - c0) / c0 * 100 if c0 else 0
            row = {"symbol": sym, "pct_change": round(pct, 2), "last": round(c1, 2)}
            if pct >= 0:
                gainers.append(row)
            else:
                losers.append(row)
        except Exception as e:
            logger.debug("bench %s: %s", sym, e)
    gainers.sort(key=lambda x: x["pct_change"], reverse=True)
    losers.sort(key=lambda x: x["pct_change"])
    return gainers[:5], losers[:5]


def build_daily_summary(db: Session, force_refresh: bool = False) -> dict:
    day_key = _utc_day_key()
    row = db.query(DailySummaryCache).filter(DailySummaryCache.day_key == day_key).first()
    if row and not force_refresh and row.created_at is not None:
        created = row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created).total_seconds()
        if age < _CACHE_SECONDS:
            return row.payload

    fii_dii = market_service.fetch_market_triggers()
    headlines = news_service.fetch_headlines_for_query("Indian stock market", 8)
    gainers, losers = _moves_from_yahoo()

    mood = "Neutral"
    if gainers and losers:
        avg_g = sum(g["pct_change"] for g in gainers[:3]) / min(3, len(gainers))
        avg_l = sum(abs(l["pct_change"]) for l in losers[:3]) / min(3, len(losers))
        if avg_g > avg_l * 1.2:
            mood = "Risk-on"
        elif avg_l > avg_g * 1.2:
            mood = "Cautious"

    top_opp = gainers[0]["symbol"] if gainers else "—"
    top_risk = losers[0]["symbol"] if losers else "—"

    ai_summary = ""
    opportunity = f"Largest 1d gain in sample: {top_opp}."
    risk = f"Largest 1d drop in sample: {top_risk}."

    if get_gemini_api_key() and headlines:
        try:
            hl = "\n".join(f"- {h}" for h in headlines[:6])
            prompt = f"""You are a concise Indian equity market assistant. Based on these headlines and a {mood} mood:
{hl}

Write 3 short sentences: (1) overall mood, (2) one opportunity, (3) one risk. Plain English, no investment advice."""
            ai_summary = gemini_service.generate_text(prompt, context="daily_summary").strip()
        except Exception as e:
            logger.warning("daily AI summary skipped: %s", e)
            ai_summary = "—"

    payload = {
        "day_key": day_key,
        "market_mood": mood,
        "fii_dii": fii_dii,
        "headlines": headlines,
        "top_gainers": gainers,
        "top_losers": losers,
        "trending_sectors": [],
        "ai_summary": ai_summary or "Summary unavailable (AI quota or rate limit).",
        "top_opportunity": opportunity,
        "top_risk": risk,
    }

    if row:
        row.payload = payload
        row.created_at = datetime.now(timezone.utc)
    else:
        db.add(DailySummaryCache(day_key=day_key, payload=payload))
    try:
        db.commit()
    except Exception as e:
        logger.warning("daily cache commit: %s", e)
        db.rollback()
    return payload
