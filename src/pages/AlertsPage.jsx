import React, { useEffect, useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { Link } from "react-router-dom";

export default function AlertsPage() {
  const { token, authHeaders } = useAuth();
  const [rows, setRows] = useState([]);
  const [sym, setSym] = useState("TCS.NS");
  const [atype, setAtype] = useState("rsi_below");
  const [thresh, setThresh] = useState("30");
  const base = getApiBase();

  function load() {
    if (!token) return;
    axios
      .get(`${base}/alerts`, { headers: authHeaders })
      .then((r) => setRows(r.data))
      .catch(() => setRows([]));
  }

  useEffect(() => {
    load();
  }, [token, authHeaders, base]);

  function create() {
    const threshold =
      atype.startsWith("rsi") || atype.startsWith("price")
        ? atype.includes("rsi")
          ? { rsi: Number(thresh) }
          : { price: Number(thresh) }
        : {};
    axios
      .post(
        `${base}/alerts`,
        { symbol: sym.trim(), alert_type: atype, threshold, active: true },
        { headers: authHeaders }
      )
      .then(load);
  }

  function checkNow() {
    axios.post(`${base}/alerts/check-now`, {}, { headers: authHeaders }).then((r) => {
      alert(`Triggered: ${r.data.count}`);
      load();
    });
  }

  if (!token) {
    return (
      <div className="page-pad">
        <Link to="/login">Log in</Link> for alerts.
      </div>
    );
  }

  return (
    <div className="page-pad">
      <h1>Alerts</h1>
      <p className="muted">Evaluated when you press &quot;Check now&quot; (no cron on free tier).</p>
      <div className="form-row">
        <input value={sym} onChange={(e) => setSym(e.target.value)} />
        <select value={atype} onChange={(e) => setAtype(e.target.value)}>
          <option value="price_above">Price above</option>
          <option value="price_below">Price below</option>
          <option value="rsi_above">RSI above</option>
          <option value="rsi_below">RSI below</option>
          <option value="verdict_changed">Verdict changed</option>
          <option value="sentiment_changed">Sentiment changed</option>
        </select>
        <input value={thresh} onChange={(e) => setThresh(e.target.value)} placeholder="threshold" />
        <button type="button" onClick={create}>
          Add
        </button>
        <button type="button" className="secondary" onClick={checkNow}>
          Check now
        </button>
      </div>
      <ul className="plain-list">
        {rows.map((r) => (
          <li key={r.id}>
            {r.symbol} · {r.alert_type} · active={String(r.active)}
          </li>
        ))}
      </ul>
    </div>
  );
}
