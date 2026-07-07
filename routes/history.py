"""Verdict history per symbol."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import VerdictRecord

router = APIRouter(prefix="/stocks", tags=["history"])


@router.get("/{symbol}/verdict-history")
def verdict_history(
    symbol: str,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=500)] = 120,
):
    sym = symbol.strip().upper()
    rows = (
        db.query(VerdictRecord)
        .filter(VerdictRecord.symbol == sym)
        .order_by(VerdictRecord.recorded_at.desc())
        .limit(limit)
        .all()
    )
    chronological = list(reversed(rows))
    records = [
        {
            "id": r.id,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            "price": r.price,
            "verdict": r.verdict,
            "signal_score": r.signal_score,
            "strategy_type": r.strategy_type,
            "news_sentiment": (r.news_sentiment or "")[:300] if r.news_sentiment else None,
        }
        for r in chronological
    ]

    change_summary = None
    if len(records) >= 2:
        prev, cur = records[-2], records[-1]
        if prev.get("strategy_type") != cur.get("strategy_type"):
            change_summary = (
                f"Verdict stance moved from {prev.get('strategy_type')} → {cur.get('strategy_type')}."
            )

    return {
        "symbol": sym,
        "records": records,
        "change_since_previous": change_summary,
    }
