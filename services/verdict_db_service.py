"""Persist verdict snapshots to SQL (alongside legacy JSON log)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from database import SessionLocal
from models.db_models import VerdictRecord

logger = logging.getLogger(__name__)


def record_verdict_db(
    symbol: str,
    price: float | None,
    verdict: str,
    *,
    signal_score: float | None = None,
    strategy_type: str | None = None,
    news_sentiment: str | None = None,
    user_id: int | None = None,
) -> None:
    db = SessionLocal()
    try:
        row = VerdictRecord(
            user_id=user_id,
            symbol=symbol.upper().strip(),
            price=price,
            verdict=verdict,
            signal_score=signal_score,
            strategy_type=strategy_type,
            news_sentiment=news_sentiment,
        )
        db.add(row)
        db.commit()
    except Exception as e:
        logger.warning("record_verdict_db failed: %s", e)
        db.rollback()
    finally:
        db.close()


def migrate_json_verdict_log_if_present(db: Session) -> int:
    """Import verdict_log.json once when DB is empty."""
    if db.query(VerdictRecord).count() > 0:
        return 0
    path = Path("verdict_log.json")
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("migrate verdict json: %s", e)
        return 0
    if not isinstance(data, list):
        return 0
    n = 0
    for row in data:
        if not isinstance(row, dict):
            continue
        sym = row.get("symbol")
        if not sym:
            continue
        db.add(
            VerdictRecord(
                user_id=None,
                symbol=str(sym).upper(),
                price=float(row["price"]) if row.get("price") is not None else None,
                verdict=str(row.get("verdict", "")),
                signal_score=None,
                strategy_type=None,
                news_sentiment=None,
            )
        )
        n += 1
    try:
        db.commit()
    except Exception as e:
        logger.warning("migrate commit: %s", e)
        db.rollback()
        return 0
    return n
