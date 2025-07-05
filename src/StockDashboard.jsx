import React from "react";
import "./Dashboard.css";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  LabelList,
  Cell,
} from "recharts";

// ✅ Fix: Add this block
const colors = {
  "P/E": "#f87171",
  "ROE (%)": "#4ade80",
  "ROA (%)": "#60a5fa",
  "Debt/Equity": "#facc15",
  "Dividend Yield (%)": "#a78bfa",
  "Market Cap (Cr)": "#f472b6",
  "Current Price": "#34d399",
  "P/B": "#fb923c",
  "Book Value": "#38bdf8",
  "Profit (Cr)": "#22d3ee",
  "Revenue (Cr)": "#fde047",
  "Promoter Holding (%)": "#f59e0b",
};
// ... existing imports
export default function StockDashboard({ data }) {
  const {
    company,
    ratios,
    chart_base64,
    full_report,
    order_summary,
    news_sentiment,
    news_headlines,
    market_triggers,
  } = data;

  const getColor = (label) => colors[label] || "#cbd5e1";

  const barData = Object.entries(ratios)
    .filter(([label, value]) =>
      [
        "P/E",
        "ROE (%)",
        "ROA (%)",
        "Debt/Equity",
        "Dividend Yield (%)",
        "P/B",
        "Book Value",
        "Profit (Cr)",
        "Revenue (Cr)",
        "Promoter Holding (%)",
      ].includes(label) && !isNaN(Number(value))
    )
    .map(([label, value]) => ({
      metric: label,
      value: Number(value),
      color: getColor(label),
    }));

  const finalVerdictLine = full_report
    .split("\n")
    .find((line) => line.toLowerCase().includes("📌 final verdict"));

  const verdictText = finalVerdictLine
    ?.replace(/\*\*/g, "")
    .replace("6. ", "")
    .trim();

  let verdictClass = "";
  if (verdictText?.toLowerCase().includes("avoid")) verdictClass = "verdict-avoid";
  else if (verdictText?.toLowerCase().includes("buy")) verdictClass = "verdict-buy";
  else if (verdictText?.toLowerCase().includes("sell")) verdictClass = "verdict-sell";
  else if (verdictText?.toLowerCase().includes("hold")) verdictClass = "verdict-hold";
  else if (verdictText?.toLowerCase().includes("watch")) verdictClass = "verdict-watch";

  const otherLines = full_report
    .split("\n")
    .filter((line) => !line.toLowerCase().includes("📌 final verdict"));

  return (
    <div className="dashboard">
      <h1 className="company-title">📊 {company}</h1>

      {/* Metric Cards */}
      <div className="metrics-grid">
        {Object.entries(ratios)
          .filter(([label]) => label !== "PEG Ratio" && label !== "Face Value")
          .map(([label, val], index) => (
            <div
              key={index}
              className="metric-card"
              style={{ backgroundColor: getColor(label) }}
            >
              <h3>{label}</h3>
              <p>{val ?? "N/A"}</p>
            </div>
          ))}
      </div>

      {/* Bar Chart */}
      <div className="bar-chart-section">
        <h2>📊 Fundamental Metrics (Bar Graph)</h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={barData} margin={{ top: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="metric" stroke="#ddd" />
            <YAxis stroke="#ccc" />
            <Tooltip />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              <LabelList
                dataKey="value"
                position="top"
                fill="#fff"
                fontWeight="bold"
              />
              {barData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Order Summary */}
      {order_summary && Object.keys(order_summary).length > 0 && (
        <div className="order-summary-section">
          <h2 className="order-summary-title">📦 Order Book Highlights</h2>
          <div className="metrics-grid">
            {Object.entries(order_summary).map(([label, val], index) => (
              <div
                key={index}
                className="metric-card"
                style={{ backgroundColor: "#fcd34d", color: "#1f2937" }}
              >
                <h3>{label}</h3>
                <p>{val}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technical Chart */}
      <div className="chart-container">
        <h2>📉 6-Month Technical Chart</h2>
        <img
          src={`data:image/png;base64,${chart_base64}`}
          alt="Stock chart"
          className="chart-image"
        />
      </div>

      {/* 📰 News & Market Triggers */}
      <div className="report-container">
        <h2 className="report-heading">📰 News & Market Sentiment</h2>
        <p><strong>News Sentiment:</strong> {news_sentiment}</p>
        <p><strong>FII/DII Activity:</strong> {market_triggers}</p>
        {news_headlines && news_headlines.length > 0 && (
          <ul>
            {news_headlines.map((headline, idx) => (
              <li key={idx}>🗞️ {headline}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Gemini Report */}
      <div className="report-container">
        <h2 className="report-heading">🧠 Gemini SEBI-Style Report</h2>
        <div className="report-text">
          {otherLines.map((line, idx) => {
            const cleanLine = line.replace(/\*/g, "").trim();
            const sectionMap = {
              "1. Company Overview": "report-section company-overview",
              "2. Technical Summary": "report-section technical-analysis",
              "3. Pros and Cons": "report-section pros-cons",
              "4. Investor Strategy": "report-section investor-strategy",
              "5. Suggested Entry/Exit": "report-section entry-exit",
            };
            const classList = ["report-line"];
            for (const key in sectionMap) {
              if (cleanLine.startsWith(key)) classList.push(sectionMap[key]);
            }
            const customHeaders = {
              "1. Company Overview": "1️⃣ Company Overview",
              "2. Technical Summary": "📉 Technical Summary",
              "3. Pros and Cons": "✅ Pros & ❌ Cons",
              "4. Investor Strategy": "🎯 Investor Strategy",
              "5. Suggested Entry/Exit": "⚖️ Entry & Exit Plan",
            };
            const headerKey = Object.keys(customHeaders).find((key) =>
              cleanLine.startsWith(key)
            );
            if (headerKey) {
              return (
                <p key={idx} className={`${classList.join(" ")} section-title`}>
                  {customHeaders[headerKey]}
                </p>
              );
            }
            return (
              <p key={idx} className={classList.join(" ")}>
                {cleanLine}
              </p>
            );
          })}

          {/* Final Verdict shown separately */}
          {verdictText && (
            <div className={`verdict-highlight ${verdictClass}`}>
              <h2>📌 Final Verdict</h2>
              <p>{verdictText}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
