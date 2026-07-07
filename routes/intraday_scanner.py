"""REST API endpoints for live intraday stock scanner."""

from __future__ import annotations

from typing import List, Dict, Any, Optional

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dependencies.deps import get_current_user
from services.intraday_scanner import intraday_scanner, IntradayStock

router = APIRouter(prefix="/intraday", tags=["intraday-scanner"])

def clean_float(val: Optional[float]) -> Optional[float]:
    if val is None or math.isnan(val) or math.isinf(val):
        return None
    return val


class StockResponse(BaseModel):
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    avg_volume: int
    volume_ratio: float
    high: float
    low: float
    open_price: float
    pdh: float
    pdl: float
    rsi: Optional[float] = None
    momentum: Optional[float] = None
    volatility: Optional[float] = None
    last_update: str
    is_breakout_above_pdh: bool
    is_breakdown_below_pdl: bool
    is_high_volume: bool
    is_strong_momentum: bool


@router.get("/stocks", response_model=List[StockResponse])
async def get_live_stocks(
    symbols: Optional[str] = Query(None, description="Comma-separated symbols (defaults to Nifty 50)"),
    current_user = Depends(get_current_user)
):
    """Get live intraday stock data."""
    try:
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() + '.NS' for s in symbols.split(',')]
        
        stocks = await intraday_scanner.get_live_stocks(symbol_list)
        
        response = []
        for stock in stocks:
            response.append(StockResponse(
                symbol=stock.symbol,
                name=stock.name,
                current_price=clean_float(stock.current_price) or 0.0,
                change=clean_float(stock.change) or 0.0,
                change_percent=clean_float(stock.change_percent) or 0.0,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                volume_ratio=clean_float(stock.volume_ratio) or 0.0,
                high=clean_float(stock.high) or 0.0,
                low=clean_float(stock.low) or 0.0,
                open_price=clean_float(stock.open_price) or 0.0,
                pdh=clean_float(stock.pdh) or 0.0,
                pdl=clean_float(stock.pdl) or 0.0,
                rsi=clean_float(stock.rsi),
                momentum=clean_float(stock.momentum),
                volatility=clean_float(stock.volatility),
                last_update=stock.last_update.isoformat() if stock.last_update else "",
                is_breakout_above_pdh=stock.is_breakout_above_pdh(),
                is_breakdown_below_pdl=stock.is_breakdown_below_pdl(),
                is_high_volume=stock.is_high_volume(),
                is_strong_momentum=stock.is_strong_momentum()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/filtered", response_model=List[StockResponse])
async def get_filtered_stocks(
    min_volume_ratio: float = Query(1.5, ge=1.0, le=10.0, description="Minimum volume ratio"),
    min_change_percent: float = Query(1.0, ge=0.1, le=20.0, description="Minimum change percentage"),
    show_breakouts: bool = Query(True, description="Show PDH/PDL breakouts"),
    show_high_volume: bool = Query(True, description="Show high volume stocks"),
    current_user = Depends(get_current_user)
):
    """Get filtered stocks based on criteria."""
    try:
        # First refresh the data
        await intraday_scanner.get_live_stocks()
        
        stocks = intraday_scanner.get_filtered_stocks(
            min_volume_ratio=min_volume_ratio,
            min_change_percent=min_change_percent,
            show_breakouts=show_breakouts,
            show_high_volume=show_high_volume
        )
        
        response = []
        for stock in stocks:
            response.append(StockResponse(
                symbol=stock.symbol,
                name=stock.name,
                current_price=clean_float(stock.current_price) or 0.0,
                change=clean_float(stock.change) or 0.0,
                change_percent=clean_float(stock.change_percent) or 0.0,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                volume_ratio=clean_float(stock.volume_ratio) or 0.0,
                high=clean_float(stock.high) or 0.0,
                low=clean_float(stock.low) or 0.0,
                open_price=clean_float(stock.open_price) or 0.0,
                pdh=clean_float(stock.pdh) or 0.0,
                pdl=clean_float(stock.pdl) or 0.0,
                rsi=clean_float(stock.rsi),
                momentum=clean_float(stock.momentum),
                volatility=clean_float(stock.volatility),
                last_update=stock.last_update.isoformat() if stock.last_update else "",
                is_breakout_above_pdh=stock.is_breakout_above_pdh(),
                is_breakdown_below_pdl=stock.is_breakdown_below_pdl(),
                is_high_volume=stock.is_high_volume(),
                is_strong_momentum=stock.is_strong_momentum()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/breakouts", response_model=List[StockResponse])
async def get_breakout_stocks(
    current_user = Depends(get_current_user)
):
    """Get stocks that are breaking out above PDH or below PDL."""
    try:
        # First refresh the data
        await intraday_scanner.get_live_stocks()
        
        stocks = intraday_scanner.get_filtered_stocks(
            min_volume_ratio=1.0,
            min_change_percent=0.5,
            show_breakouts=True,
            show_high_volume=False
        )
        
        # Filter for only breakouts
        breakout_stocks = [
            stock for stock in stocks 
            if stock.is_breakout_above_pdh() or stock.is_breakdown_below_pdl()
        ]
        
        response = []
        for stock in breakout_stocks:
            response.append(StockResponse(
                symbol=stock.symbol,
                name=stock.name,
                current_price=clean_float(stock.current_price) or 0.0,
                change=clean_float(stock.change) or 0.0,
                change_percent=clean_float(stock.change_percent) or 0.0,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                volume_ratio=clean_float(stock.volume_ratio) or 0.0,
                high=clean_float(stock.high) or 0.0,
                low=clean_float(stock.low) or 0.0,
                open_price=clean_float(stock.open_price) or 0.0,
                pdh=clean_float(stock.pdh) or 0.0,
                pdl=clean_float(stock.pdl) or 0.0,
                rsi=clean_float(stock.rsi),
                momentum=clean_float(stock.momentum),
                volatility=clean_float(stock.volatility),
                last_update=stock.last_update.isoformat() if stock.last_update else "",
                is_breakout_above_pdh=stock.is_breakout_above_pdh(),
                is_breakdown_below_pdl=stock.is_breakdown_below_pdl(),
                is_high_volume=stock.is_high_volume(),
                is_strong_momentum=stock.is_strong_momentum()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/high-volume", response_model=List[StockResponse])
async def get_high_volume_stocks(
    min_volume_ratio: float = Query(2.0, ge=1.5, le=10.0, description="Minimum volume ratio"),
    current_user = Depends(get_current_user)
):
    """Get stocks with unusually high volume."""
    try:
        # First refresh the data
        await intraday_scanner.get_live_stocks()
        
        stocks = intraday_scanner.get_filtered_stocks(
            min_volume_ratio=min_volume_ratio,
            min_change_percent=0.1,
            show_breakouts=False,
            show_high_volume=True
        )
        
        response = []
        for stock in stocks:
            response.append(StockResponse(
                symbol=stock.symbol,
                name=stock.name,
                current_price=clean_float(stock.current_price) or 0.0,
                change=clean_float(stock.change) or 0.0,
                change_percent=clean_float(stock.change_percent) or 0.0,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                volume_ratio=clean_float(stock.volume_ratio) or 0.0,
                high=clean_float(stock.high) or 0.0,
                low=clean_float(stock.low) or 0.0,
                open_price=clean_float(stock.open_price) or 0.0,
                pdh=clean_float(stock.pdh) or 0.0,
                pdl=clean_float(stock.pdl) or 0.0,
                rsi=clean_float(stock.rsi),
                momentum=clean_float(stock.momentum),
                volatility=clean_float(stock.volatility),
                last_update=stock.last_update.isoformat() if stock.last_update else "",
                is_breakout_above_pdh=stock.is_breakout_above_pdh(),
                is_breakdown_below_pdl=stock.is_breakdown_below_pdl(),
                is_high_volume=stock.is_high_volume(),
                is_strong_momentum=stock.is_strong_momentum()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/gainers", response_model=List[StockResponse])
async def get_top_gainers(
    limit: int = Query(20, ge=1, le=100, description="Number of stocks to return"),
    current_user = Depends(get_current_user)
):
    """Get top gainers for the day."""
    try:
        # First refresh the data
        await intraday_scanner.get_live_stocks()
        
        stocks = list(intraday_scanner.cache.values())
        
        # Filter for positive changes and sort by percentage
        gainers = [stock for stock in stocks if stock.change_percent > 0]
        gainers.sort(key=lambda x: x.change_percent, reverse=True)
        
        response = []
        for stock in gainers[:limit]:
            response.append(StockResponse(
                symbol=stock.symbol,
                name=stock.name,
                current_price=clean_float(stock.current_price) or 0.0,
                change=clean_float(stock.change) or 0.0,
                change_percent=clean_float(stock.change_percent) or 0.0,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                volume_ratio=clean_float(stock.volume_ratio) or 0.0,
                high=clean_float(stock.high) or 0.0,
                low=clean_float(stock.low) or 0.0,
                open_price=clean_float(stock.open_price) or 0.0,
                pdh=clean_float(stock.pdh) or 0.0,
                pdl=clean_float(stock.pdl) or 0.0,
                rsi=clean_float(stock.rsi),
                momentum=clean_float(stock.momentum),
                volatility=clean_float(stock.volatility),
                last_update=stock.last_update.isoformat() if stock.last_update else "",
                is_breakout_above_pdh=stock.is_breakout_above_pdh(),
                is_breakdown_below_pdl=stock.is_breakdown_below_pdl(),
                is_high_volume=stock.is_high_volume(),
                is_strong_momentum=stock.is_strong_momentum()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/losers", response_model=List[StockResponse])
async def get_top_losers(
    limit: int = Query(20, ge=1, le=100, description="Number of stocks to return"),
    current_user = Depends(get_current_user)
):
    """Get top losers for the day."""
    try:
        # First refresh the data
        await intraday_scanner.get_live_stocks()
        
        stocks = list(intraday_scanner.cache.values())
        
        # Filter for negative changes and sort by percentage
        losers = [stock for stock in stocks if stock.change_percent < 0]
        losers.sort(key=lambda x: x.change_percent)
        
        response = []
        for stock in losers[:limit]:
            response.append(StockResponse(
                symbol=stock.symbol,
                name=stock.name,
                current_price=clean_float(stock.current_price) or 0.0,
                change=clean_float(stock.change) or 0.0,
                change_percent=clean_float(stock.change_percent) or 0.0,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
                volume_ratio=clean_float(stock.volume_ratio) or 0.0,
                high=clean_float(stock.high) or 0.0,
                low=clean_float(stock.low) or 0.0,
                open_price=clean_float(stock.open_price) or 0.0,
                pdh=clean_float(stock.pdh) or 0.0,
                pdl=clean_float(stock.pdl) or 0.0,
                rsi=clean_float(stock.rsi),
                momentum=clean_float(stock.momentum),
                volatility=clean_float(stock.volatility),
                last_update=stock.last_update.isoformat() if stock.last_update else "",
                is_breakout_above_pdh=stock.is_breakout_above_pdh(),
                is_breakdown_below_pdl=stock.is_breakdown_below_pdl(),
                is_high_volume=stock.is_high_volume(),
                is_strong_momentum=stock.is_strong_momentum()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-summary")
async def get_market_summary(current_user = Depends(get_current_user)):
    """Get overall market summary."""
    try:
        # First refresh the data
        await intraday_scanner.get_live_stocks()
        
        stocks = list(intraday_scanner.cache.values())
        
        if not stocks:
            return {
                "total_stocks": 0,
                "gainers": 0,
                "losers": 0,
                "unchanged": 0,
                "avg_change_percent": 0,
                "total_volume": 0,
                "breakouts": 0,
                "high_volume_stocks": 0,
                "last_update": None
            }
        
        gainers = len([s for s in stocks if s.change_percent > 0])
        losers = len([s for s in stocks if s.change_percent < 0])
        unchanged = len([s for s in stocks if s.change_percent == 0])
        
        avg_change = sum(s.change_percent for s in stocks) / len(stocks)
        total_volume = sum(s.volume for s in stocks)
        breakouts = len([s for s in stocks if s.is_breakout_above_pdh() or s.is_breakdown_below_pdl()])
        high_volume = len([s for s in stocks if s.is_high_volume()])
        
        return {
            "total_stocks": len(stocks),
            "gainers": gainers,
            "losers": losers,
            "unchanged": unchanged,
            "avg_change_percent": clean_float(round(avg_change, 2)) or 0.0,
            "total_volume": total_volume,
            "breakouts": breakouts,
            "high_volume_stocks": high_volume,
            "last_update": intraday_scanner.last_update.isoformat() if intraday_scanner.last_update else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
