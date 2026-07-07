import React, { useState, useEffect } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import "../Dashboard.css";

const BreakoutStrategyPage = () => {
  const { user } = useAuth();
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [activeTab, setActiveTab] = useState("strategies");
  const [signals, setSignals] = useState([]);
  const [trades, setTrades] = useState([]);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await axios.get(`${getApiBase()}/breakout-strategy/strategies`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setStrategies(response.data);
    } catch (error) {
      console.error("Error fetching strategies:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStrategy = async (strategyId) => {
    try {
      await axios.post(`${getApiBase()}/breakout-strategy/strategies/${strategyId}/start`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      fetchStrategies();
    } catch (error) {
      console.error("Error starting strategy:", error);
      alert(error.response?.data?.detail || "Failed to start strategy");
    }
  };

  const handleStopStrategy = async (strategyId) => {
    try {
      await axios.post(`${getApiBase()}/breakout-strategy/strategies/${strategyId}/stop`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      fetchStrategies();
    } catch (error) {
      console.error("Error stopping strategy:", error);
      alert(error.response?.data?.detail || "Failed to stop strategy");
    }
  };

  const handleDeleteStrategy = async (strategyId) => {
    if (!window.confirm("Are you sure you want to delete this strategy?")) return;
    
    try {
      await axios.delete(`${getApiBase()}/breakout-strategy/strategies/${strategyId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      fetchStrategies();
      if (selectedStrategy?.id === strategyId) {
        setSelectedStrategy(null);
      }
    } catch (error) {
      console.error("Error deleting strategy:", error);
      alert(error.response?.data?.detail || "Failed to delete strategy");
    }
  };

  const closeTrade = async (tradeId) => {
    if (!window.confirm("Are you sure you want to close this trade?")) return;
    
    try {
      await axios.post(`${getApiBase()}/breakout-strategy/trades/${tradeId}/close`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      if (selectedStrategy) {
        fetchStrategyDetails(selectedStrategy);
      }
    } catch (error) {
      console.error("Error closing trade:", error);
      alert(error.response?.data?.detail || "Failed to close trade");
    }
  };

  const fetchStrategyDetails = async (strategy) => {
    setSelectedStrategy(strategy);
    setActiveTab("details");
    
    try {
      const [signalsRes, tradesRes] = await Promise.all([
        axios.get(`${getApiBase()}/breakout-strategy/strategies/${strategy.id}/signals`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        }),
        axios.get(`${getApiBase()}/breakout-strategy/strategies/${strategy.id}/trades`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        })
      ]);
      
      setSignals(signalsRes.data);
      setTrades(tradesRes.data);
    } catch (error) {
      console.error("Error fetching strategy details:", error);
    }
  };

  if (loading) {
    return <div className="loading">Loading strategies...</div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Intraday Breakout Strategy</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
        >
          + Create Strategy
        </button>
      </div>

      <div className="dashboard-tabs">
        <button 
          className={`tab-btn ${activeTab === "strategies" ? "active" : ""}`}
          onClick={() => setActiveTab("strategies")}
        >
          Strategies
        </button>
        {selectedStrategy && (
          <button 
            className={`tab-btn ${activeTab === "details" ? "active" : ""}`}
            onClick={() => setActiveTab("details")}
          >
            {selectedStrategy.name} Details
          </button>
        )}
        <button 
          className={`tab-btn ${activeTab === "backtest" ? "active" : ""}`}
          onClick={() => setActiveTab("backtest")}
        >
          Backtesting
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === "strategies" && (
          <div className="strategies-grid">
            {strategies.length === 0 ? (
              <div className="empty-state">
                <h3>No strategies found</h3>
                <p>Create your first intraday breakout strategy to get started.</p>
                <button 
                  className="btn btn-primary"
                  onClick={() => setShowCreateForm(true)}
                >
                  Create Strategy
                </button>
              </div>
            ) : (
              strategies.map((strategy) => (
                <div key={strategy.id} className="strategy-card">
                  <div className="strategy-header">
                    <h3>{strategy.name}</h3>
                    <div className="strategy-status">
                      <span className={`status-badge ${strategy.active ? "active" : "inactive"}`}>
                        {strategy.active ? "Active" : "Inactive"}
                      </span>
                      {strategy.is_running && (
                        <span className="status-badge running">Running</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="strategy-info">
                    <div className="info-row">
                      <span className="label">Symbols:</span>
                      <span className="value">{strategy.symbols.join(", ")}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">Capital:</span>
                      <span className="value">₹{strategy.capital.toLocaleString()}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">Risk/Trade:</span>
                      <span className="value">{strategy.risk_per_trade}%</span>
                    </div>
                    <div className="info-row">
                      <span className="label">Timeframe:</span>
                      <span className="value">{strategy.timeframe}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">R:R Ratio:</span>
                      <span className="value">1:{strategy.risk_reward_ratio}</span>
                    </div>
                  </div>

                  <div className="strategy-actions">
                    <button 
                      className="btn btn-secondary"
                      onClick={() => fetchStrategyDetails(strategy)}
                    >
                      View Details
                    </button>
                    {strategy.active && (
                      <>
                        {strategy.is_running ? (
                          <button 
                            className="btn btn-danger"
                            onClick={() => handleStopStrategy(strategy.id)}
                          >
                            Stop
                          </button>
                        ) : (
                          <button 
                            className="btn btn-success"
                            onClick={() => handleStartStrategy(strategy.id)}
                          >
                            Start
                          </button>
                        )}
                      </>
                    )}
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDeleteStrategy(strategy.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "details" && selectedStrategy && (
          <div className="strategy-details">
            <div className="details-header">
              <h2>{selectedStrategy.name}</h2>
              <div className="strategy-status">
                <span className={`status-badge ${selectedStrategy.active ? "active" : "inactive"}`}>
                  {selectedStrategy.active ? "Active" : "Inactive"}
                </span>
                {selectedStrategy.is_running && (
                  <span className="status-badge running">Running</span>
                )}
              </div>
            </div>

            <div className="details-tabs">
              <button className="details-tab active">Signals</button>
              <button className="details-tab">Trades</button>
              <button className="details-tab">Settings</button>
            </div>

            <div className="details-content">
              <div className="signals-section">
                <h3>Recent Signals</h3>
                {signals.length === 0 ? (
                  <p>No signals generated yet.</p>
                ) : (
                  <div className="signals-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Time</th>
                          <th>Symbol</th>
                          <th>Type</th>
                          <th>Price</th>
                          <th>PDH</th>
                          <th>PDL</th>
                          <th>Body %</th>
                          <th>Volume</th>
                          <th>Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {signals.map((signal) => (
                          <tr key={signal.id}>
                            <td>{new Date(signal.signal_time).toLocaleString()}</td>
                            <td>{signal.symbol}</td>
                            <td>
                              <span className={`signal-type ${signal.signal_type.toLowerCase()}`}>
                                {signal.signal_type}
                              </span>
                            </td>
                            <td>₹{signal.price.toFixed(2)}</td>
                            <td>₹{signal.pdh.toFixed(2)}</td>
                            <td>₹{signal.pdl.toFixed(2)}</td>
                            <td>{(signal.body_percentage * 100).toFixed(1)}%</td>
                            <td>{signal.volume_ratio.toFixed(1)}x</td>
                            <td>
                              <span className={`confidence-badge ${signal.confidence >= 80 ? 'high' : signal.confidence >= 70 ? 'medium' : 'low'}`}>
                                {signal.confidence || 70}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              <div className="trades-section">
                <h3>Recent Trades</h3>
                {trades.length === 0 ? (
                  <p>No trades executed yet.</p>
                ) : (
                  <div className="trades-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Entry Time</th>
                          <th>Symbol</th>
                          <th>Type</th>
                          <th>Entry</th>
                          <th>Exit</th>
                          <th>P&L</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trades.map((trade) => (
                          <tr key={trade.id}>
                            <td>{new Date(trade.entry_time).toLocaleString()}</td>
                            <td>{trade.symbol}</td>
                            <td>
                              <span className={`trade-type ${trade.trade_type.toLowerCase()}`}>
                                {trade.trade_type}
                              </span>
                            </td>
                            <td>₹{trade.entry_price.toFixed(2)}</td>
                            <td>
                              {trade.exit_price ? `₹${trade.exit_price.toFixed(2)}` : "-"}
                            </td>
                            <td>
                              {trade.pnl ? (
                                <span className={trade.pnl >= 0 ? "profit" : "loss"}>
                                  ₹{trade.pnl.toFixed(2)} ({trade.pnl_percentage.toFixed(1)}%)
                                </span>
                              ) : "-"}
                            </td>
                            <td>
                              <span className={`status ${trade.status.toLowerCase()}`}>
                                {trade.status}
                              </span>
                            </td>
                            <td>
                              {trade.status === "OPEN" && (
                                <button 
                                  className="btn btn-small btn-danger"
                                  onClick={() => closeTrade(trade.id)}
                                >
                                  Close
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "backtest" && (
          <BacktestSection />
        )}
      </div>

      {showCreateForm && (
        <CreateStrategyForm 
          onClose={() => setShowCreateForm(false)}
          onSuccess={fetchStrategies}
        />
      )}
    </div>
  );
};

const BacktestSection = () => {
  const [backtestForm, setBacktestForm] = useState({
    strategy_name: "",
    symbols: "",
    start_date: "",
    end_date: "",
    timeframe: "1min",
    capital: 100000,
    risk_per_trade: 1.5
  });
  const [backtestResults, setBacktestResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${getApiBase()}/breakout-strategy/backtest`,
        {
          ...backtestForm,
          symbols: backtestForm.symbols.split(",").map(s => s.trim().toUpperCase())
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        }
      );
      alert("Backtest started! Results will be available shortly.");
    } catch (error) {
      console.error("Error running backtest:", error);
      alert(error.response?.data?.detail || "Failed to start backtest");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="backtest-section">
      <h2>Strategy Backtesting</h2>
      
      <div className="backtest-form">
        <div className="form-grid">
          <div className="form-group">
            <label>Strategy Name</label>
            <input
              type="text"
              value={backtestForm.strategy_name}
              onChange={(e) => setBacktestForm({...backtestForm, strategy_name: e.target.value})}
              placeholder="My Backtest Strategy"
            />
          </div>
          
          <div className="form-group">
            <label>Symbols (comma-separated)</label>
            <input
              type="text"
              value={backtestForm.symbols}
              onChange={(e) => setBacktestForm({...backtestForm, symbols: e.target.value})}
              placeholder="RELIANCE, TCS, INFY"
            />
          </div>
          
          <div className="form-group">
            <label>Start Date</label>
            <input
              type="date"
              value={backtestForm.start_date}
              onChange={(e) => setBacktestForm({...backtestForm, start_date: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>End Date</label>
            <input
              type="date"
              value={backtestForm.end_date}
              onChange={(e) => setBacktestForm({...backtestForm, end_date: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Timeframe</label>
            <select
              value={backtestForm.timeframe}
              onChange={(e) => setBacktestForm({...backtestForm, timeframe: e.target.value})}
            >
              <option value="1min">1 Minute</option>
              <option value="5min">5 Minutes</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Capital (₹)</label>
            <input
              type="number"
              value={backtestForm.capital}
              onChange={(e) => setBacktestForm({...backtestForm, capital: Number(e.target.value)})}
              min="10000"
              step="10000"
            />
          </div>
          
          <div className="form-group">
            <label>Risk per Trade (%)</label>
            <input
              type="number"
              value={backtestForm.risk_per_trade}
              onChange={(e) => setBacktestForm({...backtestForm, risk_per_trade: Number(e.target.value)})}
              min="0.5"
              max="5"
              step="0.5"
            />
          </div>
        </div>
        
        <button 
          className="btn btn-primary"
          onClick={runBacktest}
          disabled={loading}
        >
          {loading ? "Running..." : "Run Backtest"}
        </button>
      </div>
    </div>
  );
};

const CreateStrategyForm = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: "",
    symbols: "",
    capital: 100000,
    risk_per_trade: 1.5,
    timeframe: "1min",
    strong_candle_threshold: 0.6,
    volume_multiplier: 1.5,
    risk_reward_ratio: 2.0,
    max_daily_trades: 3,
    stop_after_losses: 2,
    enable_trend_filter: false,
    trend_ema_period: 50,
    enable_session_filter: false,
    session_start: "09:15",
    session_end: "10:30"
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(
        `${getApiBase()}/breakout-strategy/strategies`,
        {
          ...formData,
          symbols: formData.symbols.split(",").map(s => s.trim().toUpperCase())
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        }
      );
      onSuccess();
      onClose();
    } catch (error) {
      console.error("Error creating strategy:", error);
      alert(error.response?.data?.detail || "Failed to create strategy");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Create Breakout Strategy</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="strategy-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Strategy Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="My Breakout Strategy"
              />
            </div>
            
            <div className="form-group">
              <label>Symbols *</label>
              <input
                type="text"
                required
                value={formData.symbols}
                onChange={(e) => setFormData({...formData, symbols: e.target.value})}
                placeholder="RELIANCE, TCS, INFY"
              />
              <small>Enter symbols separated by commas</small>
            </div>
            
            <div className="form-group">
              <label>Capital (₹) *</label>
              <input
                type="number"
                required
                value={formData.capital}
                onChange={(e) => setFormData({...formData, capital: Number(e.target.value)})}
                min="10000"
                step="10000"
              />
            </div>
            
            <div className="form-group">
              <label>Risk per Trade (%) *</label>
              <input
                type="number"
                required
                value={formData.risk_per_trade}
                onChange={(e) => setFormData({...formData, risk_per_trade: Number(e.target.value)})}
                min="0.5"
                max="5"
                step="0.5"
              />
            </div>
            
            <div className="form-group">
              <label>Timeframe *</label>
              <select
                value={formData.timeframe}
                onChange={(e) => setFormData({...formData, timeframe: e.target.value})}
                required
              >
                <option value="1min">1 Minute</option>
                <option value="5min">5 Minutes</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Risk:Reward Ratio</label>
              <input
                type="number"
                value={formData.risk_reward_ratio}
                onChange={(e) => setFormData({...formData, risk_reward_ratio: Number(e.target.value)})}
                min="1"
                max="5"
                step="0.5"
              />
            </div>
            
            <div className="form-group">
              <label>Max Daily Trades</label>
              <input
                type="number"
                value={formData.max_daily_trades}
                onChange={(e) => setFormData({...formData, max_daily_trades: Number(e.target.value)})}
                min="1"
                max="10"
              />
            </div>
            
            <div className="form-group">
              <label>Stop After Losses</label>
              <input
                type="number"
                value={formData.stop_after_losses}
                onChange={(e) => setFormData({...formData, stop_after_losses: Number(e.target.value)})}
                min="1"
                max="5"
              />
            </div>
            
            <div className="form-group">
              <label>Strong Candle Threshold</label>
              <input
                type="number"
                value={formData.strong_candle_threshold}
                onChange={(e) => setFormData({...formData, strong_candle_threshold: Number(e.target.value)})}
                min="0.3"
                max="0.9"
                step="0.1"
              />
              <small>Body size as % of candle range (0.3-0.9)</small>
            </div>
            
            <div className="form-group">
              <label>Volume Multiplier</label>
              <input
                type="number"
                value={formData.volume_multiplier}
                onChange={(e) => setFormData({...formData, volume_multiplier: Number(e.target.value)})}
                min="1"
                max="5"
                step="0.5"
              />
              <small>Volume must be X times average</small>
            </div>
          </div>
          
          <div className="form-section">
            <h3>Advanced Filters</h3>
            
            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.enable_trend_filter}
                  onChange={(e) => setFormData({...formData, enable_trend_filter: e.target.checked})}
                />
                Enable Trend Filter (EMA)
              </label>
              {formData.enable_trend_filter && (
                <input
                  type="number"
                  value={formData.trend_ema_period}
                  onChange={(e) => setFormData({...formData, trend_ema_period: Number(e.target.value)})}
                  min="10"
                  max="200"
                  placeholder="EMA Period"
                />
              )}
            </div>
            
            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.enable_session_filter}
                  onChange={(e) => setFormData({...formData, enable_session_filter: e.target.checked})}
                />
                Enable Session Time Filter
              </label>
              {formData.enable_session_filter && (
                <div className="session-times">
                  <input
                    type="time"
                    value={formData.session_start}
                    onChange={(e) => setFormData({...formData, session_start: e.target.value})}
                  />
                  <span>to</span>
                  <input
                    type="time"
                    value={formData.session_end}
                    onChange={(e) => setFormData({...formData, session_end: e.target.value})}
                  />
                </div>
              )}
            </div>
          </div>
          
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Creating..." : "Create Strategy"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BreakoutStrategyPage;
