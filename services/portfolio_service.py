"""Portfolio metrics from holdings + live prices."""

from __future__ import annotations

import logging

import yfinance as yf
from sqlalchemy.orm import Session

from models.db_models import Holding

logger = logging.getLogger(__name__)


def _last_price(symbol: str) -> float | None:
    try:
        t = yf.Ticker(symbol)
        info = t.info or {}
        p = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
        return float(p) if p is not None else None
    except Exception as e:
        logger.debug("price %s: %s", symbol, e)
        return None


def portfolio_summary(db: Session, user_id: int) -> dict:
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    positions = []
    total_invested = 0.0
    total_value = 0.0
    for h in holdings:
        cost = h.quantity * h.avg_buy_price
        px = _last_price(h.symbol.upper()) or h.avg_buy_price
        mv = h.quantity * px
        pnl = mv - cost
        total_invested += cost
        total_value += mv
        positions.append(
            {
                "id": h.id,
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_buy_price": h.avg_buy_price,
                "last_price": px,
                "market_value": round(mv, 2),
                "invested": round(cost, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round((pnl / cost * 100) if cost else 0, 2),
            }
        )
    positions.sort(key=lambda x: x["pnl"], reverse=True)
    winner = positions[0] if positions else None
    loser = positions[-1] if positions else None
    total_pnl = total_value - total_invested
    return {
        "total_invested": round(total_invested, 2),
        "total_value": round(total_value, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round((total_pnl / total_invested * 100) if total_invested else 0, 2),
        "positions": positions,
        "top_winner": winner,
        "top_loser": loser,
    }
