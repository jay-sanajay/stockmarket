"""REST API endpoints for intraday breakout strategy management."""

from __future__ import annotations

from datetime import datetime, date
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import BreakoutStrategy, BreakoutSignal, BreakoutTrade, BacktestResult, User
from dependencies.deps import get_current_user
from services.breakout_strategy_service import breakout_service

router = APIRouter(prefix="/breakout-strategy", tags=["breakout-strategy"])


# Pydantic models for API requests/responses
class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    symbols: List[str] = Field(..., min_items=1, max_items=10)
    capital: float = Field(..., gt=0)
    risk_per_trade: float = Field(..., ge=0.5, le=5.0)  # 0.5% to 5%
    timeframe: str = Field(..., pattern="^(1min|5min)$")
    strong_candle_threshold: float = Field(default=0.6, ge=0.3, le=0.9)
    volume_multiplier: float = Field(default=1.5, ge=1.0, le=5.0)
    risk_reward_ratio: float = Field(default=2.0, ge=1.0, le=5.0)
    max_daily_trades: int = Field(default=3, ge=1, le=10)
    stop_after_losses: int = Field(default=2, ge=1, le=5)
    enable_trend_filter: bool = Field(default=False)
    trend_ema_period: int = Field(default=50, ge=10, le=200)
    enable_session_filter: bool = Field(default=False)
    session_start: str = Field(default="09:15", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    session_end: str = Field(default="10:30", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    symbols: Optional[List[str]] = Field(None, min_items=1, max_items=10)
    capital: Optional[float] = Field(None, gt=0)
    risk_per_trade: Optional[float] = Field(None, ge=0.5, le=5.0)
    timeframe: Optional[str] = Field(None, pattern="^(1min|5min)$")
    strong_candle_threshold: Optional[float] = Field(None, ge=0.3, le=0.9)
    volume_multiplier: Optional[float] = Field(None, ge=1.0, le=5.0)
    risk_reward_ratio: Optional[float] = Field(None, ge=1.0, le=5.0)
    max_daily_trades: Optional[int] = Field(None, ge=1, le=10)
    stop_after_losses: Optional[int] = Field(None, ge=1, le=5)
    enable_trend_filter: Optional[bool] = None
    trend_ema_period: Optional[int] = Field(None, ge=10, le=200)
    enable_session_filter: Optional[bool] = None
    session_start: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    session_end: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    active: Optional[bool] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    symbols: List[str]
    capital: float
    risk_per_trade: float
    timeframe: str
    strong_candle_threshold: float
    volume_multiplier: float
    risk_reward_ratio: float
    max_daily_trades: int
    stop_after_losses: int
    enable_trend_filter: bool
    trend_ema_period: int
    enable_session_filter: bool
    session_start: str
    session_end: str
    active: bool
    created_at: datetime
    updated_at: datetime
    is_running: bool = False


class SignalResponse(BaseModel):
    id: int
    symbol: str
    signal_type: str
    signal_time: datetime
    price: float
    pdh: float
    pdl: float
    candle_close: float
    candle_high: float
    candle_low: float
    candle_volume: int
    avg_volume_5: float
    body_percentage: float
    volume_ratio: float
    confirmed: bool
    executed: bool


class TradeResponse(BaseModel):
    id: int
    symbol: str
    trade_type: str
    entry_price: float
    stop_loss: float
    target_price: float
    quantity: float
    entry_time: datetime
    exit_price: Optional[float]
    exit_time: Optional[datetime]
    exit_reason: Optional[str]
    pnl: Optional[float]
    pnl_percentage: Optional[float]
    status: str


class BacktestRequest(BaseModel):
    strategy_name: str
    symbols: List[str] = Field(..., min_items=1, max_items=10)
    start_date: date
    end_date: date
    timeframe: str = Field(..., pattern="^(1min|5min)$")
    capital: float = Field(..., gt=0)
    risk_per_trade: float = Field(..., ge=0.5, le=5.0)
    strong_candle_threshold: float = Field(default=0.6, ge=0.3, le=0.9)
    volume_multiplier: float = Field(default=1.5, ge=1.0, le=5.0)
    risk_reward_ratio: float = Field(default=2.0, ge=1.0, le=5.0)
    max_daily_trades: int = Field(default=3, ge=1, le=10)
    enable_trend_filter: bool = Field(default=False)
    trend_ema_period: int = Field(default=50, ge=10, le=200)


class BacktestResponse(BaseModel):
    id: int
    strategy_name: str
    symbols: List[str]
    start_date: date
    end_date: date
    timeframe: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_percentage: float
    max_drawdown: float
    max_drawdown_percentage: float
    sharpe_ratio: Optional[float]
    parameters: Dict[str, Any]
    created_at: datetime


@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new breakout strategy."""
    try:
        db_strategy = BreakoutStrategy(
            user_id=current_user.id,
            **strategy.dict()
        )
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        
        # Convert to response model
        response = StrategyResponse.from_orm(db_strategy)
        response.is_running = False
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/strategies", response_model=List[StrategyResponse])
async def get_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all strategies for the current user."""
    strategies = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.user_id == current_user.id
    ).order_by(BreakoutStrategy.created_at.desc()).all()
    
    response = []
    for strategy in strategies:
        strat_resp = StrategyResponse.from_orm(strategy)
        strat_resp.is_running = strategy.id in breakout_service.active_monitors
        response.append(strat_resp)
    
    return response


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    response = StrategyResponse.from_orm(strategy)
    response.is_running = strategy.id in breakout_service.active_monitors
    return response


@router.put("/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Stop strategy if it's running
    if strategy.id in breakout_service.active_monitors:
        breakout_service.stop_strategy(strategy.id)
    
    # Update fields
    update_data = strategy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)
    
    db.commit()
    db.refresh(strategy)
    
    response = StrategyResponse.from_orm(strategy)
    response.is_running = False
    return response


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Stop strategy if it's running
    if strategy.id in breakout_service.active_monitors:
        breakout_service.stop_strategy(strategy.id)
    
    db.delete(strategy)
    db.commit()
    
    return {"message": "Strategy deleted successfully"}


@router.post("/strategies/{strategy_id}/start")
async def start_strategy(
    strategy_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start monitoring a strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if not strategy.active:
        raise HTTPException(status_code=400, detail="Strategy is not active")
    
    if strategy.id in breakout_service.active_monitors:
        raise HTTPException(status_code=400, detail="Strategy is already running")
    
    # Start strategy in background
    background_tasks.add_task(breakout_service.start_strategy, strategy_id)
    
    return {"message": "Strategy started successfully"}


@router.post("/strategies/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop monitoring a strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if strategy.id not in breakout_service.active_monitors:
        raise HTTPException(status_code=400, detail="Strategy is not running")
    
    breakout_service.stop_strategy(strategy_id)
    
    return {"message": "Strategy stopped successfully"}


@router.get("/strategies/{strategy_id}/signals", response_model=List[SignalResponse])
async def get_strategy_signals(
    strategy_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get signals for a strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    signals = db.query(BreakoutSignal).filter(
        BreakoutSignal.strategy_id == strategy_id
    ).order_by(BreakoutSignal.signal_time.desc()).limit(limit).all()
    
    return [SignalResponse.from_orm(s) for s in signals]


@router.get("/strategies/{strategy_id}/trades", response_model=List[TradeResponse])
async def get_strategy_trades(
    strategy_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trades for a strategy."""
    strategy = db.query(BreakoutStrategy).filter(
        BreakoutStrategy.id == strategy_id,
        BreakoutStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    trades = db.query(BreakoutTrade).filter(
        BreakoutTrade.strategy_id == strategy_id
    ).order_by(BreakoutTrade.entry_time.desc()).limit(limit).all()
    
    return [TradeResponse.from_orm(t) for t in trades]


@router.post("/trades/{trade_id}/close")
async def close_trade(
    trade_id: int,
    exit_price: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually close a trade."""
    trade = db.query(BreakoutTrade).join(BreakoutStrategy).filter(
        BreakoutTrade.id == trade_id,
        BreakoutStrategy.user_id == current_user.id,
        BreakoutTrade.status == "OPEN"
    ).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Open trade not found")
    
    # Get current price if not provided
    if exit_price is None:
        from services.breakout_strategy_service import DataFetcher
        async with DataFetcher() as fetcher:
            exit_price = await fetcher.get_current_price(trade.symbol)
    
    if exit_price <= 0:
        raise HTTPException(status_code=400, detail="Invalid exit price")
    
    # Calculate P&L
    if trade.trade_type == "BUY":
        pnl = (exit_price - trade.entry_price) * trade.quantity
        pnl_percentage = ((exit_price - trade.entry_price) / trade.entry_price) * 100
    else:  # SELL
        pnl = (trade.entry_price - exit_price) * trade.quantity
        pnl_percentage = ((trade.entry_price - exit_price) / trade.entry_price) * 100
    
    # Update trade
    trade.exit_price = exit_price
    trade.exit_time = datetime.now()
    trade.exit_reason = "MANUAL"
    trade.pnl = pnl
    trade.pnl_percentage = pnl_percentage
    trade.status = "CLOSED"
    
    db.commit()
    
    return {"message": "Trade closed successfully", "pnl": pnl, "pnl_percentage": pnl_percentage}


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(
    backtest_request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run a backtest on historical data."""
    from services.backtest_service import run_backtest
    
    # Run backtest in background
    backtest_task = background_tasks.add_task(
        run_backtest,
        user_id=current_user.id,
        **backtest_request.dict()
    )
    
    # For now, return a placeholder response
    # In production, you'd want to implement proper async task tracking
    return {
        "message": "Backtest started. Results will be available shortly.",
        "task_id": str(id(backtest_task))
    }


@router.get("/backtest/results", response_model=List[BacktestResponse])
async def get_backtest_results(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get backtest results for the current user."""
    results = db.query(BacktestResult).filter(
        BacktestResult.user_id == current_user.id
    ).order_by(BacktestResult.created_at.desc()).limit(limit).all()
    
    return [BacktestResponse.from_orm(r) for r in results]


@router.get("/backtest/results/{result_id}", response_model=BacktestResponse)
async def get_backtest_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific backtest result."""
    result = db.query(BacktestResult).filter(
        BacktestResult.id == result_id,
        BacktestResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    return BacktestResponse.from_orm(result)
