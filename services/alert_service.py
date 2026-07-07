"""Evaluate user alert rules against latest analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.db_models import AlertRule
from services.analysis_service import run_analysis, stock_cache

logger = logging.getLogger(__name__)


def _price(data: dict) -> float | None:
    r = data.get("ratios") or {}
    p = r.get("Current Price")
    try:
        return float(p) if p is not None else None
    except (TypeError, ValueError):
        return None


def _rsi(data: dict) -> float | None:
    ts = data.get("technical_snapshot") or {}
    v = ts.get("rsi")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def evaluate_alert(rule: AlertRule, data: dict) -> bool:
    if data.get("error"):
        return False
    th = rule.threshold or {}
    t = rule.alert_type
    if t == "price_above":
        p = _price(data)
        return p is not None and p >= float(th.get("price", 0))
    if t == "price_below":
        p = _price(data)
        return p is not None and p <= float(th.get("price", 0))
    if t == "rsi_above":
        r = _rsi(data)
        return r is not None and r >= float(th.get("rsi", 100))
    if t == "rsi_below":
        r = _rsi(data)
        return r is not None and r <= float(th.get("rsi", 0))
    if t == "verdict_changed":
        cur = data.get("strategy_type")
        prev = (rule.last_snapshot or {}).get("strategy_type")
        if prev is None:
            return False
        return cur is not None and prev != cur
    if t == "sentiment_changed":
        cur = (data.get("news_sentiment") or "")[:80]
        prev = (rule.last_snapshot or {}).get("sentiment_snippet")
        return prev is not None and cur != prev
    if t in ("ma_cross", "volatility_spike"):
        return False
    return False


def check_user_alerts(db: Session, user_id: int) -> list[dict]:
    rules = (
        db.query(AlertRule)
        .filter(AlertRule.user_id == user_id, AlertRule.active.is_(True))
        .limit(40)
        .all()
    )
    triggered: list[dict] = []
    now = datetime.now(timezone.utc)
    for rule in rules:
        sym = rule.symbol.upper()
        data = stock_cache.get(sym)
        if not data:
            try:
                data = run_analysis(sym)
            except Exception as e:
                logger.debug("alert skip %s: %s", sym, e)
                continue
        snap = {
            "strategy_type": data.get("strategy_type"),
            "sentiment_snippet": (data.get("news_sentiment") or "")[:80],
        }
        fired = evaluate_alert(rule, data)
        if fired:
            rule.last_triggered_at = now
            triggered.append(
                {
                    "alert_id": rule.id,
                    "symbol": sym,
                    "alert_type": rule.alert_type,
                    "message": f"{rule.alert_type} fired for {sym}",
                }
            )
        rule.last_snapshot = snap
    try:
        db.commit()
    except Exception as e:
        logger.warning("alert commit: %s", e)
        db.rollback()
    return triggered
