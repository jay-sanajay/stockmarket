"""Backtesting service for intraday breakout strategy."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from models.db_models import BacktestResult
from services.breakout_strategy_service import (
    BreakoutDetector, RiskManager, CandleData, MarketData
)

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Represents a trade in backtest."""
    symbol: str
    trade_type: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    quantity: float
    stop_loss: float
    target_price: float
    pnl: float
    pnl_percentage: float
    exit_reason: str


class BacktestEngine:
    """Core backtesting engine for breakout strategy."""
    
    def __init__(self):
        self.detector = BreakoutDetector()
        self.risk_manager = RiskManager()
    
    async def fetch_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        interval: str = "1m"
    ) -> Tuple[List[CandleData], Dict[date, Tuple[float, float]]]:
        """
        Fetch historical data and previous day high/low for each day.
        
        Returns:
            (candles, daily_high_low_dict)
        """
        try:
            # Convert to yfinance format
            ticker = yf.Ticker(f"{symbol}.NS")
            
            # Get intraday data
            end_datetime = datetime.combine(end_date, datetime.max.time())
            start_datetime = datetime.combine(start_date, datetime.min.time())
            
            hist = ticker.history(
                start=start_datetime,
                end=end_datetime,
                interval=interval
            )
            
            candles = []
            for timestamp, row in hist.iterrows():
                candle = CandleData(
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                candles.append(candle)
            
            # Get daily data for PDH/PDL
            daily_hist = ticker.history(
                start=start_date - timedelta(days=5),
                end=end_date + timedelta(days=1),
                interval="1d"
            )
            
            daily_high_low = {}
            for day_timestamp, row in daily_hist.iterrows():
                day_date = day_timestamp.date()
                if start_date <= day_date <= end_date:
                    daily_high_low[day_date] = (float(row['High']), float(row['Low']))
            
            return candles, daily_high_low
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return [], {}
    
    def get_previous_day_high_low(
        self, 
        current_date: date, 
        daily_high_low: Dict[date, Tuple[float, float]]
    ) -> Tuple[float, float]:
        """Get previous day's high and low."""
        prev_date = current_date - timedelta(days=1)
        
        # Try to get previous trading day (skip weekends)
        attempts = 0
        while attempts < 7:  # Look back up to 7 days
            if prev_date in daily_high_low:
                return daily_high_low[prev_date]
            prev_date -= timedelta(days=1)
            attempts += 1
        
        return 0.0, 0.0
    
    def run_single_symbol_backtest(
        self,
        symbol: str,
        candles: List[CandleData],
        daily_high_low: Dict[date, Tuple[float, float]],
        parameters: Dict[str, Any]
    ) -> List[BacktestTrade]:
        """Run backtest for a single symbol."""
        trades = []
        open_trades = {}  # symbol -> trade
        daily_trade_count = {}
        consecutive_losses = {}
        
        # Group candles by date
        candles_by_date = {}
        for candle in candles:
            candle_date = candle.timestamp.date()
            if candle_date not in candles_by_date:
                candles_by_date[candle_date] = []
            candles_by_date[candle_date].append(candle)
        
        # Process each day
        for current_date, day_candles in sorted(candles_by_date.items()):
            pdh, pdl = self.get_previous_day_high_low(current_date, daily_high_low)
            
            if pdh == 0 or pdl == 0:
                continue
            
            # Reset daily trade count
            daily_trade_count[current_date] = 0
            
            # Process candles for the day
            for i, candle in enumerate(day_candles):
                # Check session filter
                if parameters.get('enable_session_filter'):
                    current_time = candle.timestamp.time()
                    start_time = datetime.strptime(parameters['session_start'], "%H:%M").time()
                    end_time = datetime.strptime(parameters['session_end'], "%H:%M").time()
                    if not (start_time <= current_time <= end_time):
                        continue
                
                # Skip if we already hit max daily trades
                if daily_trade_count[current_date] >= parameters.get('max_daily_trades', 3):
                    continue
                
                # Skip if we had consecutive losses
                if symbol in consecutive_losses:
                    if consecutive_losses[symbol] >= parameters.get('stop_after_losses', 2):
                        continue
                
                # Check existing open trades for exit conditions
                if symbol in open_trades:
                    open_trade = open_trades[symbol]
                    
                    # Check stop loss and target
                    if open_trade.trade_type == "BUY":
                        if candle.low <= open_trade.stop_loss:
                            # Stop loss hit
                            open_trade.exit_price = open_trade.stop_loss
                            open_trade.exit_time = candle.timestamp
                            open_trade.exit_reason = "STOP_LOSS"
                        elif candle.high >= open_trade.target_price:
                            # Target hit
                            open_trade.exit_price = open_trade.target_price
                            open_trade.exit_time = candle.timestamp
                            open_trade.exit_reason = "TARGET"
                    else:  # SELL
                        if candle.high >= open_trade.stop_loss:
                            # Stop loss hit
                            open_trade.exit_price = open_trade.stop_loss
                            open_trade.exit_time = candle.timestamp
                            open_trade.exit_reason = "STOP_LOSS"
                        elif candle.low <= open_trade.target_price:
                            # Target hit
                            open_trade.exit_price = open_trade.target_price
                            open_trade.exit_time = candle.timestamp
                            open_trade.exit_reason = "TARGET"
                    
                    # If trade closed, calculate P&L and update consecutive losses
                    if open_trade.exit_price > 0:
                        if open_trade.trade_type == "BUY":
                            open_trade.pnl = (open_trade.exit_price - open_trade.entry_price) * open_trade.quantity
                            open_trade.pnl_percentage = ((open_trade.exit_price - open_trade.entry_price) / open_trade.entry_price) * 100
                        else:  # SELL
                            open_trade.pnl = (open_trade.entry_price - open_trade.exit_price) * open_trade.quantity
                            open_trade.pnl_percentage = ((open_trade.entry_price - open_trade.exit_price) / open_trade.entry_price) * 100
                        
                        trades.append(open_trade)
                        
                        # Update consecutive losses
                        if open_trade.pnl < 0:
                            consecutive_losses[symbol] = consecutive_losses.get(symbol, 0) + 1
                        else:
                            consecutive_losses[symbol] = 0
                        
                        del open_trades[symbol]
                
                # Skip if we already have an open trade for this symbol
                if symbol in open_trades:
                    continue
                
                # Check for breakout signals (need at least 5 candles for volume average)
                if i >= 5:
                    recent_candles = day_candles[max(0, i-5):i]
                    avg_volume_5 = sum(c.volume for c in recent_candles) / len(recent_candles)
                    
                    # Create market data for detection
                    market_data = MarketData(
                        symbol=symbol,
                        current_price=candle.close,
                        pdh=pdh,
                        pdl=pdl,
                        candles=day_candles[:i+1]
                    )
                    
                    # Detect breakout
                    signal = self.detector.detect_breakout(market_data, type('Strategy', (), {
                        'strong_candle_threshold': parameters.get('strong_candle_threshold', 0.6),
                        'volume_multiplier': parameters.get('volume_multiplier', 1.5)
                    })())
                    
                    if signal:
                        # Apply trend filter if enabled
                        if parameters.get('enable_trend_filter'):
                            # Simple EMA calculation for trend
                            ema_period = parameters.get('trend_ema_period', 50)
                            if len(day_candles[:i+1]) >= ema_period:
                                closes = [c.close for c in day_candles[:i+1]]
                                ema = pd.Series(closes).ewm(span=ema_period, adjust=False).mean().iloc[-1]
                                if candle.close < ema:
                                    continue  # Skip signal if below EMA
                        
                        # Calculate position size and risk levels
                        stop_loss, target_price = self.risk_manager.calculate_stop_loss_target(
                            signal['type'],
                            signal['price'],
                            signal['candle'].high,
                            signal['candle'].low,
                            parameters.get('risk_reward_ratio', 2.0)
                        )
                        
                        quantity = self.risk_manager.calculate_position_size(
                            parameters['capital'],
                            parameters['risk_per_trade'],
                            signal['price'],
                            stop_loss
                        )
                        
                        if quantity > 0:
                            # Create new trade
                            trade = BacktestTrade(
                                symbol=symbol,
                                trade_type=signal['type'],
                                entry_price=signal['price'],
                                exit_price=0.0,  # Will be set when trade closes
                                entry_time=candle.timestamp,
                                exit_time=candle.timestamp,  # Will be updated when trade closes
                                quantity=quantity,
                                stop_loss=stop_loss,
                                target_price=target_price,
                                pnl=0.0,  # Will be calculated when trade closes
                                pnl_percentage=0.0,  # Will be calculated when trade closes
                                exit_reason=""
                            )
                            
                            open_trades[symbol] = trade
                            daily_trade_count[current_date] += 1
        
        # Close any remaining open trades at end of period
        for symbol, trade in open_trades.items():
            if candles:
                trade.exit_price = candles[-1].close
                trade.exit_time = candles[-1].timestamp
                trade.exit_reason = "EOD"
                
                if trade.trade_type == "BUY":
                    trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
                    trade.pnl_percentage = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                else:  # SELL
                    trade.pnl = (trade.entry_price - trade.exit_price) * trade.quantity
                    trade.pnl_percentage = ((trade.entry_price - trade.exit_price) / trade.entry_price) * 100
                
                trades.append(trade)
        
        return trades
    
    def calculate_metrics(self, trades: List[BacktestTrade], capital: float) -> Dict[str, float]:
        """Calculate performance metrics from trades."""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_pnl_percentage': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_percentage': 0.0,
                'sharpe_ratio': None
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        total_pnl = sum(t.pnl for t in trades)
        total_pnl_percentage = (total_pnl / capital) * 100 if capital > 0 else 0.0
        
        # Calculate max drawdown
        equity_curve = [capital]
        for trade in sorted(trades, key=lambda x: x.entry_time):
            equity_curve.append(equity_curve[-1] + trade.pnl)
        
        peak = equity_curve[0]
        max_drawdown = 0.0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_percentage = (max_drawdown / capital) * 100 if capital > 0 else 0.0
        
        # Calculate Sharpe ratio (simplified)
        if len(trades) > 1:
            returns = [t.pnl_percentage for t in trades]
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0.0
        else:
            sharpe_ratio = None
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_percentage': total_pnl_percentage,
            'max_drawdown': max_drawdown,
            'max_drawdown_percentage': max_drawdown_percentage,
            'sharpe_ratio': sharpe_ratio
        }


async def run_backtest(
    user_id: int,
    strategy_name: str,
    symbols: List[str],
    start_date: date,
    end_date: date,
    timeframe: str,
    capital: float,
    risk_per_trade: float,
    strong_candle_threshold: float = 0.6,
    volume_multiplier: float = 1.5,
    risk_reward_ratio: float = 2.0,
    max_daily_trades: int = 3,
    stop_after_losses: int = 2,
    enable_trend_filter: bool = False,
    trend_ema_period: int = 50
) -> BacktestResult:
    """Run a complete backtest and save results to database."""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        engine = BacktestEngine()
        all_trades = []
        
        parameters = {
            'capital': capital,
            'risk_per_trade': risk_per_trade,
            'strong_candle_threshold': strong_candle_threshold,
            'volume_multiplier': volume_multiplier,
            'risk_reward_ratio': risk_reward_ratio,
            'max_daily_trades': max_daily_trades,
            'stop_after_losses': stop_after_losses,
            'enable_trend_filter': enable_trend_filter,
            'trend_ema_period': trend_ema_period,
            'enable_session_filter': False,  # Default to false for backtesting
            'session_start': '09:15',
            'session_end': '15:30'
        }
        
        # Run backtest for each symbol
        for symbol in symbols:
            logger.info(f"Running backtest for {symbol}")
            candles, daily_high_low = await engine.fetch_historical_data(
                symbol, start_date, end_date, timeframe
            )
            
            if candles:
                symbol_trades = engine.run_single_symbol_backtest(
                    symbol, candles, daily_high_low, parameters
                )
                all_trades.extend(symbol_trades)
        
        # Calculate metrics
        metrics = engine.calculate_metrics(all_trades, capital)
        
        # Prepare detailed trades for storage
        detailed_trades = [
            {
                'symbol': trade.symbol,
                'trade_type': trade.trade_type,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'entry_time': trade.entry_time.isoformat(),
                'exit_time': trade.exit_time.isoformat(),
                'quantity': trade.quantity,
                'stop_loss': trade.stop_loss,
                'target_price': trade.target_price,
                'pnl': trade.pnl,
                'pnl_percentage': trade.pnl_percentage,
                'exit_reason': trade.exit_reason
            }
            for trade in all_trades
        ]
        
        # Save results to database
        result = BacktestResult(
            user_id=user_id,
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            win_rate=metrics['win_rate'],
            total_pnl=metrics['total_pnl'],
            total_pnl_percentage=metrics['total_pnl_percentage'],
            max_drawdown=metrics['max_drawdown'],
            max_drawdown_percentage=metrics['max_drawdown_percentage'],
            sharpe_ratio=metrics['sharpe_ratio'],
            parameters=parameters,
            detailed_trades=detailed_trades
        )
        
        db.add(result)
        db.commit()
        db.refresh(result)
        
        logger.info(f"Backtest completed: {metrics['total_trades']} trades, {metrics['win_rate']:.1f}% win rate")
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error running backtest: {e}")
        raise
    finally:
        db.close()
