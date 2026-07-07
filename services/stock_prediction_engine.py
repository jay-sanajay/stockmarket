"""Advanced stock prediction engine with ML models and technical analysis."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)


class Verdict(Enum):
    """Trading verdict types."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class PredictionResult:
    """Stock prediction result with confidence and risk assessment."""
    symbol: str
    current_price: float
    verdict: Verdict
    confidence: float  # 0-100
    target_price: float
    stop_loss: float
    risk_reward_ratio: float
    time_horizon: str  # "1D", "1W", "1M"
    technical_score: float
    momentum_score: float
    volume_score: float
    sentiment_score: float
    overall_score: float
    key_indicators: Dict[str, Any]
    risk_factors: List[str]
    opportunities: List[str]
    prediction_date: datetime


class TechnicalIndicators:
    """Advanced technical analysis indicators."""
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume."""
        obv = np.where(close > close.shift(), volume, 
                      np.where(close < close.shift(), -volume, 0)).cumsum()
        return pd.Series(obv, index=close.index)


class StockPredictionEngine:
    """Advanced stock prediction engine with ML and technical analysis."""
    
    def __init__(self):
        self.technical_indicators = TechnicalIndicators()
        self.scaler = StandardScaler()
        self.ml_models = {
            'rf': RandomForestClassifier(n_estimators=100, random_state=42),
            'gb': GradientBoostingClassifier(n_estimators=100, random_state=42)
        }
        self.model_trained = False
        
    async def predict_stock(self, symbol: str, timeframe: str = "1D") -> PredictionResult:
        """
        Generate comprehensive stock prediction with ML and technical analysis.
        
        Args:
            symbol: Stock symbol
            timeframe: Prediction timeframe ("1D", "1W", "1M")
            
        Returns:
            PredictionResult with detailed analysis
        """
        try:
            # Fetch historical data
            data = await self._fetch_stock_data(symbol)
            
            if data is None or len(data) < 50:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Calculate technical indicators
            indicators = self._calculate_all_indicators(data)
            
            # Generate technical scores
            technical_score = self._calculate_technical_score(data, indicators)
            momentum_score = self._calculate_momentum_score(data, indicators)
            volume_score = self._calculate_volume_score(data, indicators)
            sentiment_score = self._calculate_sentiment_score(symbol, data, indicators)
            
            # ML prediction
            ml_prediction = await self._ml_predict(data, indicators)
            
            # Generate verdict
            verdict, confidence = self._generate_verdict(
                technical_score, momentum_score, volume_score, 
                sentiment_score, ml_prediction, indicators
            )
            
            # Calculate target and stop loss
            current_price = data['Close'].iloc[-1]
            target_price, stop_loss = self._calculate_targets(
                current_price, verdict, indicators, timeframe
            )
            
            # Risk assessment
            risk_factors = self._identify_risk_factors(indicators, data)
            opportunities = self._identify_opportunities(indicators, data)
            
            # Overall score
            overall_score = (technical_score * 0.3 + momentum_score * 0.25 + 
                           volume_score * 0.2 + sentiment_score * 0.15 + 
                           ml_prediction * 0.1)
            
            return PredictionResult(
                symbol=symbol,
                current_price=current_price,
                verdict=verdict,
                confidence=confidence,
                target_price=target_price,
                stop_loss=stop_loss,
                risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
                time_horizon=timeframe,
                technical_score=technical_score,
                momentum_score=momentum_score,
                volume_score=volume_score,
                sentiment_score=sentiment_score,
                overall_score=overall_score,
                key_indicators=indicators,
                risk_factors=risk_factors,
                opportunities=opportunities,
                prediction_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error predicting {symbol}: {e}")
            raise
    
    async def _fetch_stock_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch historical stock data."""
        try:
            ticker = yf.Ticker(symbol + ".NS")
            data = ticker.history(period=period, interval="1d")
            
            if data.empty:
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _calculate_all_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators."""
        indicators = {}
        
        # Basic indicators
        indicators['rsi'] = self.technical_indicators.calculate_rsi(data['Close'])
        indicators['macd'] = self.technical_indicators.calculate_macd(data['Close'])
        indicators['bollinger'] = self.technical_indicators.calculate_bollinger_bands(data['Close'])
        indicators['stochastic'] = self.technical_indicators.calculate_stochastic(
            data['High'], data['Low'], data['Close']
        )
        indicators['atr'] = self.technical_indicators.calculate_atr(
            data['High'], data['Low'], data['Close']
        )
        indicators['obv'] = self.technical_indicators.calculate_obv(data['Close'], data['Volume'])
        
        # Moving averages
        indicators['sma_20'] = data['Close'].rolling(window=20).mean()
        indicators['sma_50'] = data['Close'].rolling(window=50).mean()
        indicators['sma_200'] = data['Close'].rolling(window=200).mean()
        indicators['ema_12'] = data['Close'].ewm(span=12).mean()
        indicators['ema_26'] = data['Close'].ewm(span=26).mean()
        
        # Price levels
        indicators['current_price'] = data['Close'].iloc[-1]
        indicators['high_20'] = data['High'].rolling(window=20).max().iloc[-1]
        indicators['low_20'] = data['Low'].rolling(window=20).min().iloc[-1]
        indicators['high_52'] = data['High'].rolling(window=252).max().iloc[-1]
        indicators['low_52'] = data['Low'].rolling(window=252).min().iloc[-1]
        
        # Volume indicators
        indicators['volume_sma'] = data['Volume'].rolling(window=20).mean()
        indicators['volume_ratio'] = data['Volume'].iloc[-1] / indicators['volume_sma'].iloc[-1]
        
        return indicators
    
    def _calculate_technical_score(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> float:
        """Calculate technical analysis score (0-100)."""
        score = 50  # Base score
        
        current_price = indicators['current_price']
        current_rsi = indicators['rsi'].iloc[-1]
        current_macd = indicators['macd']['macd'].iloc[-1]
        current_signal = indicators['macd']['signal'].iloc[-1]
        current_bb_upper = indicators['bollinger']['upper'].iloc[-1]
        current_bb_lower = indicators['bollinger']['lower'].iloc[-1]
        current_sma_20 = indicators['sma_20'].iloc[-1]
        current_sma_50 = indicators['sma_50'].iloc[-1]
        current_sma_200 = indicators['sma_200'].iloc[-1]
        current_stoch_k = indicators['stochastic']['k'].iloc[-1]
        current_stoch_d = indicators['stochastic']['d'].iloc[-1]
        
        # RSI scoring
        if 30 <= current_rsi <= 70:
            score += 10  # Neutral zone
        elif current_rsi < 30:
            score += 15  # Oversold (bullish)
        elif current_rsi > 70:
            score -= 15  # Overbought (bearish)
        
        # MACD scoring
        if current_macd > current_signal:
            score += 10  # Bullish crossover
        else:
            score -= 10  # Bearish crossover
        
        # Bollinger Bands scoring
        if current_price < current_bb_lower:
            score += 15  # Oversold
        elif current_price > current_bb_upper:
            score -= 15  # Overbought
        
        # Moving averages scoring
        if current_price > current_sma_20 > current_sma_50 > current_sma_200:
            score += 20  # Strong uptrend
        elif current_price < current_sma_20 < current_sma_50 < current_sma_200:
            score -= 20  # Strong downtrend
        elif current_price > current_sma_20 > current_sma_50:
            score += 10  # Uptrend
        elif current_price < current_sma_20 < current_sma_50:
            score -= 10  # Downtrend
        
        # Stochastic scoring
        if current_stoch_k > current_stoch_d and current_stoch_k < 80:
            score += 10  # Bullish momentum
        elif current_stoch_k < current_stoch_d and current_stoch_k > 20:
            score -= 10  # Bearish momentum
        
        return max(0, min(100, score))
    
    def _calculate_momentum_score(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> float:
        """Calculate momentum score (0-100)."""
        score = 50
        
        # Price momentum
        returns_5d = (data['Close'].iloc[-1] / data['Close'].iloc[-6] - 1) * 100
        returns_20d = (data['Close'].iloc[-1] / data['Close'].iloc[-21] - 1) * 100
        
        if returns_5d > 2:
            score += 15
        elif returns_5d > 0:
            score += 10
        elif returns_5d < -2:
            score -= 15
        elif returns_5d < 0:
            score -= 10
        
        if returns_20d > 5:
            score += 15
        elif returns_20d > 0:
            score += 10
        elif returns_20d < -5:
            score -= 15
        elif returns_20d < 0:
            score -= 10
        
        # Volume momentum
        volume_ratio = indicators['volume_ratio']
        if volume_ratio > 2:
            score += 15
        elif volume_ratio > 1.5:
            score += 10
        elif volume_ratio < 0.5:
            score -= 10
        
        # OBV momentum
        obv_slope = np.polyfit(range(10), indicators['obv'].iloc[-10:], 1)[0]
        if obv_slope > 0:
            score += 10
        else:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_volume_score(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> float:
        """Calculate volume analysis score (0-100)."""
        score = 50
        
        current_volume = data['Volume'].iloc[-1]
        avg_volume = indicators['volume_sma'].iloc[-1]
        volume_ratio = current_volume / avg_volume
        
        # Volume ratio scoring
        if volume_ratio > 3:
            score += 25
        elif volume_ratio > 2:
            score += 20
        elif volume_ratio > 1.5:
            score += 15
        elif volume_ratio > 1.2:
            score += 10
        elif volume_ratio < 0.5:
            score -= 15
        
        # Volume trend
        volume_trend = np.polyfit(range(10), data['Volume'].iloc[-10:], 1)[0]
        if volume_trend > 0:
            score += 10
        else:
            score -= 10
        
        # Price-volume relationship
        price_change = (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100
        if price_change > 0 and volume_ratio > 1.5:
            score += 15  # Accumulation
        elif price_change < 0 and volume_ratio > 1.5:
            score -= 15  # Distribution
        
        return max(0, min(100, score))
    
    def _calculate_sentiment_score(self, symbol: str, data: pd.DataFrame, indicators: Dict[str, Any]) -> float:
        """Calculate market sentiment score (0-100)."""
        score = 50
        
        # Market position relative to 52-week high/low
        current_price = data['Close'].iloc[-1]
        high_52 = indicators['high_52']
        low_52 = indicators['low_52']
        
        position_52 = (current_price - low_52) / (high_52 - low_52) * 100
        
        if position_52 > 80:
            score += 10  # Near highs (bullish)
        elif position_52 < 20:
            score -= 10  # Near lows (bearish)
        
        # Recent volatility (inverse relationship with sentiment)
        volatility = data['Close'].pct_change().rolling(window=20).std().iloc[-1]
        if volatility < 0.02:
            score += 10  # Low volatility (stable)
        elif volatility > 0.05:
            score -= 10  # High volatility (uncertain)
        
        return max(0, min(100, score))
    
    async def _ml_predict(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> float:
        """ML-based prediction score (0-100)."""
        try:
            # Prepare features
            features = self._prepare_features(data, indicators)
            
            if not self.model_trained:
                # Train model with historical data
                await self._train_models(features)
            
            # Predict
            prediction = self._predict_with_models(features)
            return prediction
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return 50  # Neutral score on error
    
    def _prepare_features(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> pd.DataFrame:
        """Prepare features for ML models."""
        features = pd.DataFrame()
        
        # Price features
        features['price_change_1d'] = data['Close'].pct_change(1)
        features['price_change_5d'] = data['Close'].pct_change(5)
        features['price_change_20d'] = data['Close'].pct_change(20)
        
        # Technical indicators
        features['rsi'] = indicators['rsi']
        features['macd'] = indicators['macd']['macd']
        features['macd_signal'] = indicators['macd']['signal']
        features['stoch_k'] = indicators['stochastic']['k']
        features['stoch_d'] = indicators['stochastic']['d']
        
        # Volume features
        features['volume_ratio'] = indicators['volume_ratio']
        features['volume_change'] = data['Volume'].pct_change(1)
        
        # Moving average features
        features['price_sma20_ratio'] = data['Close'] / indicators['sma_20']
        features['price_sma50_ratio'] = data['Close'] / indicators['sma_50']
        features['price_sma200_ratio'] = data['Close'] / indicators['sma_200']
        
        # Volatility
        features['volatility'] = data['Close'].pct_change().rolling(window=20).std()
        
        return features.dropna()
    
    async def _train_models(self, features: pd.DataFrame):
        """Train ML models with historical data."""
        try:
            # Create labels (future price direction)
            labels = (features['price_change_5d'].shift(-1) > 0).astype(int)
            
            # Remove last row (no label)
            X = features.iloc[:-1]
            y = labels.iloc[:-1]
            
            if len(X) < 50:
                return  # Not enough data
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train models
            for name, model in self.ml_models.items():
                model.fit(X_scaled, y)
            
            self.model_trained = True
            logger.info("ML models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training ML models: {e}")
    
    def _predict_with_models(self, features: pd.DataFrame) -> float:
        """Make prediction with trained ML models."""
        if not self.model_trained or len(features) == 0:
            return 50
        
        try:
            # Get latest features
            latest_features = features.iloc[-1:].values
            latest_scaled = self.scaler.transform(latest_features)
            
            # Ensemble prediction
            predictions = []
            for model in self.ml_models.values():
                pred = model.predict_proba(latest_scaled)[0]
                predictions.append(pred[1])  # Probability of upward movement
            
            avg_prediction = np.mean(predictions)
            return avg_prediction * 100
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return 50
    
    def _generate_verdict(self, technical_score: float, momentum_score: float, 
                         volume_score: float, sentiment_score: float, 
                         ml_score: float, indicators: Dict[str, Any]) -> Tuple[Verdict, float]:
        """Generate trading verdict with confidence."""
        
        # Weighted overall score
        overall_score = (technical_score * 0.3 + momentum_score * 0.25 + 
                        volume_score * 0.2 + sentiment_score * 0.15 + 
                        ml_score * 0.1)
        
        # Generate verdict based on score
        if overall_score >= 85:
            verdict = Verdict.STRONG_BUY
            confidence = min(95, overall_score + 5)
        elif overall_score >= 70:
            verdict = Verdict.BUY
            confidence = min(85, overall_score + 10)
        elif overall_score >= 55:
            verdict = Verdict.HOLD
            confidence = 70
        elif overall_score >= 40:
            verdict = Verdict.SELL
            confidence = min(85, (100 - overall_score) + 10)
        else:
            verdict = Verdict.STRONG_SELL
            confidence = min(95, (100 - overall_score) + 5)
        
        return verdict, confidence
    
    def _calculate_targets(self, current_price: float, verdict: Verdict, 
                          indicators: Dict[str, Any], timeframe: str) -> Tuple[float, float]:
        """Calculate target price and stop loss based on verdict and indicators."""
        
        atr = indicators['atr'].iloc[-1]
        volatility = indicators.get('volatility', 0.02)
        
        if verdict in [Verdict.STRONG_BUY, Verdict.BUY]:
            # Bullish targets
            if timeframe == "1D":
                target = current_price + (atr * 1.5)
                stop_loss = current_price - (atr * 0.8)
            elif timeframe == "1W":
                target = current_price + (atr * 3)
                stop_loss = current_price - (atr * 1.5)
            else:  # 1M
                target = current_price + (atr * 5)
                stop_loss = current_price - (atr * 2)
        else:
            # Bearish targets
            if timeframe == "1D":
                target = current_price - (atr * 1.5)
                stop_loss = current_price + (atr * 0.8)
            elif timeframe == "1W":
                target = current_price - (atr * 3)
                stop_loss = current_price + (atr * 1.5)
            else:  # 1M
                target = current_price - (atr * 5)
                stop_loss = current_price + (atr * 2)
        
        return target, stop_loss
    
    def _identify_risk_factors(self, indicators: Dict[str, Any], data: pd.DataFrame) -> List[str]:
        """Identify potential risk factors."""
        risks = []
        
        current_rsi = indicators['rsi'].iloc[-1]
        current_price = indicators['current_price']
        volume_ratio = indicators['volume_ratio']
        
        if current_rsi > 80:
            risks.append("Extremely overbought conditions (RSI > 80)")
        elif current_rsi < 20:
            risks.append("Extremely oversold conditions (RSI < 20)")
        
        if volume_ratio < 0.5:
            risks.append("Low volume indicates lack of interest")
        
        if current_price > indicators['high_52'] * 0.95:
            risks.append("Trading near 52-week highs")
        elif current_price < indicators['low_52'] * 1.05:
            risks.append("Trading near 52-week lows")
        
        volatility = data['Close'].pct_change().rolling(window=20).std().iloc[-1]
        if volatility > 0.05:
            risks.append("High volatility increases risk")
        
        return risks
    
    def _identify_opportunities(self, indicators: Dict[str, Any], data: pd.DataFrame) -> List[str]:
        """Identify trading opportunities."""
        opportunities = []
        
        current_rsi = indicators['rsi'].iloc[-1]
        current_price = indicators['current_price']
        current_macd = indicators['macd']['macd'].iloc[-1]
        current_signal = indicators['macd']['signal'].iloc[-1]
        volume_ratio = indicators['volume_ratio']
        
        if 30 <= current_rsi <= 40 and volume_ratio > 1.5:
            opportunities.append("Oversold with increasing volume - potential reversal")
        
        if current_macd > current_signal and current_macd > 0:
            opportunities.append("MACD bullish crossover confirmed")
        
        if current_price > indicators['sma_20'].iloc[-1] and indicators['sma_20'].iloc[-1] > indicators['sma_50'].iloc[-1]:
            opportunities.append("Golden cross pattern - bullish trend")
        
        if volume_ratio > 2 and current_price > data['Close'].iloc[-2]:
            opportunities.append("High volume breakout pattern")
        
        if current_price < indicators['bollinger']['lower'].iloc[-1]:
            opportunities.append("Price at lower Bollinger Band - potential bounce")
        
        return opportunities


# Global prediction engine
prediction_engine = StockPredictionEngine()
