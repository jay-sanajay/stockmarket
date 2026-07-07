import React, { useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";

export default function ComparePage() {
  const [a, setA] = useState("TCS.NS");
  const [b, setB] = useState("INFY.NS");
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const base = getApiBase();

  function run() {
    setErr("");
    axios
      .get(`${base}/compare`, { params: { a, b } })
      .then((r) => setData(r.data))
      .catch((e) => setErr(e.message));
  }

  return (
    <div className="page-pad">
      <h1>Compare</h1>
      <div className="form-row">
        <input value={a} onChange={(e) => setA(e.target.value)} />
        <input value={b} onChange={(e) => setB(e.target.value)} />
        <button type="button" onClick={run}>
          Compare
        </button>
      </div>
      {err && <p className="error-inline">{err}</p>}
      {data?.error && <p className="error-inline">{data.error}</p>}
      {data?.ai_comparison && (
        <section className="card wide">
          <h3>AI comparison</h3>
          <p className="prose">{data.ai_comparison}</p>
        </section>
      )}
      <div className="grid-two">
        {data?.a && !data.a.error && (
          <div className="card">
            <h3>{data.a.symbol}</h3>
            <p>{data.a.strategy_type}</p>
            <p>Score {data.a.signal_score}</p>
          </div>
        )}
        {data?.b && !data.b.error && (
          <div className="card">
            <h3>{data.b.symbol}</h3>
            <p>{data.b.strategy_type}</p>
            <p>Score {data.b.signal_score}</p>
          </div>
        )}
      </div>
    </div>
  );
}
