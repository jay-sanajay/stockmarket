"""
FastAPI entrypoint for the stock analysis backend.
"""

from utils.logging_config import setup_logging

setup_logging()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from config import get_cors_origin_regex, get_cors_origins  # noqa: E402
from routes import analyze, health  # noqa: E402

app = FastAPI(
    title="JayQuant Stock Analyzer API",
    version="1.0.0",
    description="Indian stock analysis: fundamentals, technicals, news, and AI report.",
)

app.include_router(health.router)
app.include_router(analyze.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=get_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
