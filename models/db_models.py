"""SQLAlchemy ORM models for dashboard features."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watchlists: Mapped[list[Watchlist]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list[AlertRule]] = relationship(back_populates="user", cascade="all, delete-orphan")
    holdings: Mapped[list[Holding]] = relationship(back_populates="user", cascade="all, delete-orphan")
    strategies: Mapped[list[BreakoutStrategy]] = relationship(back_populates="user", cascade="all, delete-orphan")
    backtest_results: Mapped[list[BacktestResult]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), default="My Watchlist")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="watchlists")
    items: Mapped[list[WatchlistItem]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watchlist: Mapped[Watchlist] = relationship(back_populates="items")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    alert_type: Mapped[str] = mapped_column(String(32))  # AlertType value
    threshold: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped[User] = relationship(back_populates="alerts")


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    avg_buy_price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="holdings")


class VerdictRecord(Base):
    """Persistent verdict / signal history (replaces verdict_log.json over time)."""

    __tablename__ = "verdict_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict: Mapped[str] = mapped_column(Text)
    signal_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strategy_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    news_sentiment: Mapped[str | None] = mapped_column(Text, nullable=True)


class DailySummaryCache(Base):
    __tablename__ = "daily_summary_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day_key: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BreakoutStrategy(Base):
    __tablename__ = "breakout_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    symbols: Mapped[list[str]] = mapped_column(JSON)
    capital: Mapped[float] = mapped_column(Float)
    risk_per_trade: Mapped[float] = mapped_column(Float)  # Percentage (1-2%)
    timeframe: Mapped[str] = mapped_column(String(16))  # "1min", "5min"
    strong_candle_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    volume_multiplier: Mapped[float] = mapped_column(Float, default=1.5)
    risk_reward_ratio: Mapped[float] = mapped_column(Float, default=2.0)
    max_daily_trades: Mapped[int] = mapped_column(Integer, default=3)
    stop_after_losses: Mapped[int] = mapped_column(Integer, default=2)
    enable_trend_filter: Mapped[bool] = mapped_column(Boolean, default=False)
    trend_ema_period: Mapped[int] = mapped_column(Integer, default=50)
    enable_session_filter: Mapped[bool] = mapped_column(Boolean, default=False)
    session_start: Mapped[str] = mapped_column(String(8), default="09:15")
    session_end: Mapped[str] = mapped_column(String(8), default="10:30")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="strategies")
    signals: Mapped[list["BreakoutSignal"]] = relationship(back_populates="strategy", cascade="all, delete-orphan")
    trades: Mapped[list["BreakoutTrade"]] = relationship(back_populates="strategy", cascade="all, delete-orphan")


class BreakoutSignal(Base):
    __tablename__ = "breakout_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("breakout_strategies.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    signal_type: Mapped[str] = mapped_column(String(8))  # "BUY" or "SELL"
    signal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[float] = mapped_column(Float)
    pdh: Mapped[float] = mapped_column(Float)
    pdl: Mapped[float] = mapped_column(Float)
    candle_close: Mapped[float] = mapped_column(Float)
    candle_high: Mapped[float] = mapped_column(Float)
    candle_low: Mapped[float] = mapped_column(Float)
    candle_volume: Mapped[int] = mapped_column(Integer)
    avg_volume_5: Mapped[float] = mapped_column(Float)
    body_percentage: Mapped[float] = mapped_column(Float)
    volume_ratio: Mapped[float] = mapped_column(Float)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    strategy: Mapped[BreakoutStrategy] = relationship(back_populates="signals")


class BreakoutTrade(Base):
    __tablename__ = "breakout_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("breakout_strategies.id", ondelete="CASCADE"), index=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("breakout_signals.id", ondelete="SET NULL"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    trade_type: Mapped[str] = mapped_column(String(8))  # "BUY" or "SELL"
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    target_price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "TARGET", "STOP_LOSS", "EOD", "MANUAL"
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="OPEN")  # "OPEN", "CLOSED", "CANCELLED"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    strategy: Mapped[BreakoutStrategy] = relationship(back_populates="trades")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_name: Mapped[str] = mapped_column(String(128))
    symbols: Mapped[list[str]] = mapped_column(JSON)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timeframe: Mapped[str] = mapped_column(String(16))
    total_trades: Mapped[int] = mapped_column(Integer)
    winning_trades: Mapped[int] = mapped_column(Integer)
    losing_trades: Mapped[int] = mapped_column(Integer)
    win_rate: Mapped[float] = mapped_column(Float)
    total_pnl: Mapped[float] = mapped_column(Float)
    total_pnl_percentage: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    max_drawdown_percentage: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON)
    detailed_trades: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="backtest_results")
