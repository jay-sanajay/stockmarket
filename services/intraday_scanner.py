"""Live intraday stock scanner service for real-time stock monitoring."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, date, time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class IntradayStock:
    """Represents a live intraday stock with key metrics."""
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
    pdh: float  # Previous Day High
    pdl: float  # Previous Day Low
    rsi: Optional[float] = None
    momentum: Optional[float] = None
    volatility: Optional[float] = None
    last_update: datetime = None
    
    def is_breakout_above_pdh(self) -> bool:
        """Check if stock is breaking out above previous day high."""
        return self.current_price > self.pdh * 1.001  # 0.1% above PDH
    
    def is_breakdown_below_pdl(self) -> bool:
        """Check if stock is breaking down below previous day low."""
        return self.current_price < self.pdl * 0.999  # 0.1% below PDL
    
    def is_high_volume(self) -> bool:
        """Check if volume is significantly higher than average."""
        return self.volume_ratio > 1.5
    
    def is_strong_momentum(self) -> bool:
        """Check if stock has strong momentum."""
        return self.momentum is not None and abs(self.momentum) > 0.02


class IntradayScanner:
    """Live intraday stock scanner with real-time data fetching."""
    
    def __init__(self):
        self.nifty50_symbols = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS',
            'INFY.NS', 'KOTAKBANK.NS', 'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS',
            'LT.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'MARUTI.NS',
            'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS', 'COALINDIA.NS', 'BPCL.NS',
            'GAIL.NS', 'TATASTEEL.NS', 'TECHM.NS', 'GRASIM.NS', 'SHREECEM.NS',
            'JSWSTEEL.NS', 'HINDALCO.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'ADANIPORTS.NS',
            'ULTRACEMCO.NS', 'BAJFINANCE.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'NESTLEIND.NS',
            'CIPLA.NS', 'BRITANNIA.NS', 'UPL.NS', 'EICHERMOT.NS', 'APOLLOHOSP.NS',
            'TATAMOTORS.NS', 'WIPRO.NS', 'HDFC.NS', 'INDUSINDBK.NS', 'SBILIFE.NS'
        ]
        
        self.cache: Dict[str, IntradayStock] = {}
        self.last_update: Optional[datetime] = None
        
    async def get_live_stocks(self, symbols: List[str] = None) -> List[IntradayStock]:
        """
        Get live stock data for specified symbols.
        
        Args:
            symbols: List of stock symbols (defaults to Nifty 50)
            
        Returns:
            List of IntradayStock objects with live data
        """
        if symbols is None:
            symbols = self.nifty50_symbols
        
        try:
            # Fetch intraday data
            stocks = []
            
            # Process symbols in batches to avoid rate limits
            batch_size = 10
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                batch_stocks = await self._fetch_batch_data(batch_symbols)
                stocks.extend(batch_stocks)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Sort by volume ratio and change percentage
            stocks.sort(key=lambda x: (x.volume_ratio, abs(x.change_percent)), reverse=True)
            
            self.last_update = datetime.now()
            return stocks
            
        except Exception as e:
            logger.error(f"Error fetching live stocks: {e}")
            return []
    
    async def _fetch_batch_data(self, symbols: List[str]) -> List[IntradayStock]:
        """Fetch data for a batch of symbols."""
        stocks = []
        
        try:
            # Get current day intraday data
            tickers = yf.Tickers(symbols)
            
            # Get previous day data for PDH/PDL
            prev_data = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d", interval="1d")
                    if len(hist) >= 2:
                        prev_day = hist.iloc[-2]
                        prev_data[symbol] = {
                            'pdh': float(prev_day['High']),
                            'pdl': float(prev_day['Low']),
                            'avg_volume': int(prev_day['Volume'])
                        }
                except Exception as e:
                    logger.warning(f"Error fetching previous data for {symbol}: {e}")
                    prev_data[symbol] = {'pdh': 0, 'pdl': 0, 'avg_volume': 0}
            
            # Process current data for each symbol
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if ticker is None:
                        continue
                    
                    # Get intraday data
                    hist = ticker.history(period="1d", interval="5m")
                    if hist.empty:
                        continue
                    
                    latest = hist.iloc[-1]
                    current_price = float(latest['Close'])
                    
                    # Calculate change
                    open_price = float(latest['Open'])
                    change = current_price - open_price
                    change_percent = (change / open_price) * 100 if open_price > 0 else 0
                    
                    # Get company name
                    info = ticker.info
                    name = info.get('shortName', info.get('longName', symbol))
                    
                    # Calculate technical indicators
                    rsi = self._calculate_rsi(hist)
                    momentum = self._calculate_momentum(hist)
                    volatility = self._calculate_volatility(hist)
                    
                    # Create stock object
                    stock = IntradayStock(
                        symbol=symbol.replace('.NS', ''),
                        name=name,
                        current_price=current_price,
                        change=change,
                        change_percent=change_percent,
                        volume=int(latest['Volume']),
                        avg_volume=prev_data[symbol]['avg_volume'],
                        volume_ratio=self._calculate_volume_ratio(int(latest['Volume']), prev_data[symbol]['avg_volume']),
                        high=float(latest['High']),
                        low=float(latest['Low']),
                        open_price=open_price,
                        pdh=prev_data[symbol]['pdh'],
                        pdl=prev_data[symbol]['pdl'],
                        rsi=rsi,
                        momentum=momentum,
                        volatility=volatility,
                        last_update=datetime.now()
                    )
                    
                    stocks.append(stock)
                    self.cache[symbol] = stock
                    
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in batch fetch: {e}")
        
        return stocks
    
    def _calculate_volume_ratio(self, current_volume: int, avg_volume: int) -> float:
        """Calculate volume ratio (current / average)."""
        if avg_volume == 0:
            return 1.0
        return current_volume / avg_volume
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate RSI indicator."""
        try:
            if len(data) < period + 1:
                return None
            
            closes = data['Close']
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            
        except Exception:
            return None
    
    def _calculate_momentum(self, data: pd.DataFrame, period: int = 10) -> Optional[float]:
        """Calculate price momentum."""
        try:
            if len(data) < period:
                return None
            
            current_price = data['Close'].iloc[-1]
            past_price = data['Close'].iloc[-period]
            
            return (current_price - past_price) / past_price
            
        except Exception:
            return None
    
    def _calculate_volatility(self, data: pd.DataFrame, period: int = 20) -> Optional[float]:
        """Calculate price volatility."""
        try:
            if len(data) < period:
                return None
            
            returns = data['Close'].pct_change().dropna()
            volatility = returns.rolling(window=min(period, len(returns))).std().iloc[-1]
            
            return float(volatility) if not pd.isna(volatility) else None
            
        except Exception:
            return None
    
    def get_filtered_stocks(
        self, 
        min_volume_ratio: float = 1.5,
        min_change_percent: float = 1.0,
        show_breakouts: bool = True,
        show_high_volume: bool = True
    ) -> List[IntradayStock]:
        """
        Get filtered stocks based on criteria.
        
        Args:
            min_volume_ratio: Minimum volume ratio
            min_change_percent: Minimum change percentage
            show_breakouts: Show PDH/PDL breakouts
            show_high_volume: Show high volume stocks
            
        Returns:
            Filtered list of stocks
        """
        if not self.cache:
            return []
        
        stocks = list(self.cache.values())
        filtered = []
        
        for stock in stocks:
            # Volume filter
            if show_high_volume and not stock.is_high_volume():
                continue
            
            # Change filter
            if abs(stock.change_percent) < min_change_percent:
                continue
            
            # Breakout filter
            if show_breakouts and not (stock.is_breakout_above_pdh() or stock.is_breakdown_below_pdl()):
                continue
            
            filtered.append(stock)
        
        return sorted(filtered, key=lambda x: abs(x.change_percent), reverse=True)
    
    async def start_monitoring(self, symbols: List[str] = None, update_interval: int = 30):
        """
        Start continuous monitoring of stocks.
        
        Args:
            symbols: List of symbols to monitor
            update_interval: Update interval in seconds
        """
        while True:
            try:
                await self.get_live_stocks(symbols)
                await asyncio.sleep(update_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error


# Global scanner instance
intraday_scanner = IntradayScanner()
