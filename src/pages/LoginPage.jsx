import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { getApiBase } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { setToken, refreshMe } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  async function submit(path) {
    setMsg("");
    const base = getApiBase();
    try {
      const res = await axios.post(`${base}/auth/${path}`, { email, password });
      setToken(res.data.access_token);
      await refreshMe();
      nav("/");
    } catch (e) {
      setMsg(e.response?.data?.detail || e.message || "Failed");
    }
  }

  return (
    <div className="page-pad narrow">
      <h1>Account</h1>
      <p className="muted">Watchlists, alerts, and portfolio are tied to your login.</p>
      <div className="form-stack">
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
        </label>
        <label>
          Password (8+ chars)
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
          />
        </label>
        {msg && <p className="error-inline">{String(msg)}</p>}
        <div className="btn-row">
          <button type="button" onClick={() => submit("login")}>
            Log in
          </button>
          <button type="button" className="secondary" onClick={() => submit("register")}>
            Create account
          </button>
        </div>
      </div>
    </div>
  );
}
