import React, { useState } from "react";
import axios from "axios";
import StockDashboard from "./StockDashboard";
import LoadingSkeleton from "./LoadingSkeleton";
import { getApiBase } from "./api.js";
import "./App.css";

const QUICK_TICKERS = [
  "TCS.NS",
  "RELIANCE.NS",
  "INFY.NS",
  "HDFCBANK.NS",
  "SBIN.NS",
  "ITC.NS",
];

function formatNetworkHelpLocal() {
  return (
    <>
      Cannot reach the API. Start the backend in a <strong>second</strong> terminal:
      <br />
      <code className="inline-code">
        python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
      </code>
      <br />
      Or run both: <code className="inline-code">npm run dev:all</code>
    </>
  );
}

function formatNetworkHelpProduction() {
  return (
    <>
      Cannot reach the API from this site. On <strong>Vercel</strong>, open{" "}
      <strong>Settings → Environment Variables</strong> and set{" "}
      <code className="inline-code">VITE_API_BASE_URL</code> to your{" "}
      <strong>public Render URL</strong> (e.g. <code className="inline-code">https://xxx.onrender.com</code>
      ) — <strong>not</strong> <code className="inline-code">127.0.0.1</code>. Redeploy after saving.
      <br />
      <br />
      Also confirm your <strong>Render</strong> service is running and <code className="inline-code">
        CORS_ORIGINS
      </code>{" "}
      includes <code className="inline-code">https://stockmarket-rho.vercel.app</code>.
    </>
  );
}

export default function App() {
  const [stock, setStock] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiBase = getApiBase();

  const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
    try {
      return await axios.get(url);
    } catch (err) {
      // Do not retry rate limits — avoids hammering Yahoo / Gemini / News APIs
      if (err.response?.status === 429) throw err;
      if (retries === 0) throw err;
      await new Promise((r) => setTimeout(r, delay));
      return fetchWithRetry(url, retries - 1, delay * 2);
    }
  };

  async function runAnalyze(symbol) {
    const s = symbol.trim();
    if (!s) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const path = `/analyze?stock=${encodeURIComponent(s)}`;
      const url = apiBase ? `${apiBase}${path}` : path;
      const res = await fetchWithRetry(url);
      if (res.data?.error) {
        setError(res.data.error);
      } else {
        setData(res.data);
      }
    } catch (err) {
      const noResponse = err.response == null;
      const msg = String(err.message || "");
      const networkFail =
        noResponse &&
        (msg === "Network Error" ||
          err.code === "ERR_NETWORK" ||
          msg.includes("Network"));

      if (networkFail) {
        setError({
          type: "network",
          jsx: import.meta.env.DEV
            ? formatNetworkHelpLocal()
            : formatNetworkHelpProduction(),
        });
      } else {
        const body = err.response?.data;
        let detail = body?.detail ?? body?.error ?? err.message;
        if (Array.isArray(detail)) {
          detail = detail.map((x) => x?.msg || JSON.stringify(x)).join("; ");
        }
        setError(
          typeof detail === "string" && detail
            ? `❌ ${detail}`
            : "❌ Request failed. Check that the API is running on port 8000."
        );
      }
    }
    setLoading(false);
  }

  const handleAnalyze = () => runAnalyze(stock);

  const onKeyDown = (e) => {
    if (e.key === "Enter") handleAnalyze();
  };

  return (
    <div className="app app-advanced">
      <header className="app-header">
        <div className="app-header-inner">
          <p className="app-eyebrow">Quant · India equities</p>
          <h1 className="app-title">JayQuant AI</h1>
          <p className="subtitle">
            Fundamentals, technicals, news & Gemini narrative — one screen.
          </p>
        </div>
      </header>

      <section className="search-section">
        <div className="search-bar">
          <label htmlFor="stock-input" className="sr-only">
            Stock symbol
          </label>
          <input
            id="stock-input"
            type="text"
            placeholder="Symbol e.g. TCS.NS, RELIANCE.NS"
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="off"
            spellCheck={false}
            className="search-input"
          />
          <button type="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? "Working…" : "Analyze"}
          </button>
        </div>
        <div className="quick-row">
          <span className="quick-label">Quick:</span>
          <div className="quick-tickers">
            {QUICK_TICKERS.map((t) => (
              <button
                key={t}
                type="button"
                className="ticker-chip"
                onClick={() => {
                  setStock(t);
                  runAnalyze(t);
                }}
                disabled={loading}
              >
                {t.replace(".NS", "")}
              </button>
            ))}
          </div>
        </div>
        {import.meta.env.DEV && (
          <p className="hint">
            {apiBase
              ? `Direct API: ${apiBase}`
              : "Dev: Vite proxies /analyze → http://127.0.0.1:8000 (start uvicorn first)"}
          </p>
        )}
      </section>

      {loading && <LoadingSkeleton />}
      {!loading && error != null && (
        <div className="error error-box">
          {typeof error === "object" && error.jsx ? (
            error.jsx
          ) : (
            <span>{error}</span>
          )}
        </div>
      )}
      {!loading && data && <StockDashboard data={data} />}

      <footer className="app-footer">
        <p>
          Markets move fast — this tool is for research, not a substitute for professional
          advice.
        </p>
      </footer>
    </div>
  );
}
