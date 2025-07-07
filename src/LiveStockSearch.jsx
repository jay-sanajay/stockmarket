// LiveStockSearch.jsx
import React, { useState, useEffect } from "react";
import axios from "axios";

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
      const res = await axios.get(
        `https://query1.finance.yahoo.com/v1/finance/search?q=${search}&lang=en&region=IN`
      );
      const valid = res.data.quotes.filter((item) =>
        item.symbol.endsWith(".NS") || item.symbol.endsWith(".BO")
      );
      setSuggestions(valid.slice(0, 6)); // Top 6 results
    } catch {
      setSuggestions([]);
    }
  };

  const handleSelect = (symbol) => {
    setInput(symbol);
    setSuggestions([]);
    onChange(symbol);
  };

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <input
        type="text"
        placeholder="Search NSE/BSE stock (e.g., TCS, IRFC)"
        value={input}
        onChange={(e) => {
          setInput(e.target.value);
          onChange(e.target.value);
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
