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
    return hist

# ==== News + Market Triggers ====
def fetch_news_sentiment(stock_name):
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={stock_name}&country=in&language=en"
        res = requests.get(url)
        data = res.json()
        headlines = [article["title"] for article in data.get("results", []) if article.get("title")][:5]
        if not headlines:
            return "No significant news found.", []

        joined = "\n- ".join(headlines)
        prompt = f"""
You are a financial news analyst. Determine the overall sentiment (positive/negative/neutral) for the following recent headlines about {stock_name}:

- {joined}

Give a one-word sentiment summary at the start and a short explanation why.
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
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        data = soup.find_all("div", class_="FL PR5")
        fii = data[0].get_text(strip=True)
        dii = data[1].get_text(strip=True)
        return f"FII: {fii}, DII: {dii}"
    except:
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

        # Financial ratios
        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None
        roa = info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None
        de_ratio = info.get("debtToEquity")
        div_yield = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
        mcap = info.get("marketCap", 0)
        price = info.get("currentPrice", 0)
        retail_flag = is_retail_stock(info)

        # External inputs
        sentiment, headlines = fetch_news_sentiment(stock)
        triggers = fetch_market_triggers()

        # Gemini Prompt
        prompt = f"""
You are a SEBI-registered investment advisor. Write a detailed investment report for:

Company: {info.get('longName')}
Symbol: {stock.upper()}
Sector: {info.get('sector')}
Price: ₹{price}
Date: {today}
Market Cap: ₹{mcap/1e7:.2f} Cr
P/E: {pe}, ROE: {roe}%, ROA: {roa}%, Debt/Equity: {de_ratio}, Dividend Yield: {div_yield}%
Is Retail-Focused Stock: {"Yes" if retail_flag else "No"}

Recent News Headlines:\n{chr(10).join('- ' + h for h in headlines)}
News Sentiment: {sentiment}
Market Activity: {triggers}
RSI: {round(hist['RSI'].iloc[-1], 2)} | MA50: {round(hist['MA50'].iloc[-1], 2)} | MA200: {round(hist['MA200'].iloc[-1], 2)}

Respond in this format:
1. *Company Overview*
2. *Technical Summary* (RSI, MA50/200, chart trend)
3. *Pros and Cons*
4. *Investor Strategy*
    - Growth: ✅/⚠️/❌
    - Value: ✅/⚠️/❌
    - Trader: ✅/⚠️/❌
5. *Suggested Entry/Exit*
6. *📌 Final Verdict:* [Buy / Watch / Avoid] + 1-line reason
"""

        gemini_report = model.generate_content(prompt).text.strip()
        verdict_line = [line for line in gemini_report.split("\n") if "📌 Final Verdict" in line]
        verdict = verdict_line[0] if verdict_line else "Verdict missing"

        log_verdict(stock.upper(), price, verdict)

        return {
            "company": info.get("longName"),
            "symbol": stock.upper(),
            "ratios": {
                "P/E": pe,
                "ROE (%)": round(roe, 2) if roe else None,
                "ROA (%)": round(roa, 2) if roa else None,
                "Debt/Equity": de_ratio,
                "Dividend Yield (%)": round(div_yield, 2),
                "Market Cap (Cr)": round(mcap / 1e7, 2),
                "Current Price": price,
                "P/B": info.get("priceToBook"),
                "Revenue (Cr)": round(info.get("totalRevenue", 0) / 1e7, 2) if info.get("totalRevenue") else None,
                "Profit (Cr)": round(info.get("netIncomeToCommon", 0) / 1e7, 2) if info.get("netIncomeToCommon") else None,
            },
            "chart_base64": chart,
            "news_sentiment": sentiment,
            "news_headlines": headlines,
            "market_triggers": triggers,
            "retail_stock": retail_flag,
            "full_report": gemini_report,
            "verdict": verdict
        }

    except Exception as e:
        return {"error": str(e)}
