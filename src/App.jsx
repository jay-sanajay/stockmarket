import React, { useState } from "react";
import axios from "axios";
import StockDashboard from "./StockDashboard";
import "./App.css";

function App() {
  const [stock, setStock] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
    try {
      return await axios.get(url);
    } catch (err) {
      if (retries === 0) throw err;
      await new Promise((r) => setTimeout(r, delay));
      return fetchWithRetry(url, retries - 1, delay * 2);
    }
  };

  const handleAnalyze = async () => {
    if (!stock.trim()) return;
    setLoading(true);
    setError("");
    setData(null);
    try {
      const res = await fetchWithRetry(`https://stockmarket-rz6w.onrender.com/analyze?stock=${stock}`);
      if (res.data.error) {
        setError(res.data.error);
      } else {
        setData(res.data);
      }
    } catch (err) {
      setError("❌ Too many requests or backend unavailable. Please try again later.");
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <h1 className="app-title">JayQuant AI — Stock Advisor</h1>
      <p className="subtitle">SEBI-Style Reports | AI-Powered Insights</p>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Enter stock symbol (e.g., TCS.NS)"
          value={stock}
          onChange={(e) => setStock(e.target.value)}
          style={{ width: "300px", padding: "8px", marginRight: "10px" }}
        />
        <button onClick={handleAnalyze}>Analyze</button>
      </div>

      {loading && <p className="loading">⏳ Analyzing stock...</p>}
      {error && <p className="error">{error}</p>}
      {data && <StockDashboard data={data} />}
    </div>
  );
}

export default App;
