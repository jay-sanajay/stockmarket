import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useWebSocket } from "../hooks/useWebSocket.js";
import "../Dashboard.css";

const IntradayScannerPage = () => {
  const { user } = useAuth();
  const [stocks, setStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [marketSummary, setMarketSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [filters, setFilters] = useState({
    minVolumeRatio: 1.5,
    minChangePercent: 1.0,
    showBreakouts: false,
    showHighVolume: true
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);

  // WebSocket for real-time updates
  const { isConnected } = useWebSocket();

  const fetchStocks = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${getApiBase()}/intraday/stocks`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setStocks(response.data);
      setLastUpdate(new Date());
      applyFilters(response.data, filters);
    } catch (error) {
      console.error("Error fetching stocks:", error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchMarketSummary = useCallback(async () => {
    try {
      const response = await axios.get(`${getApiBase()}/intraday/market-summary`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setMarketSummary(response.data);
    } catch (error) {
      console.error("Error fetching market summary:", error);
    }
  }, []);

  const applyFilters = (stockList, currentFilters) => {
    if (!Array.isArray(stockList)) {
      setFilteredStocks([]);
      return;
    }
    let filtered = stockList;

    if (currentFilters.showHighVolume) {
      filtered = filtered.filter(stock => stock.is_high_volume);
    }

    if (currentFilters.showBreakouts) {
      filtered = filtered.filter(stock => stock.is_breakout_above_pdh || stock.is_breakdown_below_pdl);
    }

    if (currentFilters.minChangePercent > 0) {
      filtered = filtered.filter(stock => Math.abs(stock.change_percent) >= currentFilters.minChangePercent);
    }

    if (currentFilters.minVolumeRatio > 1) {
      filtered = filtered.filter(stock => stock.volume_ratio >= currentFilters.minVolumeRatio);
    }

    if (searchTerm) {
      filtered = filtered.filter(stock => 
        stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredStocks(filtered);
  };

  const fetchFilteredStocks = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.minVolumeRatio > 1.5) params.append('min_volume_ratio', filters.minVolumeRatio);
      if (filters.minChangePercent > 1.0) params.append('min_change_percent', filters.minChangePercent);
      params.append('show_breakouts', filters.showBreakouts);
      params.append('show_high_volume', filters.showHighVolume);

      const response = await axios.get(`${getApiBase()}/intraday/stocks/filtered?${params}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setFilteredStocks(Array.isArray(response.data) ? response.data : []);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching filtered stocks:", error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchTabData = useCallback(async () => {
    try {
      setLoading(true);
      let endpoint = `${getApiBase()}/intraday/stocks`;
      
      switch (activeTab) {
        case "breakouts":
          endpoint = `${getApiBase()}/intraday/stocks/breakouts`;
          break;
        case "high-volume":
          endpoint = `${getApiBase()}/intraday/stocks/high-volume`;
          break;
        case "gainers":
          endpoint = `${getApiBase()}/intraday/stocks/gainers`;
          break;
        case "losers":
          endpoint = `${getApiBase()}/intraday/stocks/losers`;
          break;
        default:
          endpoint = `${getApiBase()}/intraday/stocks`;
      }

      const response = await axios.get(endpoint, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setFilteredStocks(Array.isArray(response.data) ? response.data : []);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching tab data:", error);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchStocks();
    fetchMarketSummary();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchStocks();
      fetchMarketSummary();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchStocks, fetchMarketSummary]);

  useEffect(() => {
    if (activeTab === "all") {
      applyFilters(stocks, filters);
    } else {
      fetchTabData();
    }
  }, [activeTab, stocks, filters, searchTerm, fetchTabData]);

  const formatNumber = (num) => {
    if (num >= 10000000) return (num / 10000000).toFixed(1) + 'Cr';
    if (num >= 100000) return (num / 100000).toFixed(1) + 'L';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatPrice = (price) => {
    return `₹${price.toFixed(2)}`;
  };

  const getChangeColor = (change) => {
    if (change > 0) return '#10b981';
    if (change < 0) return '#ef4444';
    return '#6b7280';
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Live Intraday Scanner</h1>
        <div className="header-info">
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Live' : '🔴 Offline'}
          </span>
          {lastUpdate && (
            <span className="last-update">
              Last Update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Market Summary */}
      {marketSummary && (
        <div className="market-summary">
          <div className="summary-card">
            <h3>Market Overview</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="label">Total Stocks</span>
                <span className="value">{marketSummary.total_stocks}</span>
              </div>
              <div className="summary-item">
                <span className="label">Gainers</span>
                <span className="value gainers">{marketSummary.gainers}</span>
              </div>
              <div className="summary-item">
                <span className="label">Losers</span>
                <span className="value losers">{marketSummary.losers}</span>
              </div>
              <div className="summary-item">
                <span className="label">Avg Change</span>
                <span className="value" style={{ color: getChangeColor(marketSummary.avg_change_percent) }}>
                  {marketSummary.avg_change_percent > 0 ? '+' : ''}{marketSummary.avg_change_percent}%
                </span>
              </div>
              <div className="summary-item">
                <span className="label">Breakouts</span>
                <span className="value breakouts">{marketSummary.breakouts}</span>
              </div>
              <div className="summary-item">
                <span className="label">High Volume</span>
                <span className="value high-volume">{marketSummary.high_volume_stocks}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={`tab-btn ${activeTab === "all" ? "active" : ""}`}
          onClick={() => setActiveTab("all")}
        >
          All Stocks
        </button>
        <button 
          className={`tab-btn ${activeTab === "breakouts" ? "active" : ""}`}
          onClick={() => setActiveTab("breakouts")}
        >
          Breakouts
        </button>
        <button 
          className={`tab-btn ${activeTab === "high-volume" ? "active" : ""}`}
          onClick={() => setActiveTab("high-volume")}
        >
          High Volume
        </button>
        <button 
          className={`tab-btn ${activeTab === "gainers" ? "active" : ""}`}
          onClick={() => setActiveTab("gainers")}
        >
          Top Gainers
        </button>
        <button 
          className={`tab-btn ${activeTab === "losers" ? "active" : ""}`}
          onClick={() => setActiveTab("losers")}
        >
          Top Losers
        </button>
      </div>

      {/* Filters */}
      {activeTab === "all" && (
        <div className="filters-section">
          <div className="filter-controls">
            <div className="filter-group">
              <label>Search:</label>
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="filter-group">
              <label>Min Volume Ratio:</label>
              <input
                type="number"
                min="1"
                max="10"
                step="0.5"
                value={filters.minVolumeRatio}
                onChange={(e) => setFilters({...filters, minVolumeRatio: parseFloat(e.target.value)})}
              />
            </div>
            <div className="filter-group">
              <label>Min Change %:</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.5"
                value={filters.minChangePercent}
                onChange={(e) => setFilters({...filters, minChangePercent: parseFloat(e.target.value)})}
              />
            </div>
            <div className="filter-group checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={filters.showBreakouts}
                  onChange={(e) => setFilters({...filters, showBreakouts: e.target.checked})}
                />
                Show Breakouts Only
              </label>
            </div>
            <div className="filter-group checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={filters.showHighVolume}
                  onChange={(e) => setFilters({...filters, showHighVolume: e.target.checked})}
                />
                High Volume Only
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Stocks Table */}
      <div className="dashboard-content">
        {loading ? (
          <div className="loading">Loading stocks...</div>
        ) : (
          <div className="stocks-table">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Company</th>
                  <th>Price</th>
                  <th>Change</th>
                  <th>Change %</th>
                  <th>Volume</th>
                  <th>Volume Ratio</th>
                  <th>PDH</th>
                  <th>PDL</th>
                  <th>RSI</th>
                  <th>Signals</th>
                </tr>
              </thead>
              <tbody>
                {filteredStocks.map((stock) => (
                  <tr key={stock.symbol}>
                    <td className="symbol-cell">
                      <strong>{stock.symbol}</strong>
                    </td>
                    <td className="name-cell">{stock.name}</td>
                    <td className="price-cell">{formatPrice(stock.current_price)}</td>
                    <td className="change-cell" style={{ color: getChangeColor(stock.change) }}>
                      {stock.change > 0 ? '+' : ''}{formatPrice(stock.change)}
                    </td>
                    <td className="change-percent-cell" style={{ color: getChangeColor(stock.change_percent) }}>
                      {stock.change_percent > 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%
                    </td>
                    <td className="volume-cell">{formatNumber(stock.volume)}</td>
                    <td className="volume-ratio-cell">
                      <span className={`volume-badge ${stock.is_high_volume ? 'high' : 'normal'}`}>
                        {stock.volume_ratio.toFixed(1)}x
                      </span>
                    </td>
                    <td className="pdh-cell">{formatPrice(stock.pdh)}</td>
                    <td className="pdl-cell">{formatPrice(stock.pdl)}</td>
                    <td className="rsi-cell">
                      {stock.rsi ? (
                        <span className={`rsi-value ${
                          stock.rsi > 70 ? 'overbought' : 
                          stock.rsi < 30 ? 'oversold' : 'neutral'
                        }`}>
                          {stock.rsi.toFixed(1)}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="signals-cell">
                      <div className="signal-badges">
                        {stock.is_breakout_above_pdh && (
                          <span className="signal-badge breakout-up">🔺 PDH</span>
                        )}
                        {stock.is_breakdown_below_pdl && (
                          <span className="signal-badge breakout-down">🔻 PDL</span>
                        )}
                        {stock.is_high_volume && (
                          <span className="signal-badge volume">📊 Vol</span>
                        )}
                        {stock.is_strong_momentum && (
                          <span className="signal-badge momentum">🚀 Mom</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredStocks.length === 0 && (
              <div className="empty-state">
                <h3>No stocks found</h3>
                <p>Try adjusting your filters or search criteria.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntradayScannerPage;
