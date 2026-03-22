import React, { useMemo, useState, useCallback } from "react";
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

const COLORS = {
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

const TABS = [
  { id: "overview", label: "Overview", icon: "◆" },
  { id: "fundamentals", label: "Fundamentals", icon: "▤" },
  { id: "charts", label: "Charts", icon: "◇" },
  { id: "news", label: "News & flow", icon: "▸" },
  { id: "report", label: "AI report", icon: "✦" },
  { id: "strategy", label: "Strategy", icon: "◎" },
];

function normalizeScore(raw) {
  if (raw == null || Number.isNaN(Number(raw))) return null;
  const n = Number(raw);
  return Math.max(-3, Math.min(12, n));
}

export default function StockDashboard({ data }) {
  const [tab, setTab] = useState("overview");
  const [copied, setCopied] = useState(false);

  const {
    company,
    ratios = {},
    chart_base64,
    full_report = "",
    order_summary,
    news_sentiment,
    news_headlines,
    market_triggers,
    strategy_type,
    strategy_reason,
    entry_zones = [],
    stop_loss_zone,
    target_zones = [],
    signal_score,
    signal_breakdown = {},
    retail_stock,
    symbol,
  } = data;

  const reasonText = strategy_reason || "";
  const getColor = (label) => COLORS[label] || "#94a3b8";

  const barData = useMemo(
    () =>
      Object.entries(ratios)
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
        })),
    [ratios]
  );

  const verdictText =
    data.verdict || "📌 Final Verdict: ⛔ Avoid — No clear signal.";

  let verdictClass = "";
  const verdictLower = (strategy_type || verdictText).toLowerCase();
  if (verdictLower.includes("avoid")) verdictClass = "verdict-avoid";
  else if (verdictLower.includes("buy")) verdictClass = "verdict-buy";
  else if (verdictLower.includes("sell")) verdictClass = "verdict-sell";
  else if (verdictLower.includes("hold")) verdictClass = "verdict-hold";
  else if (verdictLower.includes("watch")) verdictClass = "verdict-watch";

  const otherLines = full_report
    .split("\n")
    .filter((line) => !line.toLowerCase().includes("📌 final verdict"));

  const scoreNorm = normalizeScore(signal_score);
  const scoreBarPct =
    scoreNorm == null ? 0 : ((scoreNorm + 3) / 15) * 100;

  const copyReport = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(full_report || verdictText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [full_report, verdictText]);

  const reportSections = (
    <div className="report-text">
      {otherLines.map((line, idx) => {
        const cleanLine = line.replace(/\*/g, "").trim();
        const sectionMap = {
          "1. Company Overview": "report-section company-overview",
          "2. Technical Summary": "report-section technical-analysis",
          "3. Pros and Cons": "report-section pros-cons",
          "4. Strategy": "report-section investor-strategy",
          "5. Entry/Exit": "report-section entry-exit",
        };
        const classList = ["report-line"];
        for (const key in sectionMap) {
          if (cleanLine.startsWith(key)) classList.push(sectionMap[key]);
        }
        const customHeaders = {
          "1. Company Overview": "1 · Company overview",
          "2. Technical Summary": "Technical summary",
          "3. Pros and Cons": "Pros & cons",
          "4. Strategy": "Strategy",
          "5. Entry/Exit": "Entry & exit",
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

      {verdictText && (
        <div className={`verdict-highlight ${verdictClass}`}>
          <h2>Final verdict</h2>
          <p>
            <strong>{verdictText}</strong>
          </p>
          {reasonText && <p className="verdict-reason">{reasonText}</p>}
        </div>
      )}
    </div>
  );

  return (
    <div className="dashboard dashboard-advanced">
      <header className="dash-hero">
        <div className="dash-hero-main">
          <p className="dash-eyebrow">{symbol}</p>
          <h1 className="company-title">{company}</h1>
          {strategy_type && (
            <span className={`strategy-pill ${verdictClass}`}>{strategy_type}</span>
          )}
        </div>
        <div className="dash-hero-stats">
          <div className="stat-block">
            <span className="stat-label">Signal score</span>
            <div className="score-meter-wrap">
              <div
                className="score-meter-fill"
                style={{ width: `${Math.min(100, Math.max(0, scoreBarPct))}%` }}
              />
            </div>
            <span className="stat-value">
              {signal_score != null ? Number(signal_score).toFixed(1) : "—"}
            </span>
          </div>
          <div className="stat-block">
            <span className="stat-label">Retail-heavy</span>
            <span className="stat-value bool">{retail_stock ? "Yes" : "No"}</span>
          </div>
          <div className="stat-block wide">
            <span className="stat-label">Key breakdown</span>
            <div className="breakdown-chips">
              {Object.entries(signal_breakdown).map(([k, v]) => (
                <span key={k} className="chip-sm" title={v}>
                  <strong>{k}</strong> · {v}
                </span>
              ))}
            </div>
          </div>
        </div>
      </header>

      <nav className="dash-tabs" role="tablist" aria-label="Report sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`dash-tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            <span className="tab-icon" aria-hidden>
              {t.icon}
            </span>
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <section className="tab-panel glass-panel" role="tabpanel">
          <div className="overview-grid">
            <div className={`verdict-card ${verdictClass}`}>
              <h3>Verdict</h3>
              <p className="verdict-lead">{strategy_type || "—"}</p>
              <p className="verdict-sub">{reasonText || "Run other tabs for detail."}</p>
            </div>
            <div className="mini-metrics">
              <div>
                <span className="mm-label">P/E</span>
                <span className="mm-val">{ratios["P/E"] ?? "—"}</span>
              </div>
              <div>
                <span className="mm-label">ROE %</span>
                <span className="mm-val">{ratios["ROE (%)"] ?? "—"}</span>
              </div>
              <div>
                <span className="mm-label">Price</span>
                <span className="mm-val">₹{ratios["Current Price"] ?? "—"}</span>
              </div>
              <div>
                <span className="mm-label">M-cap (Cr)</span>
                <span className="mm-val">{ratios["Market Cap (Cr)"] ?? "—"}</span>
              </div>
            </div>
          </div>
          <details className="dev-details">
            <summary>Raw strategy payload (debug)</summary>
            <pre>
              {JSON.stringify(
                { entry_zones, target_zones, stop_loss_zone },
                null,
                2
              )}
            </pre>
          </details>
        </section>
      )}

      {tab === "fundamentals" && (
        <section className="tab-panel" role="tabpanel">
          <div className="metrics-grid metrics-grid-advanced">
            {Object.entries(ratios)
              .filter(([label]) => label !== "PEG Ratio" && label !== "Face Value")
              .map(([label, val], index) => (
                <div
                  key={index}
                  className="metric-card metric-card-advanced"
                  style={{
                    background: `linear-gradient(145deg, ${getColor(label)}55 0%, #1e293b 100%)`,
                  }}
                >
                  <h3>{label}</h3>
                  <p>{val ?? "N/A"}</p>
                </div>
              ))}
          </div>
          <div className="bar-chart-section">
            <h2>Fundamental comparison</h2>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={barData} margin={{ top: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis
                    dataKey="metric"
                    stroke="#94a3b8"
                    tick={{ fontSize: 11 }}
                    angle={-28}
                    textAnchor="end"
                    height={70}
                  />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      background: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    <LabelList
                      dataKey="value"
                      position="top"
                      fill="#f8fafc"
                      fontSize={11}
                    />
                    {barData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {order_summary && Object.keys(order_summary).length > 0 && (
            <div className="order-summary-section">
              <h2 className="order-summary-title">Order book highlights</h2>
              <div className="metrics-grid">
                {Object.entries(order_summary).map(([label, val], index) => (
                  <div key={index} className="metric-card metric-card-order">
                    <h3>{label}</h3>
                    <p>{val}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {tab === "charts" && (
        <section className="tab-panel" role="tabpanel">
          <div className="chart-container chart-container-advanced">
            <h2>Price action (recent ~6 months)</h2>
            {chart_base64 ? (
              <img
                src={`data:image/png;base64,${chart_base64}`}
                alt={`Price chart for ${company}`}
                className="chart-image"
                loading="lazy"
              />
            ) : (
              <p className="muted">Chart unavailable.</p>
            )}
          </div>
        </section>
      )}

      {tab === "news" && (
        <section className="tab-panel glass-panel" role="tabpanel">
          <h2 className="inline-heading">Sentiment & flows</h2>
          <div className="news-grid">
            <article className="news-card">
              <h3>Headline sentiment</h3>
              <p className="news-body">{news_sentiment}</p>
            </article>
            <article className="news-card">
              <h3>FII / DII (NSE)</h3>
              <p className="news-body small">{market_triggers}</p>
            </article>
          </div>
          {news_headlines && news_headlines.length > 0 && (
            <ul className="headline-list">
              {news_headlines.map((headline, idx) => (
                <li key={idx}>
                  <span className="hl-dot" />
                  {headline}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {tab === "report" && (
        <section className="tab-panel report-container report-advanced" role="tabpanel">
          <div className="report-toolbar">
            <h2 className="report-heading">Investment narrative</h2>
            <button type="button" className="btn-ghost" onClick={copyReport}>
              {copied ? "Copied" : "Copy report"}
            </button>
          </div>
          {reportSections}
        </section>
      )}

      {tab === "strategy" && (
        <section className="tab-panel" role="tabpanel">
          {(entry_zones.length > 0 ||
            target_zones.length > 0 ||
            stop_loss_zone) && (
            <div className="strategy-layout">
              {entry_zones.length > 0 && (
                <div className="strategy-card entry">
                  <h3>Entry zones</h3>
                  <ul>
                    {entry_zones.map((zone, idx) => (
                      <li key={idx}>
                        <strong>{zone.range}</strong>
                        <span>{zone.reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {target_zones.length > 0 && (
                <div className="strategy-card target">
                  <h3>Targets</h3>
                  <ul>
                    {target_zones.map((zone, idx) => (
                      <li key={idx}>
                        <strong>{zone.level}</strong>
                        <span>{zone.reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {stop_loss_zone && (
                <div className="strategy-card stop">
                  <h3>Stop loss</h3>
                  <p>{stop_loss_zone}</p>
                </div>
              )}
            </div>
          )}
          {entry_zones.length === 0 &&
            target_zones.length === 0 &&
            !stop_loss_zone && (
              <p className="muted centered">
                No entry/target bands for this signal — see AI report.
              </p>
            )}
        </section>
      )}

      <footer className="dash-footer">
        <p>
          Educational analytics only — not investment advice. Verify data with official
          filings and your advisor.
        </p>
      </footer>
    </div>
  );
}
