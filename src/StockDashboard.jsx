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

// Updated color map without PEG Ratio or Face Value
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

export default function StockDashboard({ data }) {
  const { company, ratios, chart_base64, full_report, order_summary } = data;

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

  return (
    <div className="dashboard">
      <h1 className="company-title">📊 {company}</h1>

      {/* Metric Cards */}
      <div className="metrics-grid">
        {Object.entries(ratios)
          .filter(([label]) => label !== "PEG Ratio" && label !== "Face Value") // ✅ Exclude here
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
              <LabelList dataKey="value" position="top" fill="#fff" fontWeight="bold" />
              {barData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Order Summary Section */}
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

      {/* Chart */}
      <div className="chart-container">
        <h2>📉 6-Month Technical Chart</h2>
        <img
          src={`data:image/png;base64,${chart_base64}`}
          alt="Stock chart"
          className="chart-image"
        />
      </div>

     {/* Gemini SEBI Report */}
<div className="report-container">
  <h2 className="report-heading">AI SEBI Analyst Verdict</h2>
  <div className="report-text">
    {full_report.split("\n").map((line, idx) => {
      const cleanLine = line.replace(/\*/g, "").trim();

      const sectionMap = {
        "1. Company Overview": "report-section company-overview",
        "2. Technical Chart Analysis Summary": "report-section technical-analysis",
        "3. Pros and Cons": "report-section pros-cons",
        "4. Suggested Strategy": "report-section investor-strategy",
        "5. Gemini AI Verdict:": "report-subheading verdict",
        "6. Final Verdict:": "report-subheading final-verdict",
      };

      const verdictColors = {
        "🟢 BUY": "buy",
        "🔴 SELL": "sell",
        "⚪ HOLD": "hold",
      };

      const classList = ["report-line"];
      for (const key in sectionMap) {
        if (cleanLine.startsWith(key)) classList.push(sectionMap[key]);
      }

      for (const vKey in verdictColors) {
        if (cleanLine.includes(vKey)) classList.push(verdictColors[vKey]);
      }

      // Custom styled section headers
      const customHeaders = {
        "1. Company Overview": "1️⃣ Company Overview",
        "2. Technical Chart Analysis Summary": "📉 Technical Chart Analysis",
        "3. Pros and Cons": "✅ Pros & ❌ Cons",
        "4. Suggested Strategy": "🎯 Suggested Strategy",
        "5. Gemini AI Verdict:": "💡 Gemini Verdict",
        "6. Final Verdict:": "📌 Final Verdict",
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
  </div>
</div>

    </div>
  );
} 