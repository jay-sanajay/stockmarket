import React, { useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import "../App.css";

export default function IntradayPicksPage() {
  const [picks, setPicks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const apiBase = getApiBase();

  const fetchPicks = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = apiBase
        ? `${apiBase}/prediction/intraday-picks`
        : "/prediction/intraday-picks";
      const res = await axios.get(url);
      setPicks(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch intraday picks. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (c) => {
    if (c >= 85) return "#10b981";
    if (c >= 75) return "#f59e0b";
    return "#ef4444";
  };

  const getSignalIcon = (signal) => {
    const s = (signal || "").toLowerCase();
    if (s.includes("breakout")) return "🔥";
    if (s.includes("momentum")) return "🚀";
    if (s.includes("bounce")) return "⚡";
    if (s.includes("gap")) return "📊";
    if (s.includes("volume")) return "📈";
    return "🎯";
  };

  return (
    <div className="app page-intraday-picks">
      <header className="app-header">
        <div className="app-header-inner">
          <p className="app-eyebrow">INTRADAY AI ENGINE</p>
          <h1 className="app-title">Today's Top Intraday Picks</h1>
          <p className="subtitle">
            AI-powered intraday stock picks with precise entry, targets & stop-loss — targeting 5-20% returns.
          </p>
        </div>
      </header>

      <section className="intraday-controls">
        <button
          className="btn-primary intraday-btn"
          onClick={fetchPicks}
          disabled={loading}
        >
          {loading ? (
            <><span className="spinner"></span> Scanning 40+ NSE Stocks Live…</>
          ) : (
            "⚡ Generate Intraday Picks"
          )}
        </button>
        {error && <div className="error-box">{error}</div>}
      </section>

      {picks.length > 0 && (
        <>
          {/* Summary Stats */}
          <section className="intraday-stats">
            <div className="istat">
              <span className="istat-val">{picks.length}</span>
              <span className="istat-lbl">Picks</span>
            </div>
            <div className="istat">
              <span className="istat-val" style={{color:"#10b981"}}>
                {picks.filter(p => (p.Confidence || 0) >= 80).length}
              </span>
              <span className="istat-lbl">High Confidence</span>
            </div>
            <div className="istat">
              <span className="istat-val" style={{color:"#f59e0b"}}>
                {picks.filter(p => p.Trade_Type === "LONG").length} L / {picks.filter(p => p.Trade_Type === "SHORT").length} S
              </span>
              <span className="istat-lbl">Long / Short</span>
            </div>
            <div className="istat">
              <span className="istat-val" style={{color:"#6366f1"}}>
                {picks.length > 0 ? (picks.reduce((s, p) => s + (p.Expected_Return_Pct || 0), 0) / picks.length).toFixed(1) : 0}%
              </span>
              <span className="istat-lbl">Avg Return</span>
            </div>
          </section>

          {/* Picks Grid */}
          <section className="intraday-grid">
            {picks.map((pick, idx) => (
              <div key={idx} className={`intraday-card ${pick.Trade_Type === "SHORT" ? "short-card" : ""}`}>
                {/* Header */}
                <div className="icard-header">
                  <div>
                    <div className="icard-rank">#{idx + 1}</div>
                    <h3 className="icard-ticker">{pick.Ticker}</h3>
                    <span className="icard-company">{pick.Company_Name}</span>
                  </div>
                  <div className="icard-badges">
                    <span className={`trade-badge ${pick.Trade_Type === "LONG" ? "long" : "short"}`}>
                      {pick.Trade_Type === "LONG" ? "📈 LONG" : "📉 SHORT"}
                    </span>
                    <span className="signal-badge">
                      {getSignalIcon(pick.Signal)} {pick.Signal}
                    </span>
                  </div>
                </div>

                {/* Confidence Bar */}
                <div className="confidence-section">
                  <div className="conf-label">
                    <span>Confidence</span>
                    <span style={{color: getConfidenceColor(pick.Confidence), fontWeight: 700}}>
                      {pick.Confidence}%
                    </span>
                  </div>
                  <div className="conf-bar">
                    <div
                      className="conf-fill"
                      style={{
                        width: `${pick.Confidence}%`,
                        background: getConfidenceColor(pick.Confidence)
                      }}
                    />
                  </div>
                </div>

                {/* Price Levels */}
                <div className="price-levels">
                  <div className="plevel">
                    <span className="plevel-lbl">Entry</span>
                    <span className="plevel-val">₹{Number(pick.Entry_Price).toFixed(2)}</span>
                  </div>
                  <div className="plevel target">
                    <span className="plevel-lbl">Target 1</span>
                    <span className="plevel-val">₹{Number(pick.Target_1).toFixed(2)}</span>
                  </div>
                  <div className="plevel target2">
                    <span className="plevel-lbl">Target 2</span>
                    <span className="plevel-val">₹{Number(pick.Target_2).toFixed(2)}</span>
                  </div>
                  <div className="plevel sl">
                    <span className="plevel-lbl">Stop Loss</span>
                    <span className="plevel-val">₹{Number(pick.Stop_Loss).toFixed(2)}</span>
                  </div>
                </div>

                {/* Expected Return */}
                <div className="return-row">
                  <span>Expected Return</span>
                  <span className="return-pct">+{Number(pick.Expected_Return_Pct).toFixed(1)}%</span>
                </div>

                {/* Reasoning */}
                <div className="reasoning">
                  <h4>Why This Trade</h4>
                  <ul>
                    {Array.isArray(pick.Reasoning) ? (
                      pick.Reasoning.map((r, i) => <li key={i}>{r}</li>)
                    ) : (
                      <li>{pick.Reasoning}</li>
                    )}
                  </ul>
                </div>

                <div className="risk-footer">
                  <span className={`risk-badge risk-${(pick.Risk_Profile || "medium").toLowerCase()}`}>
                    {pick.Risk_Profile} Risk
                  </span>
                </div>
              </div>
            ))}
          </section>
        </>
      )}

      <style>{`
        .page-intraday-picks { padding-bottom: 3rem; }
        .intraday-controls {
          display: flex; flex-direction: column; align-items: center;
          margin-bottom: 2rem; gap: 1rem;
        }
        .intraday-btn {
          background: linear-gradient(135deg, #f59e0b, #ef4444);
          color: white; border: none; padding: 1rem 2.5rem;
          font-size: 1.15rem; font-weight: 700; border-radius: 12px;
          cursor: pointer; transition: all 0.3s;
          box-shadow: 0 4px 20px rgba(245, 158, 11, 0.5);
          display: flex; align-items: center; gap: 0.75rem;
        }
        .intraday-btn:hover:not(:disabled) {
          transform: translateY(-3px);
          box-shadow: 0 8px 30px rgba(245, 158, 11, 0.7);
        }
        .intraday-btn:disabled { background: #4b5563; box-shadow: none; cursor: not-allowed; opacity: 0.7; }
        .spinner {
          display: inline-block; width: 18px; height: 18px;
          border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
          border-radius: 50%; animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .intraday-stats {
          display: flex; justify-content: center; gap: 2rem;
          padding: 1.25rem 2rem; margin: 0 1rem 2.5rem;
          background: rgba(31, 41, 55, 0.6); border-radius: 12px;
          border: 1px solid rgba(75, 85, 99, 0.3);
        }
        .istat { display: flex; flex-direction: column; align-items: center; }
        .istat-val { font-size: 1.5rem; font-weight: 700; color: #f59e0b; }
        .istat-lbl { font-size: 0.7rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }

        .intraday-grid {
          display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
          gap: 1.5rem; padding: 0 1rem;
        }

        .intraday-card {
          background: rgba(31, 41, 55, 0.7); backdrop-filter: blur(12px);
          border: 1px solid rgba(75, 85, 99, 0.4); border-radius: 16px;
          padding: 1.5rem; transition: all 0.3s;
          border-left: 4px solid #10b981;
        }
        .intraday-card.short-card { border-left-color: #ef4444; }
        .intraday-card:hover {
          transform: translateY(-4px); border-color: rgba(245, 158, 11, 0.5);
          box-shadow: 0 8px 30px rgba(245, 158, 11, 0.1);
        }

        .icard-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
        .icard-rank { font-size: 0.7rem; color: #6b7280; font-weight: 600; margin-bottom: 0.15rem; }
        .icard-ticker { margin: 0; font-size: 1.3rem; color: #f3f4f6; font-weight: 700; }
        .icard-company { font-size: 0.8rem; color: #9ca3af; }
        .icard-badges { display: flex; flex-direction: column; gap: 0.4rem; align-items: flex-end; }
        .trade-badge {
          padding: 0.2rem 0.7rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700;
        }
        .trade-badge.long { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .trade-badge.short { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        .signal-badge {
          padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.7rem;
          background: rgba(99, 102, 241, 0.15); color: #a5b4fc; font-weight: 500;
        }

        .confidence-section { margin-bottom: 1rem; }
        .conf-label { display: flex; justify-content: space-between; font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.3rem; }
        .conf-bar { height: 6px; background: rgba(55, 65, 81, 0.8); border-radius: 3px; overflow: hidden; }
        .conf-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }

        .price-levels {
          display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem;
          padding: 0.75rem; background: rgba(17, 24, 39, 0.5); border-radius: 10px;
          margin-bottom: 0.75rem;
        }
        .plevel { display: flex; flex-direction: column; }
        .plevel-lbl { font-size: 0.65rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
        .plevel-val { font-size: 0.95rem; font-weight: 600; color: #e5e7eb; }
        .plevel.target .plevel-val { color: #34d399; }
        .plevel.target2 .plevel-val { color: #6ee7b7; }
        .plevel.sl .plevel-val { color: #f87171; }

        .return-row {
          display: flex; justify-content: space-between; align-items: center;
          padding: 0.6rem 0.75rem; background: rgba(16, 185, 129, 0.08);
          border-radius: 8px; margin-bottom: 0.75rem; font-size: 0.85rem; color: #9ca3af;
        }
        .return-pct { font-size: 1.1rem; font-weight: 700; color: #34d399; }

        .reasoning h4 { font-size: 0.8rem; color: #d1d5db; margin: 0 0 0.5rem; }
        .reasoning ul { margin: 0; padding-left: 1.1rem; font-size: 0.8rem; color: #9ca3af; }
        .reasoning li { margin-bottom: 0.3rem; line-height: 1.35; }

        .risk-footer { margin-top: 0.75rem; }
        .risk-badge {
          padding: 0.2rem 0.6rem; border-radius: 9999px;
          font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        }
        .risk-low { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .risk-medium { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .risk-high { background: rgba(239, 68, 68, 0.2); color: #f87171; }

        @media (max-width: 768px) {
          .intraday-grid { grid-template-columns: 1fr; }
          .price-levels { grid-template-columns: repeat(2, 1fr); }
          .intraday-stats { gap: 1rem; flex-wrap: wrap; }
        }
      `}</style>
    </div>
  );
}
