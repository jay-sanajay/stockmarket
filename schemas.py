"""Pydantic response models for API documentation and validation."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str = Field(description="deployment mode hint")


class EntryZone(BaseModel):
    range: str
    reason: str


class TargetZone(BaseModel):
    level: str
    reason: str


class AnalyzeSuccessResponse(BaseModel):
    company: str | None = None
    symbol: str
    ratios: dict[str, Any] = Field(default_factory=dict)
    chart_base64: str | None = None
    news_sentiment: str | None = None
    news_headlines: list[str] = Field(default_factory=list)
    market_triggers: str | None = None
    retail_stock: bool = False
    signal_score: float | int | None = None
    signal_breakdown: dict[str, str] = Field(default_factory=dict)
    full_report: str | None = None
    verdict: str | None = None
    strategy_type: str | None = None
    strategy_reason: str | None = None
    entry_zones: list[dict[str, str]] = Field(default_factory=list)
    stop_loss_zone: str | None = None
    target_zones: list[dict[str, str]] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    detail: str
