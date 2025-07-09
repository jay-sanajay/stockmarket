from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import google.generativeai as genai
import io, base64, os, requests, json
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

load_dotenv()
today = datetime.now().strftime("%B %d, %Y")

GEMINI_API_KEY = "AIzaSyB9VNMFfpB_95-6ZMh_UW8FoSYMjQCNSUQ"
NEWSDATA_API_KEY = "pub_48e1a7203f9c402ab31981ca24cfc2c6"

# Gemini Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# FastAPI app init
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"status": "ok", "message": "Stock Analyzer API is live 🚀"}

@app.get("/yahoo_search")
def yahoo_search(q: str):
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={q}&lang=en&region=IN"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}
# ==== Chart and Technicals ====
def generate_chart_base64(hist):
    plt.figure(figsize=(10, 4))
    plt.plot(hist.index, hist["Close"], label="Close Price", color="cyan")
    plt.title(f"Price Chart (6M)")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def compute_technicals(hist):
    hist["MA50"] = hist["Close"].rolling(window=50).mean()
    hist["MA200"] = hist["Close"].rolling(window=200).mean()

    delta = hist["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    hist["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = hist["Close"].ewm(span=12, adjust=False).mean()
    ema26 = hist["Close"].ewm(span=26, adjust=False).mean()
    hist["MACD"] = ema12 - ema26
    hist["Signal"] = hist["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    hist["BB_MA"] = hist["Close"].rolling(window=20).mean()
    hist["BB_STD"] = hist["Close"].rolling(window=20).std()
    hist["Upper_BB"] = hist["BB_MA"] + 2 * hist["BB_STD"]
    hist["Lower_BB"] = hist["BB_MA"] - 2 * hist["BB_STD"]

    # Volume Trend
    hist["Volume_Trend"] = hist["Volume"].pct_change().rolling(5).mean()
    return hist

# ==== News + Market Triggers ====
def fetch_news_sentiment(stock_name: str, fallback_term: str = "Indian Stock Market"):
    try:
        # Try company-specific news first
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={stock_name}&country=in&language=en"
        res = requests.get(url)
        data = res.json()
        headlines = [article["title"] for article in data.get("results", []) if article.get("title")][:5]

        # Fallback to general stock news
        if not headlines:
            url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={fallback_term}&country=in&language=en"
            res = requests.get(url)
            data = res.json()
            headlines = [article["title"] for article in data.get("results", []) if article.get("title")][:5]

        if not headlines:
            return "No news available", []

        joined = "\n- ".join(headlines)
        prompt = f"""
You are a financial news analyst. Given these headlines related to {stock_name}, determine the overall market sentiment.

Headlines:
- {joined}

Classify sentiment as one of the following:
1. Positive
2. Negative
3. Neutral

Write the sentiment as a one-word summary first, followed by a brief reason based on patterns in the headlines.
"""
        sentiment_response = model.generate_content(prompt)
        sentiment = sentiment_response.text.strip()
        return sentiment, headlines

    except Exception as e:
        return f"Sentiment analysis error: {str(e)}", []

import requests

import requests

def fetch_market_triggers():
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com/"
        }

        # Start session and get initial cookies
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5)

        res = session.get(url, timeout=5)
        res.raise_for_status()

        try:
            data = res.json()
        except ValueError:
            return "Market trigger fetch error: Invalid JSON from NSE"

        if not isinstance(data, dict) or "data" not in data or not data["data"]:
            return "Market trigger fetch error: Unexpected API structure"

        latest = data["data"][-1]

        date = latest.get("date")
        fii_buy = latest.get("buyValue", "N/A")
        fii_sell = latest.get("sellValue", "N/A")
        dii_buy = latest.get("buyValueDii", "N/A")
        dii_sell = latest.get("sellValueDii", "N/A")

        return f"📅 {date} | FII: Buy ₹{fii_buy:,} Cr / Sell ₹{fii_sell:,} Cr | DII: Buy ₹{dii_buy:,} Cr / Sell ₹{dii_sell:,} Cr"

    except Exception as e:
        return f"Market trigger fetch error: {str(e)}"



def is_retail_stock(info):
    try:
        return info.get("heldPercentInstitutions", 1) < 0.1
    except:
        return False

# ==== Backtesting: Save to JSON ====
def log_verdict(symbol, price, verdict):
    record = {
        "symbol": symbol,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "price": price,
        "verdict": verdict
    }
    try:
        with open("verdict_log.json", "r+") as f:
            data = json.load(f)
            data.append(record)
            f.seek(0)
            json.dump(data, f, indent=2)
    except FileNotFoundError:
        with open("verdict_log.json", "w") as f:
            json.dump([record], f, indent=2)

# ==== Main Endpoint ====
@app.get("/analyze")
def analyze(stock: str = Query(...)):
    try:
        ticker = yf.Ticker(stock.upper())
        info = ticker.info
        hist = ticker.history(period="6mo")

        if hist.empty or 'currentPrice' not in info:
            return {"error": "Invalid stock symbol or no data."}

        hist = compute_technicals(hist)
        chart = generate_chart_base64(hist)

        pe = info.get("trailingPE") if info.get("trailingPE", 0) > 0 else None
        pb = info.get("priceToBook")
        eps = info.get("trailingEps")
        book_value = info.get("bookValue")
        roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None
        roa = info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None
        roce = info.get("returnOnCapitalEmployed", 0) * 100 if info.get("returnOnCapitalEmployed") else None
        de_ratio = info.get("debtToEquity")

        raw_div = info.get("dividendYield", 0)
        div_yield = raw_div * 100 if raw_div and raw_div < 1 else 0

        mcap = info.get("marketCap", 0)
        price = info.get("currentPrice", 0)
        revenue = info.get("totalRevenue", 0)
        profit = info.get("netIncomeToCommon", 0)
        retail_flag = is_retail_stock(info)

        sentiment, headlines = fetch_news_sentiment(stock)
        if not sentiment:
            sentiment = "Neutral"
        triggers = fetch_market_triggers()

        rsi = round(hist["RSI"].iloc[-1], 2)
        ma50 = round(hist["MA50"].iloc[-1], 2)
        ma200 = round(hist["MA200"].iloc[-1], 2)
        trend = "Uptrend" if ma50 > ma200 else "Downtrend"

        score = 0
        explanations = {}

        if rsi < 30:
            score += 1; explanations["RSI"] = "Oversold (<30)"
        elif rsi > 70:
            score -= 1; explanations["RSI"] = "Overbought (>70)"
        else:
            explanations["RSI"] = "Neutral"

        if ma50 > ma200:
            score += 2; explanations["MA Trend"] = "Uptrend"
        else:
            score -= 0.5; explanations["MA Trend"] = "Downtrend"

        if "positive" in sentiment.lower():
            score += 1; explanations["Sentiment"] = "Positive"
        elif "negative" in sentiment.lower():
            score -= 1; explanations["Sentiment"] = "Negative"
        else:
            score += 0.5; explanations["Sentiment"] = "Neutral"

        if pe and pe < 15:
            score += 1; explanations["P/E"] = f"Attractive: {pe}"
        elif pe and pe > 35:
            score -= 1; explanations["P/E"] = f"Expensive: {pe}"
        else:
            explanations["P/E"] = f"Moderate: {pe}"

        if de_ratio and de_ratio < 1:
            score += 1; explanations["D/E"] = f"Healthy: {de_ratio}"
        elif de_ratio and de_ratio > 2:
            if roe and roe > 30 and "services" in info.get("industry", "").lower():
                explanations["D/E"] = f"High but acceptable for IT: {de_ratio}"
            else:
                score -= 0.5; explanations["D/E"] = f"Risky: {de_ratio}"
        else:
            explanations["D/E"] = f"Moderate: {de_ratio}"

        if roe and roe > 15:
            score += 1; explanations["ROE"] = f"Strong: {roe:.2f}%"
        elif roe and roe < 5:
            score -= 1; explanations["ROE"] = f"Weak: {roe:.2f}%"

        if roa and roa > 10:
            score += 1; explanations["ROA"] = f"Efficient: {roa:.2f}%"

        if profit and revenue and (profit / revenue) > 0.15:
            score += 1; explanations["Profit Margin"] = f"{round((profit / revenue)*100, 2)}%"

        if roce and roce > 12:
            score += 1; explanations["ROCE"] = f"Efficient: {roce:.2f}%"
        elif roce and roce < 5:
            score -= 1; explanations["ROCE"] = f"Poor: {roce:.2f}%"

        if roe and roe > 40 and mcap > 1e12 and "services" in info.get("industry", "").lower():
            if score < 4:
                score = 4
                explanations["Fundamental Override"] = "High ROE & large-cap IT company"

        if score >= 7 and roe and roe > 20 and div_yield > 2:
            suggested = "✅ Strong Buy"
            strategy_notes = "Strong EPS, low P/E, uptrend, positive sentiment"
        elif score >= 5:
            suggested = "✅ Buy"
            strategy_notes = "Good fundamentals, uptrend or oversold"
        elif score == 4:
            suggested = "📊 Long-Term Buy"
            strategy_notes = "Strong fundamentals, but downtrend or neutral macro"
        elif score == 3:
            suggested = "🟡 Hold"
            strategy_notes = "Mixed signals. Hold and monitor for clearer direction."
        elif score == 2:
            suggested = "📈 Short-Term Buy"
            strategy_notes = "Technical bounce expected (e.g., oversold RSI)"
        elif score == 1:
            suggested = "⚠️ Watch"
            strategy_notes = "Weak indicators. Wait for confirmation."
        else:
            suggested = "⛔ Avoid"
            strategy_notes = "Bad metrics or high risk (debt, downtrend, overbought, etc.)"

        entry_zones, target_zones = [], []
        stop_loss_zone = None

        if "buy" in suggested.lower() or suggested in ["⚠️ Watch", "🟡 Hold"]:
    # calculate potential levels even if we don't recommend entry

            if rsi < 60 and price > ma50:
                entry_zones.append({
                    "range": f"₹{round(ma50 * 0.98, 2)}–₹{round(ma50 * 1.02, 2)}",
                    "reason": "Near MA50 support & RSI not overbought"
                })
            entry_zones.append({
                "range": f"₹{round(price * 0.90, 2)}–₹{round(price * 0.95, 2)}",
                "reason": "Moderate dip (~5–10%)"
            })
            if ma200 and price < ma200 * 1.05:
                entry_zones.append({
                    "range": f"₹{round(ma200 * 0.95, 2)}–₹{round(ma200, 2)}",
                    "reason": "Deep support near 200‑day MA"
                })
            try:
                lowest = float(entry_zones[-1]["range"].split("–")[0].replace("₹", ""))
                stop_loss_zone = f"₹{round(lowest * 0.93, 2)} (7% below lower band)"
            except:
                stop_loss_zone = "Not defined"

            target_zones.append({
                "level": f"₹{round(ma50 * 1.15, 2)}",
                "reason": "15% above MA50 — short/mid‑term target"
            })
            target_zones.append({
                "level": f"₹{round(ma50 * 1.25, 2)}",
                "reason": "25% above MA50 if momentum resumes"
            })
        else:
            stop_loss_zone = "N/A"

        today = datetime.now().strftime("%Y-%m-%d")
        headlines_text = "\n".join("- " + h for h in headlines) if headlines else "- No headlines available"
        prompt = f"""
You are a SEBI-registered investment advisor. Analyze the following stock and prepare a final investment report.

Stock: {info.get('longName')}
Symbol: {stock.upper()}
Date: {today}
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

        gemini_report = model.generate_content(prompt).text.strip()
        verdict = f"📌 Final Verdict: **{suggested}** — {strategy_notes}"


        log_verdict(stock.upper(), price, verdict)

        return {
            "company": info.get("longName"),
            "symbol": stock.upper(),
            "ratios": {
                "P/E": pe, "P/B": pb, "EPS": eps,
                "Book Value": book_value,
                "ROE (%)": round(roe, 2) if roe else None,
                "ROA (%)": round(roa, 2) if roa else None,
                "ROCE (%)": round(roce, 2) if roce else None,
                "Debt/Equity": de_ratio,
                "Dividend Yield (%)": round(div_yield, 2),
                "Market Cap (Cr)": round(mcap / 1e7, 2),
                "Current Price": price,
                "Revenue (Cr)": round(revenue / 1e7, 2) if revenue else None,
                "Profit (Cr)": round(profit / 1e7, 2) if profit else None
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
            "target_zones": target_zones
        }

    except Exception as e:
        return {"error": str(e)}
