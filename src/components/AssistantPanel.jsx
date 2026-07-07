import React, { useState } from "react";
import axios from "axios";
import { getApiBase } from "../api.js";

const QUICK = [
  "Which areas of the market should I watch today?",
  "Summarize overall sentiment in one paragraph.",
  "What are common risks when trading Indian large caps?",
];

export default function AssistantPanel() {
  const [q, setQ] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(message) {
    const text = (message ?? q).trim();
    if (!text) return;
    setLoading(true);
    setReply("");
    try {
      const base = getApiBase();
      const res = await axios.post(`${base}/assistant/chat`, { message: text });
      setReply(res.data?.reply || "");
    } catch (e) {
      setReply(e.response?.data?.detail || e.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card wide assistant-panel">
      <h3>Daily assistant</h3>
      <p className="muted small">
        Short answers from Gemini (not advice). Requires{" "}
        <code className="inline-code">GEMINI_API_KEY</code> on the API.
      </p>
      <div className="quick-prompts">
        {QUICK.map((p) => (
          <button key={p} type="button" className="ticker-chip" onClick={() => send(p)}>
            {p}
          </button>
        ))}
      </div>
      <div className="form-row">
        <input
          placeholder="Ask anything about markets or your routine…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button type="button" onClick={() => send()} disabled={loading}>
          {loading ? "…" : "Ask"}
        </button>
      </div>
      {reply && <p className="prose assistant-reply">{reply}</p>}
    </section>
  );
}
