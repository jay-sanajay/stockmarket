"""User alerts."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies.deps import get_current_user
from models.db_models import AlertRule, User
from services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    alert_type: str = Field(
        description="price_above|price_below|rsi_above|rsi_below|verdict_changed|sentiment_changed"
    )
    threshold: dict | None = None
    active: bool = True


@router.get("")
def list_alerts(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.query(AlertRule).filter(AlertRule.user_id == user.id).order_by(AlertRule.id.desc()).all()
    return [
        {
            "id": r.id,
            "symbol": r.symbol,
            "alert_type": r.alert_type,
            "threshold": r.threshold,
            "active": r.active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
        }
        for r in rows
    ]


@router.post("")
def create_alert(
    body: AlertCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    sym = body.symbol.strip().upper()
    r = AlertRule(
        user_id=user.id,
        symbol=sym,
        alert_type=body.alert_type.strip(),
        threshold=body.threshold,
        active=body.active,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id}


class AlertPatch(BaseModel):
    active: bool | None = None
    threshold: dict | None = None


@router.patch("/{alert_id}")
def patch_alert(
    alert_id: int,
    body: AlertPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    r = db.query(AlertRule).filter(AlertRule.id == alert_id, AlertRule.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Alert not found")
    if body.active is not None:
        r.active = body.active
    if body.threshold is not None:
        r.threshold = body.threshold
    db.commit()
    return {"ok": True}


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    r = db.query(AlertRule).filter(AlertRule.id == alert_id, AlertRule.user_id == user.id).first()
    if r:
        db.delete(r)
        db.commit()
    return {"ok": True}


@router.post("/check-now")
def check_now(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    triggered = alert_service.check_user_alerts(db, user.id)
    return {"triggered": triggered, "count": len(triggered)}
