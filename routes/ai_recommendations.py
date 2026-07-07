"""REST API endpoints for AI Analyst Recommendations."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from services.ai_recommendations_service import get_ai_recommendations

router = APIRouter(prefix="/prediction", tags=["ai-recommendations"])

@router.get("/ai-recommendations", response_model=List[Dict[str, Any]])
async def get_recommendations():
    """Get high-potential stock recommendations based on time horizons."""
    try:
        recommendations = await get_ai_recommendations()
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
