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

load_dotenv()
today = datetime.now().strftime("%B %d, %Y")

GEMINI_API_KEY = "AIzaSyDrOp4KNiFs98AKRnjemD-EqsigetuXuco"
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



def fetch_market_triggers():
    try:
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        data = soup.find_all("div", class_="FL PR5")

        fii = data[0].get_text(strip=True) if len(data) > 0 else "FII data unavailable"
        dii = data[1].get_text(strip=True) if len(data) > 1 else "DII data unavailable"
        return f"FII: {fii}, DII: {dii}"

    except Exception as e:
        return "Market triggers unavailable"


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

        # ==== Financials ====
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

        # ==== External Data ====
        sentiment, headlines = fetch_news_sentiment(stock)
        triggers = fetch_market_triggers()

        # ==== Technicals ====
        rsi = round(hist["RSI"].iloc[-1], 2)
        ma50 = round(hist["MA50"].iloc[-1], 2)
        ma200 = round(hist["MA200"].iloc[-1], 2)
        trend = "Uptrend" if ma50 > ma200 else "Downtrend"

        # ==== Scoring Logic ====
        score = 0
        explanations = {}

        if rsi < 30:
            score += 1; explanations["RSI"] = "Oversold (<30)"
        elif rsi > 70:
            score -= 1; explanations["RSI"] = "Overbought (>70)"
        else:
            explanations["RSI"] = "Neutral"

        if ma50 > ma200:
            score += 2; explanations["MA Trend"] = "Uptrend (MA50 > MA200)"
        else:
            explanations["MA Trend"] = "Downtrend (MA50 <= MA200)"

        if "positive" in sentiment.lower():
            score += 1; explanations["Sentiment"] = "Positive"
        elif "negative" in sentiment.lower():
            score -= 1; explanations["Sentiment"] = "Negative"
        else:
            explanations["Sentiment"] = "Neutral"

        if pe and pe < 15:
            score += 1; explanations["P/E"] = f"Attractive: {pe}"
        elif pe and pe > 35:
            score -= 1; explanations["P/E"] = f"Expensive: {pe}"
        else:
            explanations["P/E"] = f"Moderate: {pe}"

        if de_ratio and de_ratio < 1:
            score += 1; explanations["D/E"] = f"Healthy: {de_ratio}"
        elif de_ratio and de_ratio > 2:
            score -= 1; explanations["D/E"] = f"Risky: {de_ratio}"
        else:
            explanations["D/E"] = f"Moderate: {de_ratio}"

        # ==== Verdict Logic ====
        if score >= 4:
            suggested = "Buy"
        elif score <= 1:
            suggested = "Avoid"
        else:
            suggested = "Sell"  # Replace 'Watch' with actionable 'Sell'

        # ==== GEMINI Prompt ====
        headlines_text = "\n".join("- " + h for h in headlines) if headlines else "- No headlines available"
        prompt = f"""
You are a SEBI-registered investment advisor. Analyze the following stock and prepare a final investment report.

Stock: {info.get('longName')}
Symbol: {stock.upper()}
Date: {today}
Current Price: ₹{price}
Market Cap: ₹{mcap/1e7:.2f} Cr
Retail Stock: {"Yes" if retail_flag else "No"}

Financials:
- P/E: {pe}, P/B: {pb}, EPS: {eps}, Book Value: ₹{book_value}
- ROE: {roe}%, ROA: {roa}%, ROCE: {roce}%
- Debt/Equity: {de_ratio}, Dividend Yield: {div_yield:.2f}%
- Revenue: ₹{revenue/1e7:.2f} Cr, Profit: ₹{profit/1e7:.2f} Cr

Technical:
- RSI: {rsi}, MA50: {ma50}, MA200: {ma200}, Trend: {trend}

News Sentiment: {sentiment}
Market Activity: {triggers}
Headlines:\n{headlines_text}

🎯 INTERNAL SYSTEM VERDICT: **{suggested}**

📌 Final Verdict (must be same): **{suggested}** — Explain in one line why.
Give clear entry or exit strategy and specific investor recommendation for Growth, Value, Trader.

Strict FORMAT:
1. Company Overview
2. Technical Summary
3. Pros & Cons
4. Strategy
5. Entry/Exit
6. 📌 Final Verdict: **{suggested}** (1-line reason only)
"""

        gemini_report = model.generate_content(prompt).text.strip()
        verdict_line = next((line for line in gemini_report.split("\n") if "📌 Final Verdict" in line), f"📌 Final Verdict: {suggested}")
        verdict = verdict_line

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
            "verdict": verdict
        }

    except Exception as e:
        return {"error": str(e)}
