from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import google.generativeai as genai
import io, base64
import matplotlib.pyplot as plt
from datetime import datetime
today = datetime.now().strftime("%B %d, %Y")

# Gemini Setup
genai.configure(api_key="AIzaSyDrOp4KNiFs98AKRnjemD-EqsigetuXuco")  # replace with env var in prod
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_chart_base64(ticker):
    hist = ticker.history(period="6mo")
    if hist.empty:
        return None
    plt.figure(figsize=(10, 4))
    plt.plot(hist.index, hist["Close"], label="Close Price", color="cyan")
    plt.title(f"{ticker.info.get('shortName', '')} Price Chart (6M)")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()  # very important
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

@app.get("/analyze")
def analyze(stock: str = Query(...)):
    try:
        ticker = yf.Ticker(stock.upper())
        info = ticker.info
        hist = ticker.history(period="6mo")

        if 'currentPrice' not in info:
            return {"error": "Invalid stock symbol or data unavailable."}

        # Fundamental Ratios
        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None
        roa = info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None
        de_ratio = info.get("debtToEquity")
        div_yield = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
        mcap = info.get("marketCap", 0)
        price = info.get("currentPrice", 0)

        # Chart (base64)
        chart = generate_chart_base64(ticker)

        # 🔮 Gemini Prompt
        # 🔮 Gemini Prompt (UPDATED: removed "Fundamental Analysis Table")
        prompt = f"""
Generate a professional SEBI-style investment advisory report for the following Indian company, based on the given data.

Company: {info.get('longName')}
Ticker: {stock.upper()}
Sector: {info.get('sector', 'Finance')}
Report Date: {today} 
📊 Key Metrics:
- P/E Ratio: {pe}
- ROE: {roe}%
- ROA: {roa}%
- Debt to Equity: {de_ratio}
- Dividend Yield: {div_yield}%
- Market Cap: ₹{mcap/1e7:.2f} Cr
- Current Price: ₹{price}

📉 Technical Overview (6-month chart data provided):
Analyze price trend, potential support/resistance levels, and overall momentum.

🎯 Structure the report in this exact format:

1. **Company Overview**
2. **Technical Chart Analysis Summary**
3. **Pros and Cons**
4. **Investor Type Strategy**
    Growth Investor: [✅ Buy / ⚠️ Wait / ❌ Avoid] + short explanation  
    Value Investor: [✅ Buy / ⚠️ Wait / ❌ Avoid] + short explanation  
    Short-Term Trader: [✅ Buy / ⚠️ Wait / ❌ Avoid] + short explanation  
5. **🎯 Suggested Strategy**  
    - Ideal accumulation zone  
    - Profit booking levels if any  
    - Cautions or sector-specific risks  
6. **📌 Final Verdict**  
    Format like:  
    📌 Final Verdict: STRONG LONG-TERM BUY (with caution on valuation)  
    Brief justification (1–2 lines)

⚠️ Avoid markdown, emojis, or headings other than mentioned.
Keep it factual, clean, and very readable. Include realistic, data-backed suggestions.
"""



        response = model.generate_content(prompt)
        report = response.text.strip()

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
            "full_report": report
        }

    except Exception as e:
        return {"error": f"❌ Error: {str(e)}"}