"""Intraday Breakout Strategy Service - Real-time monitoring and signal generation."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import aiohttp
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from models.db_models import BreakoutStrategy, BreakoutSignal, BreakoutTrade
from database import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class CandleData:
    """Represents a single candlestick with OHLCV data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class MarketData:
    """Real-time market data for a symbol."""
    symbol: str
    current_price: float
    pdh: float  # Previous Day High
    pdl: float  # Previous Day Low
    candles: List[CandleData]
    ema_50: Optional[float] = None


class BreakoutDetector:
    """Core breakout detection and confirmation logic."""
    
    def __init__(self, strong_candle_threshold: float = 0.6, volume_multiplier: float = 1.5):
        self.strong_candle_threshold = strong_candle_threshold
        self.volume_multiplier = volume_multiplier
    
    def is_strong_candle(self, candle: CandleData, avg_volume_5: float) -> Tuple[bool, float, float]:
        """
        Check if candle is strong based on body size and volume.
        
        Returns:
            (is_strong, body_percentage, volume_ratio)
        """
        # Calculate body percentage
        candle_range = candle.high - candle.low
        if candle_range == 0:
            return False, 0.0, 0.0
        
        body_size = abs(candle.close - candle.open)
        body_percentage = body_size / candle_range
        
        # Calculate volume ratio
        volume_ratio = candle.volume / avg_volume_5 if avg_volume_5 > 0 else 0.0
        
        # Check conditions
        is_strong = (
            body_percentage >= self.strong_candle_threshold and
            volume_ratio >= self.volume_multiplier
        )
        
        return is_strong, body_percentage, volume_ratio
    
    def detect_breakout(self, market_data: MarketData, strategy: BreakoutStrategy) -> Optional[Dict]:
        """
        Enhanced breakout detection with multiple profitability filters.
        
        Returns:
            Signal dict or None if no breakout detected
        """
        if not market_data.candles or len(market_data.candles) < 10:
            return None
        
        latest_candle = market_data.candles[-1]
        
        # Calculate average volume of last 5 candles
        recent_candles = market_data.candles[-6:-1] if len(market_data.candles) >= 6 else market_data.candles[:-1]
        if not recent_candles:
            return None
        
        avg_volume_5 = sum(c.volume for c in recent_candles) / len(recent_candles)
        
        # Enhanced volume analysis - check for volume spike
        volume_spike_threshold = strategy.volume_multiplier * 1.5  # Higher threshold for better signals
        
        # Price momentum check - ensure strong momentum
        price_momentum = self.calculate_price_momentum(market_data.candles[-5:])
        
        # Volatility filter - avoid low volatility breakouts
        volatility = self.calculate_volatility(market_data.candles[-10:])
        min_volatility = 0.005  # 0.5% minimum volatility
        
        if volatility < min_volatility:
            return None
        
        # Time-based filter - avoid first 15 minutes (high noise)
        current_time = latest_candle.timestamp.time()
        if datetime.strptime("09:15", "%H:%M").time() <= current_time <= datetime.strptime("09:30", "%H:%M").time():
            return None
        
        # Check for bullish breakout (above PDH)
        if latest_candle.close > market_data.pdh:
            # Additional filters for BUY signals
            if not self.validate_buy_signal(market_data, latest_candle, strategy):
                return None
                
            is_strong, body_pct, vol_ratio = self.is_strong_candle(latest_candle, avg_volume_5)
            
            # Enhanced conditions for higher probability trades
            if (is_strong and 
                vol_ratio >= volume_spike_threshold and
                price_momentum > 0.002 and  # Positive momentum
                latest_candle.close > market_data.pdh * 1.001):  # Clear breakout (0.1% above PDH)
                
                return {
                    'symbol': market_data.symbol,
                    'type': 'BUY',
                    'price': latest_candle.close,
                    'pdh': market_data.pdh,
                    'pdl': market_data.pdl,
                    'candle': latest_candle,
                    'avg_volume_5': avg_volume_5,
                    'body_percentage': body_pct,
                    'volume_ratio': vol_ratio,
                    'momentum': price_momentum,
                    'volatility': volatility,
                    'confidence': self.calculate_signal_confidence(body_pct, vol_ratio, price_momentum)
                }
        
        # Check for bearish breakout (below PDL)
        elif latest_candle.close < market_data.pdl:
            # Additional filters for SELL signals
            if not self.validate_sell_signal(market_data, latest_candle, strategy):
                return None
                
            is_strong, body_pct, vol_ratio = self.is_strong_candle(latest_candle, avg_volume_5)
            
            # Enhanced conditions for higher probability trades
            if (is_strong and 
                vol_ratio >= volume_spike_threshold and
                price_momentum < -0.002 and  # Negative momentum
                latest_candle.close < market_data.pdl * 0.999):  # Clear breakdown (0.1% below PDL)
                
                return {
                    'symbol': market_data.symbol,
                    'type': 'SELL',
                    'price': latest_candle.close,
                    'pdh': market_data.pdh,
                    'pdl': market_data.pdl,
                    'candle': latest_candle,
                    'avg_volume_5': avg_volume_5,
                    'body_percentage': body_pct,
                    'volume_ratio': vol_ratio,
                    'momentum': price_momentum,
                    'volatility': volatility,
                    'confidence': self.calculate_signal_confidence(body_pct, vol_ratio, abs(price_momentum))
                }
        
        return None
    
    def calculate_price_momentum(self, candles: List[CandleData]) -> float:
        """Calculate price momentum over recent candles."""
        if len(candles) < 2:
            return 0.0
        
        first_close = candles[0].close
        last_close = candles[-1].close
        return (last_close - first_close) / first_close
    
    def calculate_volatility(self, candles: List[CandleData]) -> float:
        """Calculate price volatility using standard deviation."""
        if len(candles) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(candles)):
            ret = (candles[i].close - candles[i-1].close) / candles[i-1].close
            returns.append(ret)
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def validate_buy_signal(self, market_data: MarketData, candle: CandleData, strategy: BreakoutStrategy) -> bool:
        """Additional validation for BUY signals to improve success rate."""
        # Avoid buying if price is too far from moving averages
        if len(market_data.candles) >= 20:
            recent_closes = [c.close for c in market_data.candles[-20:]]
            sma_20 = sum(recent_closes) / len(recent_closes)
            
            # Don't buy if price is > 3% above 20 SMA (overbought)
            if candle.close > sma_20 * 1.03:
                return False
        
        # Check if recent candles show upward trend
        if len(market_data.candles) >= 3:
            last_3_candles = market_data.candles[-3:]
            if (last_3_candles[0].close > last_3_candles[1].close > last_3_candles[2].close):
                return True  # Strong uptrend
        
        return True
    
    def validate_sell_signal(self, market_data: MarketData, candle: CandleData, strategy: BreakoutStrategy) -> bool:
        """Additional validation for SELL signals to improve success rate."""
        # Avoid selling if price is too far below moving averages
        if len(market_data.candles) >= 20:
            recent_closes = [c.close for c in market_data.candles[-20:]]
            sma_20 = sum(recent_closes) / len(recent_closes)
            
            # Don't sell if price is < 3% below 20 SMA (oversold)
            if candle.close < sma_20 * 0.97:
                return False
        
        # Check if recent candles show downward trend
        if len(market_data.candles) >= 3:
            last_3_candles = market_data.candles[-3:]
            if (last_3_candles[0].close < last_3_candles[1].close < last_3_candles[2].close):
                return True  # Strong downtrend
        
        return True
    
    def calculate_signal_confidence(self, body_pct: float, vol_ratio: float, momentum: float) -> float:
        """Calculate signal confidence score (0-100)."""
        confidence = 50  # Base confidence
        
        # Add points for strong candle body
        if body_pct > 0.7:
            confidence += 20
        elif body_pct > 0.6:
            confidence += 10
        
        # Add points for high volume
        if vol_ratio > 3.0:
            confidence += 20
        elif vol_ratio > 2.0:
            confidence += 10
        
        # Add points for strong momentum
        if abs(momentum) > 0.01:
            confidence += 10
        elif abs(momentum) > 0.005:
            confidence += 5
        
        return min(confidence, 100)


class RiskManager:
    """Risk management and position sizing calculations."""
    
    @staticmethod
    def calculate_position_size(
        capital: float, 
        risk_per_trade: float, 
        entry_price: float, 
        stop_loss: float
    ) -> float:
        """Calculate position size based on risk percentage."""
        risk_amount = capital * (risk_per_trade / 100)
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return 0.0
        
        position_size = risk_amount / risk_per_share
        return position_size
    
    @staticmethod
    def calculate_stop_loss_target(
        signal_type: str, 
        entry_price: float, 
        candle_high: float,
        candle_low: float,
        risk_reward_ratio: float = 2.0,
        volatility: float = 0.01,
        confidence: float = 70
    ) -> Tuple[float, float]:
        """
        Enhanced stop loss and target calculation with dynamic adjustments.
        
        Returns:
            (stop_loss, target_price)
        """
        # Dynamic risk adjustment based on volatility and confidence
        volatility_multiplier = min(max(volatility * 100, 0.5), 2.0)  # 0.5x to 2x based on volatility
        confidence_multiplier = confidence / 100  # Higher confidence = tighter stops
        
        if signal_type == 'BUY':
            # Dynamic stop loss based on volatility and confidence
            if confidence >= 80:
                # High confidence - tighter stop
                stop_loss = candle_low * (1 - 0.002 * volatility_multiplier)  # 0.2% to 0.4% below low
            elif confidence >= 70:
                # Medium confidence - standard stop
                stop_loss = candle_low * (1 - 0.005 * volatility_multiplier)  # 0.5% to 1% below low
            else:
                # Low confidence - wider stop for safety
                stop_loss = candle_low * (1 - 0.008 * volatility_multiplier)  # 0.8% to 1.6% below low
            
            # Ensure stop loss is not too far from entry
            max_stop_distance = entry_price * 0.02  # Maximum 2% risk
            if entry_price - stop_loss > max_stop_distance:
                stop_loss = entry_price - max_stop_distance
            
            risk_per_share = entry_price - stop_loss
            
            # Dynamic target based on confidence and market conditions
            if confidence >= 80:
                # High confidence - more aggressive target
                target_multiplier = risk_reward_ratio * 1.2
            elif confidence >= 70:
                # Standard target
                target_multiplier = risk_reward_ratio
            else:
                # Low confidence - conservative target
                target_multiplier = risk_reward_ratio * 0.8
            
            target_price = entry_price + (risk_per_share * target_multiplier)
            
            # Add profit buffer for high-volatility stocks
            if volatility > 0.02:  # High volatility (>2%)
                target_price *= 1.1  # Add 10% buffer
                
        else:  # SELL
            # Dynamic stop loss for short positions
            if confidence >= 80:
                # High confidence - tighter stop
                stop_loss = candle_high * (1 + 0.002 * volatility_multiplier)  # 0.2% to 0.4% above high
            elif confidence >= 70:
                # Medium confidence - standard stop
                stop_loss = candle_high * (1 + 0.005 * volatility_multiplier)  # 0.5% to 1% above high
            else:
                # Low confidence - wider stop for safety
                stop_loss = candle_high * (1 + 0.008 * volatility_multiplier)  # 0.8% to 1.6% above high
            
            # Ensure stop loss is not too far from entry
            max_stop_distance = entry_price * 0.02  # Maximum 2% risk
            if stop_loss - entry_price > max_stop_distance:
                stop_loss = entry_price + max_stop_distance
            
            risk_per_share = stop_loss - entry_price
            
            # Dynamic target for short positions
            if confidence >= 80:
                # High confidence - more aggressive target
                target_multiplier = risk_reward_ratio * 1.2
            elif confidence >= 70:
                # Standard target
                target_multiplier = risk_reward_ratio
            else:
                # Low confidence - conservative target
                target_multiplier = risk_reward_ratio * 0.8
            
            target_price = entry_price - (risk_per_share * target_multiplier)
            
            # Add profit buffer for high-volatility stocks
            if volatility > 0.02:  # High volatility (>2%)
                target_price *= 0.9  # Add 10% buffer for shorts
        
        return stop_loss, target_price


class DataFetcher:
    """Real-time and historical data fetching."""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_previous_day_high_low(self, symbol: str) -> Tuple[float, float]:
        """Fetch previous day's high and low prices."""
        try:
            # Use yfinance for historical data
            ticker = yf.Ticker(f"{symbol}.NS")  # NSE stocks
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                prev_day = hist.iloc[-2]
                return float(prev_day['High']), float(prev_day['Low'])
            
            return 0.0, 0.0
        except Exception as e:
            logger.error(f"Error fetching previous day data for {symbol}: {e}")
            return 0.0, 0.0
    
    async def get_intraday_data(self, symbol: str, interval: str = "1m") -> List[CandleData]:
        """Fetch intraday candlestick data."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period="1d", interval=interval)
            
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
            
            return candles
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            return float(info.get('currentPrice', 0)) or float(info.get('regularMarketPrice', 0))
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return 0.0
    
    async def calculate_ema(self, symbol: str, period: int = 50) -> Optional[float]:
        """Calculate EMA for trend filtering."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period=f"{period * 2}d")  # Get enough data
            
            if len(hist) >= period:
                closes = hist['Close'].values
                ema = pd.Series(closes).ewm(span=period, adjust=False).mean()
                return float(ema.iloc[-1])
            
            return None
        except Exception as e:
            logger.error(f"Error calculating EMA for {symbol}: {e}")
            return None


class BreakoutStrategyService:
    """Main service for running intraday breakout strategies."""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.detector = BreakoutDetector()
        self.risk_manager = RiskManager()
        self.active_monitors: Dict[int, asyncio.Task] = {}
    
    def is_in_session(self, strategy: BreakoutStrategy) -> bool:
        """Check if current time is within allowed trading session."""
        if not strategy.enable_session_filter:
            return True
        
        now = datetime.now().time()
        start_time = datetime.strptime(strategy.session_start, "%H:%M").time()
        end_time = datetime.strptime(strategy.session_end, "%H:%M").time()
        
        return start_time <= now <= end_time
    
    def can_take_trade(self, strategy: BreakoutStrategy, db: Session) -> bool:
        """Check if strategy can take new trade based on limits."""
        today = datetime.now().date()
        
        # Check daily trade limit
        today_trades = db.query(BreakoutTrade).filter(
            BreakoutTrade.strategy_id == strategy.id,
            BreakoutTrade.entry_time >= today,
            BreakoutTrade.status == "OPEN"
        ).count()
        
        if today_trades >= strategy.max_daily_trades:
            return False
        
        # Check consecutive losses
        recent_trades = db.query(BreakoutTrade).filter(
            BreakoutTrade.strategy_id == strategy.id,
            BreakoutTrade.status == "CLOSED"
        ).order_by(BreakoutTrade.exit_time.desc()).limit(strategy.stop_after_losses).all()
        
        if len(recent_trades) >= strategy.stop_after_losses:
            all_losses = all(trade.pnl and trade.pnl < 0 for trade in recent_trades)
            if all_losses:
                return False
        
        return True
    
    async def monitor_symbol(self, strategy: BreakoutStrategy, symbol: str):
        """Monitor a single symbol for breakout signals."""
        logger.info(f"Starting monitor for {symbol} in strategy {strategy.name}")
        
        async with self.data_fetcher:
            while strategy.active:
                try:
                    # Check session timing
                    if not self.is_in_session(strategy):
                        await asyncio.sleep(60)  # Wait 1 minute
                        continue
                    
                    # Get market data
                    pdh, pdl = await self.data_fetcher.get_previous_day_high_low(symbol)
                    if pdh == 0 or pdl == 0:
                        await asyncio.sleep(60)
                        continue
                    
                    candles = await self.data_fetcher.get_intraday_data(symbol, strategy.timeframe)
                    if not candles:
                        await asyncio.sleep(60)
                        continue
                    
                    current_price = await self.data_fetcher.get_current_price(symbol)
                    
                    # Calculate EMA if trend filter is enabled
                    ema_50 = None
                    if strategy.enable_trend_filter:
                        ema_50 = await self.data_fetcher.calculate_ema(symbol, strategy.trend_ema_period)
                    
                    market_data = MarketData(
                        symbol=symbol,
                        current_price=current_price,
                        pdh=pdh,
                        pdl=pdl,
                        candles=candles,
                        ema_50=ema_50
                    )
                    
                    # Apply trend filter
                    if strategy.enable_trend_filter and ema_50:
                        if current_price < ema_50:
                            await asyncio.sleep(60)
                            continue
                    
                    # Detect breakout
                    signal = self.detector.detect_breakout(market_data, strategy)
                    if signal:
                        await self.handle_signal(strategy, signal)
                    
                    # Wait for next candle
                    interval_seconds = 60 if strategy.timeframe == "1m" else 300
                    await asyncio.sleep(interval_seconds)
                    
                except Exception as e:
                    logger.error(f"Error monitoring {symbol}: {e}")
                    await asyncio.sleep(60)
    
    async def handle_signal(self, strategy: BreakoutStrategy, signal: Dict):
        """Handle detected breakout signal."""
        db = SessionLocal()
        try:
            # Check if we can take this trade
            if not self.can_take_trade(strategy, db):
                logger.info(f"Strategy {strategy.name} cannot take new trade")
                return
            
            # Calculate stop loss and target with enhanced parameters
            stop_loss, target_price = self.risk_manager.calculate_stop_loss_target(
                signal['type'],
                signal['price'],
                signal['candle'].high,
                signal['candle'].low,
                strategy.risk_reward_ratio,
                signal.get('volatility', 0.01),
                signal.get('confidence', 70)
            )
            
            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                strategy.capital,
                strategy.risk_per_trade,
                signal['price'],
                stop_loss
            )
            
            # Save signal
            db_signal = BreakoutSignal(
                strategy_id=strategy.id,
                symbol=signal['symbol'],
                signal_type=signal['type'],
                signal_time=datetime.now(),
                price=signal['price'],
                pdh=signal['pdh'],
                pdl=signal['pdl'],
                candle_close=signal['candle'].close,
                candle_high=signal['candle'].high,
                candle_low=signal['candle'].low,
                candle_volume=signal['candle'].volume,
                avg_volume_5=signal['avg_volume_5'],
                body_percentage=signal['body_percentage'],
                volume_ratio=signal['volume_ratio'],
                confirmed=True
            )
            db.add(db_signal)
            db.flush()
            
            # Create trade
            trade = BreakoutTrade(
                strategy_id=strategy.id,
                signal_id=db_signal.id,
                symbol=signal['symbol'],
                trade_type=signal['type'],
                entry_price=signal['price'],
                stop_loss=stop_loss,
                target_price=target_price,
                quantity=quantity,
                entry_time=datetime.now(),
                status="OPEN"
            )
            db.add(trade)
            db.commit()
            
            logger.info(f"Created {signal['type']} trade for {signal['candle'].timestamp} at {signal['price']}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling signal: {e}")
        finally:
            db.close()
    
    async def start_strategy(self, strategy_id: int):
        """Start monitoring a strategy."""
        db = SessionLocal()
        try:
            strategy = db.query(BreakoutStrategy).filter(BreakoutStrategy.id == strategy_id).first()
            if not strategy or not strategy.active:
                return
            
            # Cancel existing monitor for this strategy
            if strategy_id in self.active_monitors:
                self.active_monitors[strategy_id].cancel()
            
            # Start monitoring all symbols
            tasks = []
            for symbol in strategy.symbols:
                task = asyncio.create_task(self.monitor_symbol(strategy, symbol))
                tasks.append(task)
            
            # Store tasks
            self.active_monitors[strategy_id] = asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error starting strategy {strategy_id}: {e}")
        finally:
            db.close()
    
    def stop_strategy(self, strategy_id: int):
        """Stop monitoring a strategy."""
        if strategy_id in self.active_monitors:
            self.active_monitors[strategy_id].cancel()
            del self.active_monitors[strategy_id]
    
    async def get_active_signals(self, strategy_id: int) -> List[Dict]:
        """Get active signals for a strategy."""
        db = SessionLocal()
        try:
            signals = db.query(BreakoutSignal).filter(
                BreakoutSignal.strategy_id == strategy_id,
                BreakoutSignal.confirmed == True,
                BreakoutSignal.executed == False
            ).order_by(BreakoutSignal.signal_time.desc()).all()
            
            return [
                {
                    'id': s.id,
                    'symbol': s.symbol,
                    'type': s.signal_type,
                    'price': s.price,
                    'pdh': s.pdh,
                    'pdl': s.pdl,
                    'time': s.signal_time.isoformat(),
                    'body_percentage': s.body_percentage,
                    'volume_ratio': s.volume_ratio
                }
                for s in signals
            ]
        finally:
            db.close()


# Global service instance
breakout_service = BreakoutStrategyService()
