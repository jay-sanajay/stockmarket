"""Health and root endpoints."""

from fastapi import APIRouter

from config import is_production
from schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/", response_model=dict)
def home():
    return {
        "status": "ok",
        "message": "Stock Analyzer API is live 🚀",
        "docs": "/docs",
        "health": "/health",
        "note": "Open this API in your browser at http://127.0.0.1:8000 (or localhost:8000). "
        "Do not use http://0.0.0.0:8000 — browsers cannot load that address.",
    }


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        environment="production" if is_production() else "development",
    )
