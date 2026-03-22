"""Health and root endpoints."""

import os

from fastapi import APIRouter
from starlette.responses import Response

from config import is_production
from schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.head("/")
def home_head():
    """Render and some proxies use HEAD on / for health checks — avoid 405."""
    return Response(status_code=200)


@router.head("/health")
def health_head():
    return Response(status_code=200)


@router.get("/", response_model=dict)
def home():
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
