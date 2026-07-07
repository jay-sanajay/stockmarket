"""REST API endpoint for AI intraday stock picks."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from services.intraday_picks_service import get_intraday_picks

router = APIRouter(prefix="/prediction", tags=["intraday-picks"])


@router.get("/intraday-picks", response_model=List[Dict[str, Any]])
async def intraday_picks():
    """Get top 10 AI-powered intraday stock picks for today."""
    try:
        picks = await get_intraday_picks()
        return picks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
