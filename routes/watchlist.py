"""User watchlists (auth required)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies.deps import get_current_user
from models.db_models import User, Watchlist, WatchlistItem
from services.analysis_service import run_analysis, stock_cache

router = APIRouter(prefix="/watchlists", tags=["watchlists"])

MAX_CARDS = 12


class CreateWatchlistBody(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class AddItemBody(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    pinned: bool = False


@router.get("")
def list_watchlists(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wls = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user.id)
        .order_by(Watchlist.sort_order, Watchlist.id)
        .all()
    )
    return [
        {
            "id": w.id,
            "name": w.name,
            "is_default": w.is_default,
            "item_count": len(w.items),
        }
        for w in wls
    ]


@router.post("")
def create_watchlist(
    body: CreateWatchlistBody,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    n = db.query(Watchlist).filter(Watchlist.user_id == user.id).count()
    wl = Watchlist(user_id=user.id, name=body.name.strip(), is_default=False, sort_order=n)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return {"id": wl.id, "name": wl.name}


@router.delete("/{watchlist_id}")
def delete_watchlist(
    watchlist_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if wl.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default watchlist")
    db.delete(wl)
    db.commit()
    return {"ok": True}


@router.post("/{watchlist_id}/items")
def add_item(
    watchlist_id: int,
    body: AddItemBody,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    sym = body.symbol.strip().upper()
    exists = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == wl.id, WatchlistItem.symbol == sym)
        .first()
    )
    if exists:
        exists.pinned = body.pinned
        db.commit()
        return {"ok": True, "symbol": sym}
    it = WatchlistItem(
        watchlist_id=wl.id,
        symbol=sym,
        pinned=body.pinned,
        sort_order=db.query(WatchlistItem).filter(WatchlistItem.watchlist_id == wl.id).count(),
    )
    db.add(it)
    db.commit()
    return {"ok": True, "symbol": sym}


@router.delete("/{watchlist_id}/items/{symbol:path}")
def remove_item(
    watchlist_id: int,
    symbol: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    sym = symbol.strip().upper()
    it = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == wl.id, WatchlistItem.symbol == sym)
        .first()
    )
    if it:
        db.delete(it)
        db.commit()
    return {"ok": True}


@router.get("/{watchlist_id}/cards")
def watchlist_cards(
    watchlist_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    items = sorted(wl.items, key=lambda x: (not x.pinned, x.sort_order, x.symbol))
    cards = []
    for it in items[:MAX_CARDS]:
        sym = it.symbol.upper()
        data = stock_cache.get(sym)
        if not data:
            try:
                data = run_analysis(sym)
            except Exception as e:
                cards.append({"symbol": sym, "error": str(e), "pinned": it.pinned})
                continue
        if isinstance(data, dict) and data.get("error"):
            cards.append({"symbol": sym, "error": data["error"], "pinned": it.pinned})
            continue
        ts = data.get("technical_snapshot") or {}
        ratios = data.get("ratios") or {}
        reason = data.get("strategy_reason") or ""
        cards.append(
            {
                "symbol": sym,
                "company": data.get("company"),
                "current_price": ratios.get("Current Price"),
                "verdict": data.get("strategy_type"),
                "sentiment": (data.get("news_sentiment") or "")[:160],
                "rsi": ts.get("rsi"),
                "trend": ts.get("trend"),
                "signal_score": data.get("signal_score"),
                "one_liner": reason[:200],
                "pinned": it.pinned,
            }
        )
    return {"watchlist_id": watchlist_id, "name": wl.name, "cards": cards}
