import React, { useEffect, useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { Link } from "react-router-dom";

export default function PortfolioPage() {
  const { token, authHeaders } = useAuth();
  const [summary, setSummary] = useState(null);
  const [sym, setSym] = useState("TCS.NS");
  const [qty, setQty] = useState("1");
  const [avg, setAvg] = useState("1000");
  const base = getApiBase();

  function load() {
    if (!token) return;
    axios
      .get(`${base}/portfolio/summary`, { headers: authHeaders })
      .then((r) => setSummary(r.data))
      .catch(() => setSummary(null));
  }

  useEffect(() => {
    load();
  }, [token, authHeaders, base]);

  function add() {
    axios
      .post(
        `${base}/portfolio/holdings`,
        {
          symbol: sym.trim(),
          quantity: Number(qty),
          avg_buy_price: Number(avg),
        },
        { headers: authHeaders }
      )
      .then(load);
  }

  if (!token) {
    return (
      <div className="page-pad">
        <Link to="/login">Log in</Link> for portfolio.
      </div>
    );
  }

  return (
    <div className="page-pad">
      <h1>Portfolio</h1>
      {summary && (
        <div className="grid-cards">
          <div className="card">
            <h3>Invested</h3>
            <p className="lead">₹{summary.total_invested}</p>
          </div>
          <div className="card">
            <h3>Value</h3>
            <p className="lead">₹{summary.total_value}</p>
          </div>
          <div className="card">
            <h3>P/L</h3>
            <p className="lead">
              ₹{summary.total_pnl} ({summary.total_pnl_pct}%)
            </p>
          </div>
        </div>
      )}
      {summary?.ai_summary && (
        <section className="card wide">
          <h3>AI snapshot</h3>
          <p>{summary.ai_summary}</p>
        </section>
      )}
      <div className="form-row">
        <input value={sym} onChange={(e) => setSym(e.target.value)} />
        <input value={qty} onChange={(e) => setQty(e.target.value)} placeholder="qty" />
        <input value={avg} onChange={(e) => setAvg(e.target.value)} placeholder="avg ₹" />
        <button type="button" onClick={add}>
          Add holding
        </button>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Qty</th>
            <th>Avg</th>
            <th>Value</th>
            <th>P/L</th>
          </tr>
        </thead>
        <tbody>
          {(summary?.positions || []).map((p) => (
            <tr key={p.id}>
              <td>{p.symbol}</td>
              <td>{p.quantity}</td>
              <td>{p.avg_buy_price}</td>
              <td>{p.market_value}</td>
              <td>
                {p.pnl} ({p.pnl_pct}%)
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
