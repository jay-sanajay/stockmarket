import React, { useEffect, useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { Link } from "react-router-dom";

export default function WatchlistPage() {
  const { token, authHeaders } = useAuth();
  const [lists, setLists] = useState([]);
  const [cards, setCards] = useState(null);
  const [wid, setWid] = useState(null);
  const [symbol, setSymbol] = useState("");
  const [err, setErr] = useState("");

  const base = getApiBase();

  useEffect(() => {
    if (!token) return;
    axios
      .get(`${base}/watchlists`, { headers: authHeaders })
      .then((r) => {
        setLists(r.data);
        if (r.data[0]) setWid(r.data[0].id);
      })
      .catch((e) => setErr(String(e.response?.data?.detail || e.message)));
  }, [token, authHeaders, base]);

  useEffect(() => {
    if (!token || !wid) return;
    axios
      .get(`${base}/watchlists/${wid}/cards`, { headers: authHeaders })
      .then((r) => setCards(r.data))
      .catch(() => setCards({ cards: [] }));
  }, [token, wid, authHeaders, base]);

  function add() {
    if (!wid || !symbol.trim()) return;
    axios
      .post(
        `${base}/watchlists/${wid}/items`,
        { symbol: symbol.trim(), pinned: false },
        { headers: authHeaders }
      )
      .then(() => {
        setSymbol("");
        return axios.get(`${base}/watchlists/${wid}/cards`, { headers: authHeaders });
      })
      .then((r) => setCards(r.data))
      .catch((e) => setErr(String(e.response?.data?.detail || e.message)));
  }

  if (!token) {
    return (
      <div className="page-pad">
        <p>
          <Link to="/login">Log in</Link> to use watchlists.
        </p>
      </div>
    );
  }

  return (
    <div className="page-pad">
      <h1>Watchlist</h1>
      {err && <p className="error-inline">{err}</p>}
      <div className="form-row">
        <select value={wid ?? ""} onChange={(e) => setWid(Number(e.target.value))}>
          {lists.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
        <input
          placeholder="TCS.NS"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />
        <button type="button" onClick={add}>
          Add
        </button>
      </div>
      <div className="watch-grid">
        {(cards?.cards || []).map((c) => (
          <div key={c.symbol} className="card watch-card">
            <div className="wc-head">
              <strong>{c.symbol}</strong>
              <span className="muted">{c.company || ""}</span>
            </div>
            {c.error ? (
              <p className="error-inline">{c.error}</p>
            ) : (
              <>
                <p>₹{c.current_price ?? "—"}</p>
                <p>{c.verdict}</p>
                <p className="small">RSI {c.rsi ?? "—"} · {c.trend}</p>
                <p className="small">{c.one_liner}</p>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
