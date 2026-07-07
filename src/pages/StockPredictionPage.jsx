import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import "../Dashboard.css";

const StockPredictionPage = () => {
  const { user, token } = useAuth();
  const isAuthenticated = token && token.length > 0;
  const [activeTab, setActiveTab] = useState("single");
  const [symbol, setSymbol] = useState("");
  const [timeframe, setTimeframe] = useState("1D");
  const [prediction, setPrediction] = useState(null);
  const [batchPredictions, setBatchPredictions] = useState([]);
  const [marketScan, setMarketScan] = useState([]);
  const [topPicks, setTopPicks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [batchSymbols, setBatchSymbols] = useState("");
  const [scanFilters, setScanFilters] = useState({
    minConfidence: 70,
    verdictFilter: ""
  });

  const predictStock = useCallback(async () => {
    if (!symbol.trim()) return;
    
    // Check if user is authenticated
    if (!isAuthenticated) {
      alert("Please log in to use prediction features.");
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post(
        `${getApiBase()}/prediction/predict/${symbol.toUpperCase()}`,
        {},
        {
          params: { timeframe },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setPrediction(response.data);
      setError(null);
    } catch (error) {
      console.error("Error predicting stock:", error);
      setError(error.message || "Error predicting stock");
      if (error.response?.status === 401) {
        alert("Please log in to use prediction features.");
      } else if (error.response?.status === 500) {
        alert("Server error occurred. Please try again later.");
      } else {
        alert("Error predicting stock. Please check the symbol and try again.");
      }
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe, isAuthenticated]);

  const predictBatch = useCallback(async () => {
    const symbols = batchSymbols.split(',').map(s => s.trim()).filter(s => s);
    if (symbols.length === 0) return;
    
    if (!isAuthenticated) {
      alert("Please log in to use prediction features.");
      return;
    }
    
    try {
      setLoading(true);
      const response = await axios.post(
        `${getApiBase()}/prediction/predict-batch`,
        { symbols, timeframe },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setBatchPredictions(response.data);
    } catch (error) {
      console.error("Error in batch prediction:", error);
      alert("Error in batch prediction. Please check the symbols and try again.");
    } finally {
      setLoading(false);
    }
  }, [batchSymbols, timeframe, isAuthenticated]);

  const scanMarket = useCallback(async () => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      alert("Please log in to use prediction features.");
      return;
    }
    
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('min_confidence', scanFilters.minConfidence);
      if (scanFilters.verdictFilter) {
        params.append('verdict_filter', scanFilters.verdictFilter);
      }

      const response = await axios.get(
        `${getApiBase()}/prediction/market-scan?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMarketScan(response.data);
    } catch (error) {
      console.error("Error scanning market:", error);
      if (error.response?.status === 401) {
        alert("Please log in to use prediction features.");
      } else {
        alert("Error scanning market. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }, [scanFilters, isAuthenticated]);

  const getTopPicks = useCallback(async (category = "all") => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      alert("Please log in to use prediction features.");
      return;
    }
    
    try {
      setLoading(true);
      const response = await axios.get(
        `${getApiBase()}/prediction/top-picks?category=${category}&limit=10`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTopPicks(response.data);
    } catch (error) {
      console.error("Error getting top picks:", error);
      if (error.response?.status === 401) {
        alert("Please log in to use prediction features.");
      } else {
        alert("Error getting top picks. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (activeTab === "market-scan") {
      scanMarket();
    } else if (activeTab === "top-picks") {
      getTopPicks();
    }
  }, [activeTab, scanMarket, getTopPicks]);

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case "STRONG_BUY": return "#10b981";
      case "BUY": return "#34d399";
      case "HOLD": return "#6b7280";
      case "SELL": return "#f87171";
      case "STRONG_SELL": return "#ef4444";
      default: return "#6b7280";
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 85) return "#10b981";
    if (confidence >= 75) return "#34d399";
    if (confidence >= 65) return "#f59e0b";
    return "#ef4444";
  };

  const formatPrice = (price) => `₹${price.toFixed(2)}`;

  const formatScore = (score) => `${score.toFixed(0)}/100`;

  // Authentication is checked above via isAuthenticated
  
  // If user is not authenticated, show login prompt
  if (!isAuthenticated) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>AI Stock Prediction Engine</h1>
          <p>Advanced AI-powered stock analysis with ML predictions and technical indicators</p>
        </div>
        
        <div className="login-prompt-card">
          <div className="login-prompt-content">
            <h2>🔐 Login Required</h2>
            <p>Please log in to access the AI Stock Prediction Engine features.</p>
            <div className="login-prompt-features">
              <h3>Available Features:</h3>
              <ul>
                <li>📊 Single Stock Prediction with ML-powered verdicts</li>
                <li>📈 Batch Analysis for multiple stocks</li>
                <li>🔍 Market Scanner for high-confidence opportunities</li>
                <li>⭐ Curated Top Picks by category</li>
                <li>🎯 Multi-timeframe analysis (1D, 1W, 1M)</li>
                <li>📉 Risk assessment and target prices</li>
              </ul>
            </div>
            <div className="login-prompt-actions">
              <button 
                className="login-button"
                onClick={() => window.location.href = '/login'}
              >
                Go to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>AI Stock Prediction Engine</h1>
        <p>Advanced ML-powered stock analysis with accurate verdicts</p>
      </div>

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={`tab-btn ${activeTab === "single" ? "active" : ""}`}
          onClick={() => setActiveTab("single")}
        >
          Single Stock
        </button>
        <button 
          className={`tab-btn ${activeTab === "batch" ? "active" : ""}`}
          onClick={() => setActiveTab("batch")}
        >
          Batch Analysis
        </button>
        <button 
          className={`tab-btn ${activeTab === "market-scan" ? "active" : ""}`}
          onClick={() => setActiveTab("market-scan")}
        >
          Market Scan
        </button>
        <button 
          className={`tab-btn ${activeTab === "top-picks" ? "active" : ""}`}
          onClick={() => setActiveTab("top-picks")}
        >
          Top Picks
        </button>
      </div>

      {/* Single Stock Prediction */}
      {activeTab === "single" && (
        <div className="prediction-content">
          <div className="prediction-form">
            <div className="form-group">
              <label>Stock Symbol:</label>
              <input
                type="text"
                placeholder="Enter symbol (e.g., RELIANCE)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
            </div>
            <div className="form-group">
              <label>Timeframe:</label>
              <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                <option value="1D">1 Day</option>
                <option value="1W">1 Week</option>
                <option value="1M">1 Month</option>
              </select>
            </div>
            <button 
              className="btn-primary" 
              onClick={predictStock} 
              disabled={loading || !symbol.trim()}
            >
              {loading ? "Analyzing..." : "Predict Stock"}
            </button>
          </div>

          {prediction && (
            <div className="prediction-result">
              <div className="prediction-header">
                <h2>{prediction.symbol}</h2>
                <div className="verdict-badge" style={{ backgroundColor: getVerdictColor(prediction.verdict) }}>
                  {prediction.verdict.replace("_", " ")}
                </div>
                <div className="confidence-badge" style={{ backgroundColor: getConfidenceColor(prediction.confidence) }}>
                  {prediction.confidence.toFixed(0)}% Confidence
                </div>
              </div>

              <div className="prediction-grid">
                <div className="prediction-card">
                  <h3>Price Analysis</h3>
                  <div className="price-info">
                    <div className="price-row">
                      <span>Current Price:</span>
                      <strong>{formatPrice(prediction.current_price)}</strong>
                    </div>
                    <div className="price-row">
                      <span>Target Price:</span>
                      <strong style={{ color: "#10b981" }}>{formatPrice(prediction.target_price)}</strong>
                    </div>
                    <div className="price-row">
                      <span>Stop Loss:</span>
                      <strong style={{ color: "#ef4444" }}>{formatPrice(prediction.stop_loss)}</strong>
                    </div>
                    <div className="price-row">
                      <span>Risk/Reward:</span>
                      <strong>{prediction.risk_reward_ratio.toFixed(2)}</strong>
                    </div>
                  </div>
                </div>

                <div className="prediction-card">
                  <h3>Analysis Scores</h3>
                  <div className="scores-grid">
                    <div className="score-item">
                      <span>Technical:</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${prediction.technical_score}%` }}></div>
                        <span>{formatScore(prediction.technical_score)}</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <span>Momentum:</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${prediction.momentum_score}%` }}></div>
                        <span>{formatScore(prediction.momentum_score)}</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <span>Volume:</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${prediction.volume_score}%` }}></div>
                        <span>{formatScore(prediction.volume_score)}</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <span>Sentiment:</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${prediction.sentiment_score}%` }}></div>
                        <span>{formatScore(prediction.sentiment_score)}</span>
                      </div>
                    </div>
                    <div className="score-item">
                      <span>Overall:</span>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${prediction.overall_score}%` }}></div>
                        <span>{formatScore(prediction.overall_score)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="prediction-card">
                  <h3>AI Recommendation</h3>
                  <p className="recommendation-text">{prediction.recommendation}</p>
                </div>
              </div>

              <div className="prediction-details">
                <div className="details-card">
                  <h3>🔍 Key Indicators</h3>
                  <div className="indicators-grid">
                    {Object.entries(prediction.key_indicators).slice(0, 8).map(([key, value]) => (
                      <div key={key} className="indicator-item">
                        <span>{key.replace(/_/g, ' ').toUpperCase()}:</span>
                        <strong>
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="details-card">
                  <h3>⚠️ Risk Factors</h3>
                  {prediction.risk_factors.length > 0 ? (
                    <ul className="risk-list">
                      {prediction.risk_factors.map((risk, index) => (
                        <li key={index}>{risk}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-risks">No significant risk factors identified.</p>
                  )}
                </div>

                <div className="details-card">
                  <h3>🚀 Opportunities</h3>
                  {prediction.opportunities.length > 0 ? (
                    <ul className="opportunity-list">
                      {prediction.opportunities.map((opportunity, index) => (
                        <li key={index}>{opportunity}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-opportunities">No specific opportunities identified at this time.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Batch Analysis */}
      {activeTab === "batch" && (
        <div className="batch-content">
          <div className="batch-form">
            <div className="form-group">
              <label>Symbols (comma-separated):</label>
              <textarea
                placeholder="Enter symbols separated by commas (e.g., RELIANCE, TCS, HDFCBANK)"
                value={batchSymbols}
                onChange={(e) => setBatchSymbols(e.target.value.toUpperCase())}
                rows={3}
              />
            </div>
            <div className="form-group">
              <label>Timeframe:</label>
              <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                <option value="1D">1 Day</option>
                <option value="1W">1 Week</option>
                <option value="1M">1 Month</option>
              </select>
            </div>
            <button 
              className="btn-primary" 
              onClick={predictBatch} 
              disabled={loading || !batchSymbols.trim()}
            >
              {loading ? "Analyzing..." : "Analyze Batch"}
            </button>
          </div>

          {batchPredictions.length > 0 && (
            <div className="batch-results">
              <h3>Batch Analysis Results</h3>
              <div className="batch-table">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Verdict</th>
                      <th>Confidence</th>
                      <th>Current Price</th>
                      <th>Target</th>
                      <th>Stop Loss</th>
                      <th>Risk/Reward</th>
                      <th>Overall Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batchPredictions.map((pred) => (
                      <tr key={pred.symbol}>
                        <td className="symbol-cell">{pred.symbol}</td>
                        <td>
                          <span className="verdict-badge-small" style={{ backgroundColor: getVerdictColor(pred.verdict) }}>
                            {pred.verdict.replace("_", " ")}
                          </span>
                        </td>
                        <td>
                          <span className="confidence-badge-small" style={{ backgroundColor: getConfidenceColor(pred.confidence) }}>
                            {pred.confidence.toFixed(0)}%
                          </span>
                        </td>
                        <td>{formatPrice(pred.current_price)}</td>
                        <td style={{ color: "#10b981" }}>{formatPrice(pred.target_price)}</td>
                        <td style={{ color: "#ef4444" }}>{formatPrice(pred.stop_loss)}</td>
                        <td>{pred.risk_reward_ratio.toFixed(2)}</td>
                        <td>{formatScore(pred.overall_score)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Market Scan */}
      {activeTab === "market-scan" && (
        <div className="market-scan-content">
          <div className="scan-filters">
            <div className="filter-group">
              <label>Min Confidence:</label>
              <input
                type="number"
                min="50"
                max="95"
                value={scanFilters.minConfidence}
                onChange={(e) => setScanFilters({...scanFilters, minConfidence: parseInt(e.target.value)})}
              />
            </div>
            <div className="filter-group">
              <label>Verdict Filter:</label>
              <select 
                value={scanFilters.verdictFilter} 
                onChange={(e) => setScanFilters({...scanFilters, verdictFilter: e.target.value})}
              >
                <option value="">All</option>
                <option value="STRONG_BUY">Strong Buy</option>
                <option value="BUY">Buy</option>
                <option value="HOLD">Hold</option>
                <option value="SELL">Sell</option>
                <option value="STRONG_SELL">Strong Sell</option>
              </select>
            </div>
            <button className="btn-primary" onClick={scanMarket} disabled={loading}>
              {loading ? "Scanning..." : "Scan Market"}
            </button>
          </div>

          {marketScan.length > 0 && (
            <div className="scan-results">
              <h3>Market Scan Results ({marketScan.length} stocks found)</h3>
              <div className="scan-table">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Verdict</th>
                      <th>Confidence</th>
                      <th>Current Price</th>
                      <th>Target</th>
                      <th>Overall Score</th>
                      <th>Key Insights</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marketScan.map((stock) => (
                      <tr key={stock.symbol}>
                        <td className="symbol-cell">{stock.symbol}</td>
                        <td>
                          <span className="verdict-badge-small" style={{ backgroundColor: getVerdictColor(stock.verdict) }}>
                            {stock.verdict.replace("_", " ")}
                          </span>
                        </td>
                        <td>
                          <span className="confidence-badge-small" style={{ backgroundColor: getConfidenceColor(stock.confidence) }}>
                            {stock.confidence.toFixed(0)}%
                          </span>
                        </td>
                        <td>{formatPrice(stock.current_price)}</td>
                        <td style={{ color: "#10b981" }}>{formatPrice(stock.target_price)}</td>
                        <td>{formatScore(stock.overall_score)}</td>
                        <td className="insights-cell">
                          <div className="insight-tags">
                            {stock.technical_score > 70 && <span className="insight-tag technical">Technical</span>}
                            {stock.momentum_score > 70 && <span className="insight-tag momentum">Momentum</span>}
                            {stock.volume_score > 70 && <span className="insight-tag volume">Volume</span>}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Picks */}
      {activeTab === "top-picks" && (
        <div className="top-picks-content">
          <div className="picks-categories">
            <button className="category-btn active" onClick={() => getTopPicks("all")}>All</button>
            <button className="category-btn" onClick={() => getTopPicks("buy")}>Buy</button>
            <button className="category-btn" onClick={() => getTopPicks("sell")}>Sell</button>
            <button className="category-btn" onClick={() => getTopPicks("momentum")}>Momentum</button>
            <button className="category-btn" onClick={() => getTopPicks("value")}>Value</button>
          </div>

          {topPicks.length > 0 && (
            <div className="top-picks-results">
              <h3>Top Stock Picks</h3>
              <div className="picks-grid">
                {topPicks.map((stock) => (
                  <div key={stock.symbol} className="pick-card">
                    <div className="pick-header">
                      <h4>{stock.symbol}</h4>
                      <span className="verdict-badge-small" style={{ backgroundColor: getVerdictColor(stock.verdict) }}>
                        {stock.verdict.replace("_", " ")}
                      </span>
                    </div>
                    <div className="pick-details">
                      <div className="pick-price">
                        <span className="current-price">{formatPrice(stock.current_price)}</span>
                        <span className="target-price">Target: {formatPrice(stock.target_price)}</span>
                      </div>
                      <div className="pick-scores">
                        <div className="mini-score">
                          <span>Confidence:</span>
                          <strong style={{ color: getConfidenceColor(stock.confidence) }}>
                            {stock.confidence.toFixed(0)}%
                          </strong>
                        </div>
                        <div className="mini-score">
                          <span>Overall:</span>
                          <strong>{formatScore(stock.overall_score)}</strong>
                        </div>
                      </div>
                      <p className="pick-recommendation">{stock.recommendation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockPredictionPage;
