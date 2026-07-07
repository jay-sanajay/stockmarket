"""Portfolio holdings."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import get_gemini_api_key
from database import get_db
from dependencies.deps import get_current_user
from models.db_models import Holding, User
from services import gemini_service
from services.portfolio_service import portfolio_summary

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class HoldingBody(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    quantity: float = Field(gt=0)
    avg_buy_price: float = Field(gt=0)


@router.get("/holdings")
def list_holdings(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.query(Holding).filter(Holding.user_id == user.id).all()
    return [
        {
            "id": h.id,
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_buy_price": h.avg_buy_price,
        }
        for h in rows
    ]


@router.post("/holdings")
def add_holding(
    body: HoldingBody,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    sym = body.symbol.strip().upper()
    h = Holding(
        user_id=user.id,
        symbol=sym,
        quantity=body.quantity,
        avg_buy_price=body.avg_buy_price,
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    return {"id": h.id}


@router.delete("/holdings/{holding_id}")
def delete_holding(
    holding_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    h = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user.id).first()
    if h:
        db.delete(h)
        db.commit()
    return {"ok": True}


@router.get("/summary")
def summary(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    data = portfolio_summary(db, user.id)
    ai = ""
    if get_gemini_api_key() and data["positions"]:
        try:
            lines = "\n".join(
                f"- {p['symbol']}: P/L {p['pnl']} ({p['pnl_pct']}%)"
                for p in data["positions"][:12]
            )
            prompt = f"""Briefly summarize this paper portfolio (not advice): 
{lines}
2 sentences: overall and one risk."""
            ai = gemini_service.generate_text(prompt, context="portfolio_summary").strip()
        except Exception:
            ai = ""
    data["ai_summary"] = ai or None
    return data
