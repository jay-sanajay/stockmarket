"""Health and root endpoints."""

import os

from fastapi import APIRouter

from config import is_production
from schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/", response_model=dict)
def home():
    # Render sets RENDER=true; also treat explicit production env
    on_render = os.getenv("RENDER", "").lower() in ("true", "1")
    note = (
        "Vercel: set VITE_API_BASE_URL to this origin (no trailing slash). Paths: /docs, /health, /analyze."
        if (on_render or is_production())
        else "Local dev: http://127.0.0.1:8000 (not 0.0.0.0)."
    )
    return {
        "status": "ok",
        "message": "Stock Analyzer API is live 🚀",
        "docs": "/docs",
        "health": "/health",
        "note": note,
    }


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        environment="production" if is_production() else "development",
    )
