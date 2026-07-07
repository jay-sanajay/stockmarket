"""REST API endpoints for advanced stock prediction engine."""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dependencies.deps import get_current_user
from services.stock_prediction_engine import prediction_engine, PredictionResult, Verdict

router = APIRouter(prefix="/prediction", tags=["stock-prediction"])


class PredictionResponse(BaseModel):
    symbol: str
    current_price: float
    verdict: str
    confidence: float
    target_price: float
    stop_loss: float
    risk_reward_ratio: float
    time_horizon: str
    technical_score: float
    momentum_score: float
    volume_score: float
    sentiment_score: float
    overall_score: float
    key_indicators: Dict[str, Any]
    risk_factors: List[str]
    opportunities: List[str]
    prediction_date: str
    recommendation: str


class BatchPredictionRequest(BaseModel):
    symbols: List[str] = Field(..., min_items=1, max_items=20, description="List of stock symbols")
    timeframe: str = Field(default="1D", pattern="^(1D|1W|1M)$", description="Prediction timeframe")


@router.post("/predict/{symbol}", response_model=PredictionResponse)
async def predict_stock(
    symbol: str,
    timeframe: str = Query(default="1D", pattern="^(1D|1W|1M)$", description="Prediction timeframe"),
    current_user = Depends(get_current_user)
):
    """Generate stock prediction with comprehensive analysis."""
    try:
        symbol = symbol.upper().strip()
        
        # Generate prediction
        result = await prediction_engine.predict_stock(symbol, timeframe)
        
        # Convert pandas Series to regular Python types for serialization
        serializable_indicators = {}
        for key, value in result.key_indicators.items():
            if hasattr(value, 'iloc'):  # Check if it's a pandas Series
                serializable_indicators[key] = float(value.iloc[-1]) if len(value) > 0 else None
            elif hasattr(value, '__iter__') and not isinstance(value, str):
                serializable_indicators[key] = list(value)
            else:
                serializable_indicators[key] = value
        
        # Format response
        response = PredictionResponse(
            symbol=result.symbol,
            current_price=result.current_price,
            verdict=result.verdict.value,
            confidence=result.confidence,
            target_price=result.target_price,
            stop_loss=result.stop_loss,
            risk_reward_ratio=result.risk_reward_ratio,
            time_horizon=result.time_horizon,
            technical_score=result.technical_score,
            momentum_score=result.momentum_score,
            volume_score=result.volume_score,
            sentiment_score=result.sentiment_score,
            overall_score=result.overall_score,
            key_indicators=serializable_indicators,
            risk_factors=result.risk_factors,
            opportunities=result.opportunities,
            prediction_date=result.prediction_date.isoformat(),
            recommendation=_generate_recommendation(result)
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-batch", response_model=List[PredictionResponse])
async def predict_batch_stocks(
    request: BatchPredictionRequest,
    current_user = Depends(get_current_user)
):
    """Generate predictions for multiple stocks."""
    try:
        predictions = []
        print(f"DEBUG: Batch prediction request received: symbols={request.symbols}, timeframe={request.timeframe}")
        
        for symbol in request.symbols:
            try:
                print(f"DEBUG: Processing symbol: {symbol}")
                result = await prediction_engine.predict_stock(symbol.upper().strip(), request.timeframe)
                print(f"DEBUG: Successfully predicted {symbol}")
                
                # Convert pandas Series to regular Python types for serialization
                serializable_indicators = {}
                for key, value in result.key_indicators.items():
                    if hasattr(value, 'iloc'):  # Check if it's a pandas Series
                        serializable_indicators[key] = float(value.iloc[-1]) if len(value) > 0 else None
                    elif hasattr(value, '__iter__') and not isinstance(value, str):
                        serializable_indicators[key] = list(value)
                    else:
                        serializable_indicators[key] = value
                
                response = PredictionResponse(
                    symbol=result.symbol,
                    current_price=result.current_price,
                    verdict=result.verdict.value,
                    confidence=result.confidence,
                    target_price=result.target_price,
                    stop_loss=result.stop_loss,
                    risk_reward_ratio=result.risk_reward_ratio,
                    time_horizon=result.time_horizon,
                    technical_score=result.technical_score,
                    momentum_score=result.momentum_score,
                    volume_score=result.volume_score,
                    sentiment_score=result.sentiment_score,
                    overall_score=result.overall_score,
                    key_indicators=serializable_indicators,
                    risk_factors=result.risk_factors,
                    opportunities=result.opportunities,
                    prediction_date=result.prediction_date.isoformat(),
                    recommendation=_generate_recommendation(result)
                )
                
                predictions.append(response)
                
            except Exception as e:
                # Continue with other symbols if one fails
                continue
        
        # Sort by overall score
        predictions.sort(key=lambda x: x.overall_score, reverse=True)
        
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-scan")
async def market_scan(
    min_confidence: float = Query(default=70, ge=50, le=95, description="Minimum confidence level"),
    verdict_filter: Optional[str] = Query(None, pattern="^(STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL)$", description="Filter by verdict"),
    current_user = Depends(get_current_user)
):
    """Scan market for stocks with strong predictions."""
    try:
        # Nifty 50 symbols for scanning
        nifty50_symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'BHARTIARTL',
            'INFY', 'KOTAKBANK', 'HINDUNILVR', 'ITC', 'SBIN',
            'LT', 'M&M', 'SUNPHARMA', 'TITAN', 'MARUTI',
            'NTPC', 'POWERGRID', 'ONGC', 'COALINDIA', 'BPCL',
            'GAIL', 'TATASTEEL', 'TECHM', 'GRASIM', 'SHREECEM',
            'JSWSTEEL', 'HINDALCO', 'DIVISLAB', 'DRREDDY', 'ADANIPORTS',
            'ULTRACEMCO', 'BAJFINANCE', 'HDFCLIFE', 'HEROMOTOCO', 'NESTLEIND',
            'CIPLA', 'BRITANNIA', 'UPL', 'EICHERMOT', 'APOLLOHOSP',
            'TATAMOTORS', 'WIPRO', 'HDFC', 'INDUSINDBK', 'SBILIFE'
        ]
        
        predictions = []
        
        for symbol in nifty50_symbols:
            try:
                result = await prediction_engine.predict_stock(symbol, "1D")
                
                # Apply filters
                if result.confidence < min_confidence:
                    continue
                
                if verdict_filter and result.verdict.value != verdict_filter:
                    continue
                
                # Convert pandas Series to regular Python types for serialization
                serializable_indicators = {}
                for key, value in result.key_indicators.items():
                    if hasattr(value, 'iloc'):  # Check if it's a pandas Series
                        serializable_indicators[key] = float(value.iloc[-1]) if len(value) > 0 else None
                    elif hasattr(value, '__iter__') and not isinstance(value, str):
                        serializable_indicators[key] = list(value)
                    else:
                        serializable_indicators[key] = value
                
                response = PredictionResponse(
                    symbol=result.symbol,
                    current_price=result.current_price,
                    verdict=result.verdict.value,
                    confidence=result.confidence,
                    target_price=result.target_price,
                    stop_loss=result.stop_loss,
                    risk_reward_ratio=result.risk_reward_ratio,
                    time_horizon=result.time_horizon,
                    technical_score=result.technical_score,
                    momentum_score=result.momentum_score,
                    volume_score=result.volume_score,
                    sentiment_score=result.sentiment_score,
                    overall_score=result.overall_score,
                    key_indicators=serializable_indicators,
                    risk_factors=result.risk_factors,
                    opportunities=result.opportunities,
                    prediction_date=result.prediction_date.isoformat(),
                    recommendation=_generate_recommendation(result)
                )
                
                predictions.append(response)
                
            except Exception as e:
                continue
        
        # Sort by confidence and overall score
        predictions.sort(key=lambda x: (x.confidence, x.overall_score), reverse=True)
        
        return predictions[:20]  # Return top 20
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-picks")
async def get_top_picks(
    category: str = Query(default="all", pattern="^(buy|sell|momentum|value|all)$", description="Category filter"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of picks to return"),
    current_user = Depends(get_current_user)
):
    """Get top stock picks based on different strategies."""
    try:
        nifty50_symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'BHARTIARTL',
            'INFY', 'KOTAKBANK', 'HINDUNILVR', 'ITC', 'SBIN',
            'LT', 'M&M', 'SUNPHARMA', 'TITAN', 'MARUTI',
            'NTPC', 'POWERGRID', 'ONGC', 'COALINDIA', 'BPCL',
            'GAIL', 'TATASTEEL', 'TECHM', 'GRASIM', 'SHREECEM',
            'JSWSTEEL', 'HINDALCO', 'DIVISLAB', 'DRREDDY', 'ADANIPORTS',
            'ULTRACEMCO', 'BAJFINANCE', 'HDFCLIFE', 'HEROMOTOCO', 'NESTLEIND',
            'CIPLA', 'BRITANNIA', 'UPL', 'EICHERMOT', 'APOLLOHOSP',
            'TATAMOTORS', 'WIPRO', 'HDFC', 'INDUSINDBK', 'SBILIFE'
        ]
        
        predictions = []
        
        for symbol in nifty50_symbols:
            try:
                result = await prediction_engine.predict_stock(symbol, "1W")
                
                # Convert pandas Series to regular Python types for serialization
                serializable_indicators = {}
                for key, value in result.key_indicators.items():
                    if hasattr(value, 'iloc'):  # Check if it's a pandas Series
                        serializable_indicators[key] = float(value.iloc[-1]) if len(value) > 0 else None
                    elif hasattr(value, '__iter__') and not isinstance(value, str):
                        serializable_indicators[key] = list(value)
                    else:
                        serializable_indicators[key] = value
                
                response = PredictionResponse(
                    symbol=result.symbol,
                    current_price=result.current_price,
                    verdict=result.verdict.value,
                    confidence=result.confidence,
                    target_price=result.target_price,
                    stop_loss=result.stop_loss,
                    risk_reward_ratio=result.risk_reward_ratio,
                    time_horizon=result.time_horizon,
                    technical_score=result.technical_score,
                    momentum_score=result.momentum_score,
                    volume_score=result.volume_score,
                    sentiment_score=result.sentiment_score,
                    overall_score=result.overall_score,
                    key_indicators=serializable_indicators,
                    risk_factors=result.risk_factors,
                    opportunities=result.opportunities,
                    prediction_date=result.prediction_date.isoformat(),
                    recommendation=_generate_recommendation(result)
                )
                
                predictions.append(response)
                
            except Exception as e:
                continue
        
        # Filter by category
        if category == "buy":
            predictions = [p for p in predictions if p.verdict in ["STRONG_BUY", "BUY"]]
            predictions.sort(key=lambda x: x.confidence, reverse=True)
        elif category == "sell":
            predictions = [p for p in predictions if p.verdict in ["STRONG_SELL", "SELL"]]
            predictions.sort(key=lambda x: x.confidence, reverse=True)
        elif category == "momentum":
            predictions.sort(key=lambda x: x.momentum_score, reverse=True)
        elif category == "value":
            predictions.sort(key=lambda x: x.technical_score, reverse=True)
        else:  # all
            predictions.sort(key=lambda x: x.overall_score, reverse=True)
        
        return predictions[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prediction-summary/{symbol}")
async def get_prediction_summary(
    symbol: str,
    current_user = Depends(get_current_user)
):
    """Get a summary of prediction for a specific stock."""
    try:
        symbol = symbol.upper().strip()
        
        # Generate predictions for different timeframes
        timeframes = ["1D", "1W", "1M"]
        predictions = {}
        
        for timeframe in timeframes:
            try:
                result = await prediction_engine.predict_stock(symbol, timeframe)
                predictions[timeframe] = {
                    "verdict": result.verdict.value,
                    "confidence": result.confidence,
                    "target_price": result.target_price,
                    "stop_loss": result.stop_loss,
                    "overall_score": result.overall_score,
                    "recommendation": _generate_recommendation(result)
                }
            except Exception as e:
                predictions[timeframe] = None
        
        return {
            "symbol": symbol,
            "predictions": predictions,
            "summary": _generate_summary(predictions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_recommendation(result: PredictionResult) -> str:
    """Generate human-readable recommendation based on prediction result."""
    
    if result.verdict == Verdict.STRONG_BUY:
        return (f"Strong BUY signal with {result.confidence:.0f}% confidence. "
                f"Target: ₹{result.target_price:.2f}, Stop Loss: ₹{result.stop_loss:.2f}. "
                f"Risk/Reward: {result.risk_reward_ratio:.2f}. "
                f"Technical score: {result.technical_score:.0f}/100, "
                f"Momentum: {result.momentum_score:.0f}/100.")
    
    elif result.verdict == Verdict.BUY:
        return (f"BUY signal with {result.confidence:.0f}% confidence. "
                f"Target: ₹{result.target_price:.2f}, Stop Loss: ₹{result.stop_loss:.2f}. "
                f"Risk/Reward: {result.risk_reward_ratio:.2f}. "
                f"Consider position sizing based on risk tolerance.")
    
    elif result.verdict == Verdict.HOLD:
        return (f"HOLD recommendation with {result.confidence:.0f}% confidence. "
                f"Current price: ₹{result.current_price:.2f}. "
                f"Wait for clearer signals before taking action.")
    
    elif result.verdict == Verdict.SELL:
        return (f"SELL signal with {result.confidence:.0f}% confidence. "
                f"Target: ₹{result.target_price:.2f}, Stop Loss: ₹{result.stop_loss:.2f}. "
                f"Risk/Reward: {result.risk_reward_ratio:.2f}. "
                f"Consider reducing exposure.")
    
    else:  # STRONG_SELL
        return (f"Strong SELL signal with {result.confidence:.0f}% confidence. "
                f"Target: ₹{result.target_price:.2f}, Stop Loss: ₹{result.stop_loss:.2f}. "
                f"Risk/Reward: {result.risk_reward_ratio:.2f}. "
                f"Technical score: {result.technical_score:.0f}/100, "
                f"Momentum: {result.momentum_score:.0f}/100. "
                f"Consider exiting position immediately.")


def _generate_summary(predictions: Dict[str, Any]) -> str:
    """Generate a summary of predictions across timeframes."""
    
    valid_predictions = {k: v for k, v in predictions.items() if v is not None}
    
    if not valid_predictions:
        return "No valid predictions available."
    
    # Count verdicts
    verdict_counts = {}
    for pred in valid_predictions.values():
        verdict = pred["verdict"]
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
    
    # Find dominant verdict
    if verdict_counts:
        dominant_verdict = max(verdict_counts, key=verdict_counts.get)
        count = verdict_counts[dominant_verdict]
        
        if dominant_verdict in ["STRONG_BUY", "BUY"]:
            return f"Bullish sentiment across {count}/{len(valid_predictions)} timeframes. Consider buying opportunities."
        elif dominant_verdict in ["STRONG_SELL", "SELL"]:
            return f"Bearish sentiment across {count}/{len(valid_predictions)} timeframes. Consider selling or avoiding."
        else:
            return f"Mixed signals with {count}/{len(valid_predictions)} timeframes suggesting HOLD. Wait for clearer direction."
    
    return "Mixed signals across timeframes. Wait for clearer direction."
