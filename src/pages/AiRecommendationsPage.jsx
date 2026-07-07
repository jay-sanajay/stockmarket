import React, { useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import "../App.css";

const HORIZON_ORDER = [
  "1 Month",
  "2 Months",
  "3 Months",
  "4 Months",
  "5 Months",
  "6 Months",
  "12 Months",
  "50% Return Picks",
  "Deep Value (Near All-Time Low)",
];

const HORIZON_ICONS = {
  "1 Month": "⚡",
  "2 Months": "🔥",
  "3 Months": "📊",
  "4 Months": "📈",
  "5 Months": "🚀",
  "6 Months": "💎",
  "12 Months": "🏆",
  "50% Return Picks": "🎯",
  "Deep Value (Near All-Time Low)": "💰",
};

const HORIZON_COLORS = {
  "1 Month": "#f59e0b",
  "2 Months": "#f97316",
  "3 Months": "#6366f1",
  "4 Months": "#8b5cf6",
  "5 Months": "#06b6d4",
  "6 Months": "#10b981",
  "12 Months": "#3b82f6",
  "50% Return Picks": "#ef4444",
  "Deep Value (Near All-Time Low)": "#14b8a6",
};

export default function AiRecommendationsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const { token } = useAuth();
  const apiBase = getApiBase();

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = apiBase
        ? `${apiBase}/prediction/ai-recommendations`
        : "/prediction/ai-recommendations";
      const headers = {};
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await axios.get(url, { headers });
      setRecommendations(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error(err);
      setError(
        "Failed to fetch recommendations. The AI might be busy — please try again in a moment."
      );
    } finally {
      setLoading(false);
    }
  };

  const grouped = Array.isArray(recommendations)
    ? recommendations.reduce((acc, rec) => {
        const h = rec.Time_Horizon || "Other";
        if (!acc[h]) acc[h] = [];
        acc[h].push(rec);
        return acc;
      }, {})
    : {};

  const filteredHorizons =
    activeFilter === "all"
      ? HORIZON_ORDER
      : activeFilter === "short"
      ? ["1 Month", "2 Months", "3 Months"]
      : activeFilter === "medium"
      ? ["4 Months", "5 Months", "6 Months"]
      : activeFilter === "long"
      ? ["12 Months"]
      : activeFilter === "multi"
      ? ["50% Return Picks"]
      : activeFilter === "value"
      ? ["Deep Value (Near All-Time Low)"]
      : HORIZON_ORDER;

  const renderCard = (rec, index) => {
    const returnPct = rec.Expected_Return_Pct
      ? rec.Expected_Return_Pct
      : rec.Current_Price && rec.Target_Price
      ? (((rec.Target_Price - rec.Current_Price) / rec.Current_Price) * 100).toFixed(1)
      : null;

    return (
      <div key={index} className="recommendation-card">
        <div className="card-header">
          <div className="card-title">
            <h3>{rec.Ticker}</h3>
            <span className="company-name">{rec.Company_Name}</span>
          </div>
          <div className="card-badges">
            <span
              className={`risk-badge risk-${(rec.Risk_Profile || "medium").toLowerCase()}`}
            >
              {rec.Risk_Profile} Risk
            </span>
            {returnPct && (
              <span className="return-badge">+{Number(returnPct).toFixed(1)}%</span>
            )}
          </div>
        </div>

        <div className="price-grid">
          <div className="price-item">
            <span className="label">Current</span>
            <span className="value">₹{Number(rec.Current_Price).toFixed(2)}</span>
          </div>
          <div className="price-item target">
            <span className="label">Target</span>
            <span className="value">₹{Number(rec.Target_Price).toFixed(2)}</span>
          </div>
          <div className="price-item stop-loss">
            <span className="label">Stop Loss</span>
            <span className="value">₹{Number(rec.Stop_Loss).toFixed(2)}</span>
          </div>
        </div>

        <div className="catalysts">
          <h4>Core Catalysts</h4>
          <ul>
            {Array.isArray(rec.Core_Catalysts) ? (
              rec.Core_Catalysts.map((cat, i) => <li key={i}>{cat}</li>)
            ) : (
              <li>{rec.Core_Catalysts}</li>
            )}
          </ul>
        </div>
      </div>
    );
  };

  return (
    <div className="app page-recommendations">
      <header className="app-header">
        <div className="app-header-inner">
          <p className="app-eyebrow">AI ANALYST</p>
          <h1 className="app-title">High-Potential Recommendations</h1>
          <p className="subtitle">
            Data-driven setups targeting 20–50%+ upside across 7 time horizons,
            multi-baggers & deep-value picks.
          </p>
        </div>
      </header>

      <section className="recommendations-controls">
        <button
          className="btn-primary generate-btn"
          onClick={fetchRecommendations}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span> Analyzing 30+ NSE Stocks…
            </>
          ) : (
            "🚀 Generate AI Recommendations"
          )}
        </button>
        {error && <div className="error-box">{error}</div>}
      </section>

      {/* Filter Tabs */}
      {recommendations.length > 0 && (
        <section className="filter-tabs">
          {[
            { key: "all", label: "All Picks" },
            { key: "short", label: "Short-Term (1-3M)" },
            { key: "medium", label: "Medium-Term (4-6M)" },
            { key: "long", label: "Long-Term (12M)" },
            { key: "multi", label: "50%+ Multi-Baggers" },
            { key: "value", label: "Deep Value" },
          ].map((tab) => (
            <button
              key={tab.key}
              className={`filter-tab ${activeFilter === tab.key ? "active" : ""}`}
              onClick={() => setActiveFilter(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </section>
      )}

      {/* Stats Bar */}
      {recommendations.length > 0 && (
        <section className="stats-bar">
          <div className="stat-item">
            <span className="stat-value">{recommendations.length}</span>
            <span className="stat-label">Total Picks</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">
              {Object.keys(grouped).length}
            </span>
            <span className="stat-label">Categories</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">
              {(grouped["50% Return Picks"] || []).length}
            </span>
            <span className="stat-label">Multi-Baggers</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">
              {(grouped["Deep Value (Near All-Time Low)"] || []).length}
            </span>
            <span className="stat-label">Deep Value</span>
          </div>
        </section>
      )}

      {/* Results */}
      {recommendations.length > 0 && (
        <section className="recommendations-results">
          {filteredHorizons.map((horizon) => {
            if (!grouped[horizon] || grouped[horizon].length === 0) return null;
            const color = HORIZON_COLORS[horizon] || "#6366f1";
            const icon = HORIZON_ICONS[horizon] || "📌";
            return (
              <div key={horizon} className="horizon-group">
                <h2 className="horizon-title" style={{ borderColor: color }}>
                  <span className="horizon-icon">{icon}</span>
                  {horizon}
                  <span className="horizon-count" style={{ background: color }}>
                    {grouped[horizon].length} picks
                  </span>
                </h2>
                <div className="cards-container">
                  {grouped[horizon].map((rec, idx) => renderCard(rec, idx))}
                </div>
              </div>
            );
          })}
        </section>
      )}

      <style>{`
        .page-recommendations { padding-bottom: 3rem; }
        .recommendations-controls {
          display: flex; flex-direction: column; align-items: center;
          margin-bottom: 2rem; gap: 1rem;
        }
        .generate-btn {
          background: linear-gradient(135deg, #6366f1, #a855f7);
          color: white; border: none; padding: 1rem 2.5rem;
          font-size: 1.15rem; font-weight: 700; border-radius: 12px;
          cursor: pointer; transition: all 0.3s;
          box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5);
          display: flex; align-items: center; gap: 0.75rem;
        }
        .generate-btn:hover:not(:disabled) {
          transform: translateY(-3px);
          box-shadow: 0 8px 30px rgba(99, 102, 241, 0.7);
        }
        .generate-btn:disabled { background: #4b5563; box-shadow: none; cursor: not-allowed; opacity: 0.7; }
        .spinner {
          display: inline-block; width: 18px; height: 18px;
          border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
          border-radius: 50%; animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .filter-tabs {
          display: flex; gap: 0.5rem; padding: 0 1rem;
          margin-bottom: 2rem; flex-wrap: wrap; justify-content: center;
        }
        .filter-tab {
          padding: 0.5rem 1.25rem; border-radius: 9999px;
          background: rgba(55, 65, 81, 0.6); color: #9ca3af;
          border: 1px solid rgba(75, 85, 99, 0.4);
          cursor: pointer; font-size: 0.875rem; font-weight: 500;
          transition: all 0.2s;
        }
        .filter-tab:hover { background: rgba(99, 102, 241, 0.2); color: #e5e7eb; }
        .filter-tab.active {
          background: linear-gradient(135deg, #6366f1, #a855f7);
          color: white; border-color: transparent;
        }

        .stats-bar {
          display: flex; justify-content: center; gap: 2rem;
          padding: 1.25rem 2rem; margin: 0 1rem 2.5rem;
          background: rgba(31, 41, 55, 0.6); border-radius: 12px;
          border: 1px solid rgba(75, 85, 99, 0.3);
        }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #a855f7; }
        .stat-label { font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }

        .horizon-group { margin-bottom: 3rem; padding: 0 1rem; }
        .horizon-title {
          font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem;
          color: #e5e7eb; border-bottom: 2px solid;
          padding-bottom: 0.75rem; display: flex; align-items: center; gap: 0.75rem;
        }
        .horizon-icon { font-size: 1.5rem; }
        .horizon-count {
          font-size: 0.75rem; padding: 0.2rem 0.75rem;
          border-radius: 9999px; color: white; font-weight: 600; margin-left: auto;
        }
        .cards-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
          gap: 1.5rem;
        }
        .recommendation-card {
          background: rgba(31, 41, 55, 0.6); backdrop-filter: blur(10px);
          border: 1px solid rgba(75, 85, 99, 0.4); border-radius: 16px;
          padding: 1.5rem; transition: all 0.3s;
        }
        .recommendation-card:hover {
          transform: translateY(-5px); border-color: #6366f1;
          box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
        }
        .card-header {
          display: flex; justify-content: space-between;
          align-items: flex-start; margin-bottom: 1.5rem;
        }
        .card-title h3 { margin: 0; font-size: 1.25rem; color: #f3f4f6; }
        .company-name { font-size: 0.875rem; color: #9ca3af; }
        .card-badges { display: flex; flex-direction: column; gap: 0.4rem; align-items: flex-end; }
        .risk-badge {
          padding: 0.25rem 0.75rem; border-radius: 9999px;
          font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        }
        .risk-low { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .risk-medium { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .risk-high { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        .return-badge {
          padding: 0.25rem 0.75rem; border-radius: 9999px;
          font-size: 0.75rem; font-weight: 700;
          background: rgba(16, 185, 129, 0.2); color: #34d399;
        }
        .price-grid {
          display: grid; grid-template-columns: repeat(3, 1fr);
          gap: 1rem; margin-bottom: 1.5rem; padding: 1rem;
          background: rgba(17, 24, 39, 0.5); border-radius: 10px;
        }
        .price-item { display: flex; flex-direction: column; }
        .price-item .label { font-size: 0.7rem; color: #9ca3af; margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .price-item .value { font-size: 1.1rem; font-weight: 600; color: #f3f4f6; }
        .price-item.target .value { color: #34d399; }
        .price-item.stop-loss .value { color: #f87171; }
        .catalysts h4 { font-size: 0.85rem; color: #d1d5db; margin-top: 0; margin-bottom: 0.75rem; }
        .catalysts ul { margin: 0; padding-left: 1.25rem; font-size: 0.85rem; color: #9ca3af; }
        .catalysts li { margin-bottom: 0.4rem; line-height: 1.4; }

        @media (max-width: 768px) {
          .cards-container { grid-template-columns: 1fr; }
          .stats-bar { gap: 1rem; flex-wrap: wrap; }
          .filter-tabs { gap: 0.35rem; }
          .filter-tab { padding: 0.4rem 0.75rem; font-size: 0.8rem; }
        }
      `}</style>
    </div>
  );
}
