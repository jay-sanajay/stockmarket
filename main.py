"""
FastAPI entrypoint — stock analysis + daily dashboard APIs.
"""

import json
import math
from contextlib import asynccontextmanager
from typing import Any

from utils.logging_config import setup_logging

setup_logging()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402


class NaNSafeJSONEncoder(json.JSONEncoder):
    """Replace NaN / Inf with None so JSON serialization never crashes."""

    def default(self, o: Any) -> Any:
        return super().default(o)

    def encode(self, o: Any) -> str:
        return super().encode(self._sanitize(o))

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._sanitize(v) for v in obj]
        return obj


class NaNSafeJSONResponse(JSONResponse):
    """JSONResponse subclass that safely handles NaN/Inf float values."""

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            cls=NaNSafeJSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")

from config import get_cors_origin_regex, get_cors_origins  # noqa: E402
from database import SessionLocal, init_db  # noqa: E402
from routes import (  # noqa: E402
    alerts,
    analyze,
    assistant,
    auth,
    breakout_strategy,
    compare,
    dashboard,
    health,
    history,
    intraday_scanner,
    intraday_picks,
    portfolio,
    stock_prediction,
    watchlist,
    websocket,
    ai_recommendations,
)
from services.verdict_db_service import migrate_json_verdict_log_if_present  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        migrate_json_verdict_log_if_present(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="JayQuant Stock Analyzer API",
    version="2.0.0",
    description="Indian stock analysis + daily dashboard (watchlists, portfolio, alerts).",
    lifespan=lifespan,
    default_response_class=NaNSafeJSONResponse,
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(auth.router)
app.include_router(watchlist.router)
app.include_router(dashboard.router)
app.include_router(history.router)
app.include_router(alerts.router)
app.include_router(portfolio.router)
app.include_router(compare.router)
app.include_router(assistant.router)
app.include_router(breakout_strategy.router)
app.include_router(intraday_scanner.router)
app.include_router(intraday_picks.router)
app.include_router(stock_prediction.router)
app.include_router(websocket.router)
app.include_router(ai_recommendations.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=get_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
