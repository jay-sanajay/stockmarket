import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { getApiBase } from "../api.js";
import AssistantPanel from "../components/AssistantPanel.jsx";

export default function HomePage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const base = getApiBase();
    axios
      .get(`${base}/dashboard/daily-summary`)
      .then((r) => setData(r.data))
      .catch((e) => setErr(e.message || "Failed to load dashboard"));
  }, []);

  if (err) {
    return <div className="panel error-box">{err}</div>;
  }
  if (!data) {
    return <div className="panel muted">Loading today&apos;s market snapshot…</div>;
  }

  return (
    <div className="home-dashboard page-pad">
      <header className="page-head">
        <h1>Today&apos;s market</h1>
        <p className="muted">Morning brief · {data.day_key}</p>
      </header>

      <section className="grid-cards">
        <div className="card">
          <h3>Market mood</h3>
          <p className="lead">{data.market_mood}</p>
        </div>
        <div className="card">
          <h3>Top opportunity (sample)</h3>
          <p>{data.top_opportunity}</p>
        </div>
        <div className="card">
          <h3>Top risk (sample)</h3>
          <p>{data.top_risk}</p>
        </div>
      </section>

      <section className="card wide">
        <h3>FII / DII</h3>
        <p className="mono small">{data.fii_dii}</p>
      </section>

      <section className="grid-two">
        <div className="card">
          <h3>Sample gainers (liquid names)</h3>
          <ul className="plain-list">
            {(data.top_gainers || []).map((g) => (
              <li key={g.symbol}>
                {g.symbol} · {g.pct_change}%
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>Sample losers</h3>
          <ul className="plain-list">
            {(data.top_losers || []).map((g) => (
              <li key={g.symbol}>
                {g.symbol} · {g.pct_change}%
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="card wide">
        <h3>AI summary</h3>
        <p className="prose">{data.ai_summary}</p>
      </section>

      <section className="card wide">
        <h3>Headlines</h3>
        <ul className="plain-list">
          {(data.headlines || []).map((h, i) => (
            <li key={i}>{h}</li>
          ))}
        </ul>
      </section>

      <AssistantPanel />
    </div>
  );
}
