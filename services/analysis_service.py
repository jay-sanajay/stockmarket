"""Stock analysis orchestration (yfinance + scoring + Gemini report)."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import random
import time
from datetime import datetime

import pandas as pd
import yfinance as yf

from config import get_analysis_cache_ttl_seconds, is_render_deployment
from services import chart_service, gemini_service, market_service, news_service
from services.technical_service import compute_technicals, last_numeric
from utils.cache import BoundedTTLCache
from utils.rate_limit import looks_like_upstream_rate_limit

logger = logging.getLogger(__name__)

stock_cache = BoundedTTLCache(
    max_size=64,
    ttl_seconds=get_analysis_cache_ttl_seconds(),
)


def is_retail_stock(info: dict) -> bool:
    try:
        held = info.get("heldPercentInstitutions")
        if held is None:
            return False
        return float(held) < 0.1
    except (TypeError, ValueError) as e:
        logger.warning("is_retail_stock: %s", e)
        return False


def log_verdict(
    symbol: str,
    price: float | None,
    verdict: str,
    *,
    signal_score: float | None = None,
    strategy_type: str | None = None,
    news_sentiment: str | None = None,
) -> None:
    record = {
        "symbol": symbol,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "price": price,
        "verdict": verdict,
    }
    try:
        with open("verdict_log.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(record)
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
    except FileNotFoundError:
        with open("verdict_log.json", "w", encoding="utf-8") as f:
            json.dump([record], f, indent=2)
    except Exception as e:
        logger.exception("log_verdict failed: %s", e)
    try:
        from services.verdict_db_service import record_verdict_db

        record_verdict_db(
            symbol,
            price,
            verdict,
            signal_score=signal_score,
            strategy_type=strategy_type,
            news_sentiment=news_sentiment,
        )
    except Exception as e:
        logger.debug("verdict DB mirror skipped: %s", e)


def _is_yf_transient(exc: BaseException) -> bool:
    s = str(exc).lower()
    return (
        "too many" in s
        or "429" in s
        or "rate" in s
        or "timeout" in s
        or "timed out" in s
        or "connection" in s
        or "temporar" in s
        or "unusual traffic" in s
        or ("yahoo" in s and ("blocked" in s or "error" in s or "limit" in s))
        or looks_like_upstream_rate_limit(exc)
    )


# Render shares Yahoo’s rate limits across many apps — more retries + longer backoff.
_YF_RETRIES = 5 if is_render_deployment() else 3
_YF_DELAYS = (0.0, 5.0, 14.0, 28.0, 50.0) if is_render_deployment() else (0.0, 4.0, 10.0)


def _normalize_yf_download_df(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Single-ticker download may use MultiIndex columns — flatten to Open/High/Low/Close/Volume."""
    if df is None or df.empty:
        raise ValueError("empty Yahoo download")
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        tickers = out.columns.get_level_values(-1).unique().tolist()
        if symbol in tickers:
            out = out.xs(symbol, axis=1, level=-1)
        elif len(tickers) == 1:
            out = out.xs(tickers[0], axis=1, level=-1)
        else:
            out = out.droplevel(1, axis=1)
    if "Close" not in out.columns:
        raise ValueError("Yahoo download missing Close column")
    if "Volume" not in out.columns:
        out["Volume"] = 0.0
    return out


def _download_to_info_hist(symbol: str, period: str) -> tuple[dict, pd.DataFrame]:
    """
    Alternate Yahoo path (yf.download) — different endpoints than Ticker.info/history;
    often still works when the Ticker path is rate-limited on shared hosting.
    Tries to also fetch fundamentals separately via Ticker.info.
    """
    if is_render_deployment():
        time.sleep(random.uniform(0.1, 0.45))
    raw = yf.download(
        symbol,
        period=period,
        progress=False,
        threads=False,
        auto_adjust=True,
    )
    hist = _normalize_yf_download_df(raw, symbol)
    last_close = float(hist["Close"].iloc[-1])

    # Try to get fundamentals even in fallback mode
    info = {
        "longName": symbol,
        "shortName": symbol,
        "currentPrice": last_close,
        "regularMarketPrice": last_close,
        "regularMarketPreviousClose": last_close,
        "previousClose": last_close,
    }

    # Attempt to fetch fast_info separately — this uses chart endpoints which are rarely blocked
    try:
        if is_render_deployment():
            time.sleep(random.uniform(0.2, 0.5))
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info
        
        info["marketCap"] = getattr(fi, "market_cap", None)
        info["currentPrice"] = getattr(fi, "last_price", last_close)
        info["previousClose"] = getattr(fi, "previous_close", last_close)
        info["fiftyTwoWeekHigh"] = getattr(fi, "year_high", None)
        info["fiftyTwoWeekLow"] = getattr(fi, "year_low", None)
        info["fiftyDayAverage"] = getattr(fi, "fifty_day_average", None)
        info["twoHundredDayAverage"] = getattr(fi, "two_hundred_day_average", None)
        
        logger.info("Fallback fast_info fetched for %s", symbol)
    except Exception as e:
        logger.warning("Fallback fast_info fetch failed for %s: %s", symbol, e)

    return info, hist


def _fetch_yfinance(symbol: str, timeout: float | None = None):
    """Ticker first (full fundamentals); then yf.download fallback (OHLCV-only) on failure."""
    if timeout is None:
        timeout = 75.0 if is_render_deployment() else 45.0

    def _work_ticker():
        if is_render_deployment():
            time.sleep(random.uniform(0.2, 0.8))
            
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not isinstance(info, dict):
            info = {}
        if is_render_deployment():
            time.sleep(0.45)
        hist = ticker.history(period="2y")
        return info, hist

    last_err: BaseException | None = None
    for attempt in range(_YF_RETRIES):
        if attempt > 0:
            time.sleep(_YF_DELAYS[attempt])
            logger.warning(
                "yfinance Ticker retry %s/%s for %s",
                attempt + 1,
                _YF_RETRIES,
                symbol,
            )
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_work_ticker)
                return fut.result(timeout=timeout)
        except Exception as e:
            last_err = e
            if _is_yf_transient(e) and attempt < _YF_RETRIES - 1:
                continue
            break

    logger.warning(
        "yfinance Ticker failed for %s — trying download fallback (last: %s)",
        symbol,
        last_err,
    )
    for period in ("2y", "1y", "6mo"):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_download_to_info_hist, symbol, period)
                return fut.result(timeout=timeout)
        except Exception as e:
            last_err = e
            logger.warning("download fallback period=%s failed: %s", period, e)
            time.sleep(1.5)

    if last_err:
        raise last_err
    raise RuntimeError("yfinance: no data")


def _safe_pe(info: dict):
    raw = info.get("trailingPE")
    try:
        if raw is not None and float(raw) > 0:
            return float(raw)
    except (TypeError, ValueError):
        pass
    return None


def _parse_de_ratio(val) -> float | None:
    try:
        ratio = float(val)
        return round(ratio / 100, 2) if ratio > 10 else round(ratio, 2)
    except (TypeError, ValueError):
        return None


def run_analysis(stock: str) -> dict:
    """
    Full pipeline for one symbol. Raises on unrecoverable errors;
    returns dict with \"error\" key for client-facing validation failures.
    """
    symbol = stock.upper().strip()
    cached = stock_cache.get(symbol)
    if cached is not None:
        logger.info("Cache hit for %s", symbol)
        return cached

    try:
        info, hist = _fetch_yfinance(symbol)
    except concurrent.futures.TimeoutError:
        logger.exception("yfinance timed out for %s", symbol)
        raise TimeoutError(f"yfinance timed out for {symbol}") from None
    except Exception as e:
        logger.exception("yfinance fetch failed for %s: %s", symbol, e)
        raise

    if hist is None or hist.empty:
        return {"error": "Invalid stock symbol or no price history."}

    info = info or {}
    price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("regularMarketPreviousClose")
        or info.get("previousClose")
    )
    try:
        price = float(price) if price is not None else 0.0
    except (TypeError, ValueError):
        price = 0.0

    if price <= 0:
        return {"error": "Invalid stock symbol or no current price data."}

    hist = compute_technicals(hist)
    try:
        # Show ~6 months of bars on the chart; indicators use full 2y history
        hist_chart = hist.tail(130) if len(hist) > 130 else hist
        chart = chart_service.generate_chart_base64(
            hist_chart, title="Price Chart (recent ~6 months)"
        )
    except Exception as e:
        logger.exception("Chart generation failed: %s", e)
        chart = ""

    pe = _safe_pe(info)
    pb = info.get("priceToBook")
    eps = info.get("trailingEps")
    book_value = info.get("bookValue")

    roe_raw = info.get("returnOnEquity")
    roe = float(roe_raw) * 100 if roe_raw is not None else None
    roa_raw = info.get("returnOnAssets")
    roa = float(roa_raw) * 100 if roa_raw is not None else None
    roce_raw = info.get("returnOnCapitalEmployed")
    roce = float(roce_raw) * 100 if roce_raw is not None else None

    de_ratio = _parse_de_ratio(info.get("debtToEquity"))

    raw_div = info.get("dividendYield") or 0
    try:
        raw_div_f = float(raw_div) if raw_div is not None else 0.0
    except (TypeError, ValueError):
        raw_div_f = 0.0
    # yfinance often returns dividend yield as a decimal (e.g. 0.02 for 2%).
    if raw_div_f and raw_div_f < 1:
        div_yield = raw_div_f * 100
    else:
        div_yield = raw_div_f

    mcap = float(info.get("marketCap") or 0)
    revenue = float(info.get("totalRevenue") or 0)
    profit = float(info.get("netIncomeToCommon") or 0)
    retail_flag = is_retail_stock(info)

    sentiment, headlines = news_service.fetch_news_sentiment(symbol)
    if not sentiment:
        sentiment = "Neutral"
    triggers = market_service.fetch_market_triggers()

    rsi = last_numeric(hist["RSI"], "RSI")
    ma50 = last_numeric(hist["MA50"], "MA50")
    ma200 = last_numeric(hist["MA200"], "MA200")

    partial_data = False
    if rsi is None:
        rsi = 50.0  # Neutral default
        partial_data = True
    if ma50 is None:
        ma50 = price  # Use current price as proxy
        partial_data = True
    if ma200 is None:
        ma200 = price  # Use current price as proxy
        partial_data = True

    if partial_data:
        logger.warning(
            "Partial indicator data for %s (len=%s) — using defaults for missing indicators",
            symbol, len(hist),
        )

    trend = "Uptrend" if ma50 > ma200 else "Downtrend"

    score = 0.0
    explanations: dict[str, str] = {}

    if rsi < 30:
        score += 1
        explanations["RSI"] = "Oversold (<30)"
    elif rsi > 70:
        score -= 1
        explanations["RSI"] = "Overbought (>70)"
    else:
        explanations["RSI"] = "Neutral"

    if ma50 > ma200:
        score += 2
        explanations["MA Trend"] = "Uptrend"
    else:
        score -= 0.5
        explanations["MA Trend"] = "Downtrend"

    s_low = sentiment.lower()
    if "positive" in s_low:
        score += 1
        explanations["Sentiment"] = "Positive"
    elif "negative" in s_low:
        score -= 1
        explanations["Sentiment"] = "Negative"
    else:
        score += 0.5
        explanations["Sentiment"] = "Neutral"

    if pe and pe < 15:
        score += 1
        explanations["P/E"] = f"Attractive: {pe}"
    elif pe and pe > 35:
        score -= 1
        explanations["P/E"] = f"Expensive: {pe}"
    else:
        explanations["P/E"] = f"Moderate: {pe}"

    if de_ratio and de_ratio < 1:
        score += 1
        explanations["D/E"] = f"Healthy: {de_ratio}"
    elif de_ratio and de_ratio > 2:
        industry = (info.get("industry") or "").lower()
        if roe and roe > 30 and "services" in industry:
            explanations["D/E"] = f"High but acceptable for IT: {de_ratio}"
        else:
            score -= 0.5
            explanations["D/E"] = f"Risky: {de_ratio}"
    else:
        explanations["D/E"] = f"Moderate: {de_ratio}"

    if roe and roe > 15:
        score += 1
        explanations["ROE"] = f"Strong: {roe:.2f}%"
    elif roe and roe < 5:
        score -= 1
        explanations["ROE"] = f"Weak: {roe:.2f}%"

    if roa and roa > 10:
        score += 1
        explanations["ROA"] = f"Efficient: {roa:.2f}%"

    if profit and revenue and revenue != 0 and (profit / revenue) > 0.15:
        score += 1
        explanations["Profit Margin"] = f"{round((profit / revenue) * 100, 2)}%"

    if roce and roce > 12:
        score += 1
        explanations["ROCE"] = f"Efficient: {roce:.2f}%"
    elif roce and roce < 5:
        score -= 1
        explanations["ROCE"] = f"Poor: {roce:.2f}%"

    industry = (info.get("industry") or "").lower()
    if roe and roe > 40 and mcap > 1e12 and "services" in industry:
        if score < 4:
            score = 4
            explanations["Fundamental Override"] = "High ROE & large-cap IT company"

    if score >= 7 and roe and roe > 20 and div_yield > 2:
        suggested = "✅ Strong Buy"
        strategy_notes = "Strong EPS, low P/E, uptrend, positive sentiment"
    elif score >= 5:
        suggested = "✅ Buy"
        strategy_notes = "Good fundamentals, uptrend or oversold"
    elif 4 <= score < 5:
        suggested = "📊 Long-Term Buy"
        strategy_notes = "Strong fundamentals, but downtrend or neutral macro"
    elif 3 <= score < 4:
        suggested = "🟡 Hold"
        strategy_notes = "Mixed signals. Hold and monitor for clearer direction."
    elif 2 <= score < 3:
        suggested = "📈 Short-Term Buy"
        strategy_notes = "Technical bounce expected (e.g., oversold RSI)"
    elif 1 <= score < 2:
        suggested = "⚠️ Watch"
        strategy_notes = "Weak indicators. Wait for confirmation."
    else:
        suggested = "⛔ Avoid"
        strategy_notes = "Bad metrics or high risk (debt, downtrend, overbought, etc.)"

    entry_zones: list[dict[str, str]] = []
    target_zones: list[dict[str, str]] = []
    stop_loss_zone: str | None = None

    if "buy" in suggested.lower() or suggested in ("⚠️ Watch", "🟡 Hold"):
        if rsi < 60 and price > ma50:
            entry_zones.append(
                {
                    "range": f"₹{round(ma50 * 0.98, 2)}–₹{round(ma50 * 1.02, 2)}",
                    "reason": "Near MA50 support & RSI not overbought",
                }
            )
        entry_zones.append(
            {
                "range": f"₹{round(price * 0.90, 2)}–₹{round(price * 0.95, 2)}",
                "reason": "Moderate dip (~5–10%)",
            }
        )
        if ma200 and price < ma200 * 1.05:
            entry_zones.append(
                {
                    "range": f"₹{round(ma200 * 0.95, 2)}–₹{round(ma200, 2)}",
                    "reason": "Deep support near 200‑day MA",
                }
            )
        try:
            lowest = float(entry_zones[-1]["range"].split("–")[0].replace("₹", ""))
            stop_loss_zone = f"₹{round(lowest * 0.93, 2)} (7% below lower band)"
        except (IndexError, ValueError) as e:
            logger.warning("stop_loss parse: %s", e)
            stop_loss_zone = "Not defined"

        target_zones.append(
            {
                "level": f"₹{round(ma50 * 1.15, 2)}",
                "reason": "15% above MA50 — short/mid‑term target",
            }
        )
        target_zones.append(
            {
                "level": f"₹{round(ma50 * 1.25, 2)}",
                "reason": "25% above MA50 if momentum resumes",
            }
        )
    else:
        stop_loss_zone = "N/A"

    today_s = datetime.now().strftime("%Y-%m-%d")
    headlines_text = (
        "\n".join("- " + h for h in headlines) if headlines else "- No headlines available"
    )
    long_name = info.get("longName") or info.get("shortName") or symbol
    prompt = f"""
You are a SEBI-registered investment advisor. Analyze the following stock and prepare a final investment report.

Stock: {long_name}
Symbol: {symbol}
Date: {today_s}
Current Price: ₹{price}
Market Cap: ₹{mcap/1e7:.2f} Cr
Retail Stock: {'Yes' if retail_flag else 'No'}

Financials:
- P/E: {pe}, P/B: {pb}, EPS: {eps}, Book Value: ₹{book_value}
- ROE: {roe}%, ROA: {roa}%, ROCE: {roce}%
- Debt/Equity: {de_ratio}, Dividend Yield: {div_yield:.2f}%
- Revenue: ₹{revenue/1e7:.2f} Cr, Profit: ₹{profit/1e7:.2f} Cr

Technical:
- RSI: {rsi}, MA50: {ma50}, MA200: {ma200}, Trend: {trend}

News Sentiment: {sentiment}
Market Activity: {triggers}
Headlines:
{headlines_text}

🧠 Strategy-Based Verdict: {suggested}
📌 Reason: {strategy_notes}

Strict FORMAT:
1. Company Overview
2. Technical Summary
3. Pros & Cons
4. Strategy
5. Entry/Exit
6. 📌 Final Verdict: **{suggested}** (1-line reason only)
"""

    try:
        gemini_report = gemini_service.generate_text(
            prompt, context="run_analysis_report"
        ).strip()
    except Exception as e:
        logger.exception("Gemini report failed: %s", e)
        if looks_like_upstream_rate_limit(e):
            gemini_report = (
                "### AI narrative temporarily unavailable (Google AI rate limit on shared hosting).\n\n"
                "Fundamentals, technicals, and the verdict below still use live data. "
                "Wait a few minutes and analyze again for the full Gemini report.\n\n"
                f"**Suggested stance:** {suggested}\n**Summary:** {strategy_notes}"
            )
        else:
            gemini_report = f"Report generation failed: {e!s}"

    verdict = f"📌 Final Verdict: **{suggested}** — {strategy_notes}"

    try:
        log_verdict(
            symbol,
            price,
            verdict,
            signal_score=score,
            strategy_type=suggested,
            news_sentiment=sentiment,
        )
    except Exception:
        pass

    result = {
        "company": long_name,
        "symbol": symbol,
        "technical_snapshot": {
            "rsi": rsi,
            "ma50": ma50,
            "ma200": ma200,
            "trend": trend,
        },
        "ratios": {
            "P/E": pe,
            "P/B": pb,
            "EPS": eps,
            "Book Value": book_value,
            "ROE (%)": round(roe, 2) if roe is not None else None,
            "ROA (%)": round(roa, 2) if roa is not None else None,
            "ROCE (%)": round(roce, 2) if roce is not None else None,
            "Debt/Equity": de_ratio,
            "Dividend Yield (%)": round(div_yield, 2),
            "Market Cap (Cr)": round(mcap / 1e7, 2),
            "Current Price": price,
            "Revenue (Cr)": round(revenue / 1e7, 2) if revenue else None,
            "Profit (Cr)": round(profit / 1e7, 2) if profit else None,
        },
        "chart_base64": chart,
        "news_sentiment": sentiment,
        "news_headlines": headlines,
        "market_triggers": triggers,
        "retail_stock": retail_flag,
        "signal_score": score,
        "signal_breakdown": explanations,
        "full_report": gemini_report,
        "verdict": verdict,
        "strategy_type": suggested,
        "strategy_reason": strategy_notes,
        "entry_zones": entry_zones,
        "stop_loss_zone": stop_loss_zone,
        "target_zones": target_zones,
    }
    stock_cache.set(symbol, result)
    return result
