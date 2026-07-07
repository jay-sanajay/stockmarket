"""Daily market summary (public; cached)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from services.daily_dashboard_service import build_daily_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/daily-summary")
def daily_summary(
    db: Annotated[Session, Depends(get_db)],
    refresh: Annotated[bool, Query(description="Bypass short TTL cache")] = False,
):
    return build_daily_summary(db, force_refresh=refresh)
