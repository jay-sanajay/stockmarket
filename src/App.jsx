import React, { useState } from "react";
import axios from "axios";
import StockDashboard from "./StockDashboard";
import LoadingSkeleton from "./LoadingSkeleton";
import "./App.css";

const QUICK_TICKERS = [
  "TCS.NS",
  "RELIANCE.NS",
  "INFY.NS",
  "HDFCBANK.NS",
  "SBIN.NS",
  "ITC.NS",
];

function App() {
  const [stock, setStock] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const apiBase =
    import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
    (import.meta.env.DEV
      ? "http://127.0.0.1:8000"
      : "https://stockmarket-rz6w.onrender.com");

  const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
    try {
      return await axios.get(url);
    } catch (err) {
      if (retries === 0) throw err;
      await new Promise((r) => setTimeout(r, delay));
      return fetchWithRetry(url, retries - 1, delay * 2);
    }
  };

  async function runAnalyze(symbol) {
    const s = symbol.trim();
    if (!s) return;
    setLoading(true);
    setError("");
    setData(null);
    try {
      const res = await fetchWithRetry(
        `${apiBase}/analyze?stock=${encodeURIComponent(s)}`
      );
      if (res.data?.error) {
        setError(res.data.error);
      } else {
        setData(res.data);
      }
    } catch (err) {
      const body = err.response?.data;
      let detail = body?.detail ?? body?.error ?? err.message;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => x?.msg || JSON.stringify(x)).join("; ");
      }
      setError(
        typeof detail === "string" && detail
          ? `❌ ${detail}`
          : "❌ Too many requests or backend unavailable. Please try again later."
      );
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
          <p className="hint">Press Enter to run · API {apiBase}</p>
        )}
      </section>

      {loading && <LoadingSkeleton />}
      {!loading && error && <p className="error">{error}</p>}
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

export default App;
