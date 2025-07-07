// LiveStockSearch.jsx
import React, { useState, useEffect } from "react";
import axios from "axios";
import "./LiveStockSearch.css";
const API_BASE = "https://stockmarket-rz6w.onrender.com"; // ✅ Your FastAPI backend base URL

const LiveStockSearch = ({ value, onChange }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [input, setInput] = useState(value || "");

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (input.length >= 2) {
        fetchSuggestions(input);
      } else {
        setSuggestions([]);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [input]);

  const fetchSuggestions = async (search) => {
    try {
      const res = await axios.get(`${API_BASE}/yahoo_search?q=${search}`);
      const valid = res.data.quotes.filter(
        (item) => item.symbol.endsWith(".NS") || item.symbol.endsWith(".BO")
      );
      setSuggestions(valid.slice(0, 6)); // Top 6 results
    } catch (err) {
      console.error("Suggestion fetch error:", err);
      setSuggestions([]);
    }
  };

  const handleSelect = (symbol) => {
    setInput(symbol);
    setSuggestions([]);
    onChange(symbol); // Notify parent
  };

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <input
        type="text"
        placeholder="Search NSE/BSE stock (e.g., TCS.NS, INFY.NS)"
        value={input}
        onChange={(e) => {
          setInput(e.target.value);
          onChange(e.target.value); // Update parent state too
        }}
        style={{ width: "300px", padding: "8px" }}
      />
      {suggestions.length > 0 && (
        <ul
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            background: "white",
            border: "1px solid #ccc",
            listStyle: "none",
            padding: "0",
            margin: "0",
            zIndex: 10,
            maxHeight: "180px",
            overflowY: "auto",
          }}
        >
          {suggestions.map((s) => (
            <li
              key={s.symbol}
              onClick={() => handleSelect(s.symbol)}
              style={{
                padding: "8px",
                borderBottom: "1px solid #eee",
                cursor: "pointer",
              }}
            >
              <strong>{s.symbol}</strong> — {s.shortname || s.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default LiveStockSearch;
