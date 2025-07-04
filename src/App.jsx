import React, { useState } from "react";
import axios from "axios";
import StockDashboard from "./StockDashboard";
import "./App.css";

function App() {
  const [stock, setStock] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!stock.trim()) return;
    setLoading(true);
    setError("");
    setData(null);
    try {
      const API_BASE = import.meta.env.VITE_BACKEND_URL;

      const res = await axios.get(`${API_BASE}/analyze?stock=${stock}`);

      //const res = await axios.get(`http://localhost:8000/analyze?stock=${stock}`);
      if (res.data.error) {
        setError(res.data.error);
      } else {
        setData(res.data);
      }
    } catch (err) {
      setError("❌ Failed to fetch data. Please check your internet or backend.");
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <h1 className="app-title"> JayQuant AI — Stock Advisor</h1>
<p className="subtitle">SEBI-Style Reports | AI-Powered Insights</p>



      <div className="search-bar">
        <input
          type="text"
          placeholder="Enter stock symbol (e.g., IRFC.NS)"
          value={stock}
          onChange={(e) => setStock(e.target.value)}
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
