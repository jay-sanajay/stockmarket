"""Service for AI-driven stock recommendations grouped by time horizons."""

import json
import logging
import re
from typing import Any, Dict, List

import yfinance as yf

from services.gemini_service import generate_text

logger = logging.getLogger(__name__)


def get_market_context() -> str:
    """Fetch recent data for top Indian stocks to provide context."""
    symbols = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
        "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LT.NS", "BAJFINANCE.NS",
        "AXISBANK.NS", "KOTAKBANK.NS", "TATAMOTORS.NS", "M&M.NS", "SUNPHARMA.NS",
        "TITAN.NS", "WIPRO.NS", "HCLTECH.NS", "NTPC.NS", "POWERGRID.NS",
        "COALINDIA.NS", "ONGC.NS", "BPCL.NS", "TATAPOWER.NS", "VEDL.NS",
        "HINDALCO.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "ADANIPORTS.NS", "CIPLA.NS",
    ]
    context_data = []
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            try:
                hist = tickers.tickers[sym].history(period="5d")
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    pct = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100
                    context_data.append(
                        f"{sym}: ₹{latest['Close']:.2f}, 1D {pct:+.2f}%, Vol {int(latest['Volume'])}"
                    )
            except Exception:
                pass
    except Exception as e:
        logger.warning("Failed to fetch market context: %s", e)
    return "\n".join(context_data)


async def get_ai_recommendations() -> List[Dict[str, Any]]:
    """Query Gemini for multi-horizon stock recommendations."""
    market_context = get_market_context()

    prompt = f"""You are an expert SEBI-registered financial analyst and quantitative stock-screening engine.
Analyze current Indian stock market data and provide high-potential stock recommendations.

CURRENT MARKET SNAPSHOT (NSE):
{market_context}

INSTRUCTIONS — provide recommendations for ALL categories below:

CATEGORY 1 — TIME-HORIZON PICKS (20%+ return target)
For EACH of these 7 horizons give exactly 3 stocks:
  "1 Month"  — aggressive momentum / breakout plays
  "2 Months" — short-term swing trades with strong catalysts
  "3 Months" — quarterly earnings plays, sector rotation picks
  "4 Months" — medium-term growth with improving fundamentals
  "5 Months" — pre-result rally candidates, sector leaders
  "6 Months" — half-year compounders with earnings visibility
  "12 Months"— long-term wealth creators, robust fundamentals

CATEGORY 2 — 50%+ RETURN MULTI-BAGGERS (12-month horizon)
Give exactly 5 stocks with 50%+ upside potential.
Turnaround stories, deep value, high-growth small/mid caps.
Set Time_Horizon = "50% Return Picks"

CATEGORY 3 — DEEP VALUE / ALL-TIME LOW BUYS
Give exactly 5 stocks near 52-week or all-time lows that are:
  - Low P/E, high ROE, low debt, strong management
  - Temporarily beaten down with likely reversal
Set Time_Horizon = "Deep Value (Near All-Time Low)"

TOTAL: exactly 31 stock objects.

OUTPUT FORMAT — return ONLY a raw JSON array (no markdown, no ```):
[
  {{
    "Time_Horizon": "...",
    "Ticker": "SYMBOL.NS",
    "Company_Name": "Full Name",
    "Current_Price": 1234.56,
    "Target_Price": 1500.00,
    "Stop_Loss": 1100.00,
    "Core_Catalysts": ["reason 1", "reason 2", "reason 3"],
    "Risk_Profile": "Low|Medium|High",
    "Expected_Return_Pct": 22.5
  }}
]

RULES:
- Use real current NSE prices. Do NOT fabricate prices.
- Do NOT repeat the same stock across categories.
- For Deep Value picks explain WHY it is cheap and why it is a buy.
- No guaranteed language — use probabilistic framing.
"""

    try:
        response_text = generate_text(prompt, context="ai_recommendations")
    except Exception as e:
        logger.error("Gemini call failed for AI recommendations: %s", e)
        return _get_fallback_recommendations()

    # Strip markdown fences
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        match = re.search(r"\[\s*\{.*\}\s*\]", cleaned, re.DOTALL)
        json_str = match.group(0) if match else cleaned.strip()
        data = json.loads(json_str)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON array")
        return data
    except Exception as e:
        logger.error("Failed to parse AI recommendations: %s\nRaw: %.500s", e, response_text)
        return _get_fallback_recommendations()


def _get_fallback_recommendations() -> List[Dict[str, Any]]:
    """Reliable fallback when Gemini is unavailable."""
    return [
        {"Time_Horizon":"1 Month","Ticker":"SBIN.NS","Company_Name":"State Bank of India","Current_Price":820.0,"Target_Price":985.0,"Stop_Loss":770.0,"Core_Catalysts":["Strong NII growth","Improving asset quality","Govt capex push"],"Risk_Profile":"Medium","Expected_Return_Pct":20.1},
        {"Time_Horizon":"1 Month","Ticker":"ITC.NS","Company_Name":"ITC Limited","Current_Price":440.0,"Target_Price":530.0,"Stop_Loss":410.0,"Core_Catalysts":["FMCG margin expansion","Hotel business demerger value unlock","Strong cash flows"],"Risk_Profile":"Low","Expected_Return_Pct":20.5},
        {"Time_Horizon":"1 Month","Ticker":"NTPC.NS","Company_Name":"NTPC Limited","Current_Price":350.0,"Target_Price":420.0,"Stop_Loss":325.0,"Core_Catalysts":["Renewable capacity addition","Strong regulated returns","Government backing"],"Risk_Profile":"Low","Expected_Return_Pct":20.0},
        {"Time_Horizon":"2 Months","Ticker":"TATAMOTORS.NS","Company_Name":"Tata Motors","Current_Price":950.0,"Target_Price":1140.0,"Stop_Loss":880.0,"Core_Catalysts":["JLR profitability improving","EV portfolio expansion","Strong domestic demand"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"2 Months","Ticker":"BAJFINANCE.NS","Company_Name":"Bajaj Finance","Current_Price":8500.0,"Target_Price":10200.0,"Stop_Loss":7900.0,"Core_Catalysts":["AUM growth 25%+","Digital lending push","Rural expansion"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"2 Months","Ticker":"AXISBANK.NS","Company_Name":"Axis Bank","Current_Price":1150.0,"Target_Price":1380.0,"Stop_Loss":1070.0,"Core_Catalysts":["Credit growth acceleration","Asset quality improving","Citibank integration gains"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"3 Months","Ticker":"ICICIBANK.NS","Company_Name":"ICICI Bank","Current_Price":1324.0,"Target_Price":1590.0,"Stop_Loss":1240.0,"Core_Catalysts":["Robust credit growth","Best-in-class asset quality","Valuation re-rating"],"Risk_Profile":"Low","Expected_Return_Pct":20.1},
        {"Time_Horizon":"3 Months","Ticker":"HCLTECH.NS","Company_Name":"HCL Technologies","Current_Price":1650.0,"Target_Price":1980.0,"Stop_Loss":1530.0,"Core_Catalysts":["Strong deal pipeline","AI services adoption","Margin improvement"],"Risk_Profile":"Low","Expected_Return_Pct":20.0},
        {"Time_Horizon":"3 Months","Ticker":"SUNPHARMA.NS","Company_Name":"Sun Pharmaceutical","Current_Price":1520.0,"Target_Price":1825.0,"Stop_Loss":1410.0,"Core_Catalysts":["Specialty portfolio growth","US generics recovery","Strong EBITDA margins"],"Risk_Profile":"Medium","Expected_Return_Pct":20.1},
        {"Time_Horizon":"4 Months","Ticker":"BHARTIARTL.NS","Company_Name":"Bharti Airtel","Current_Price":1650.0,"Target_Price":1980.0,"Stop_Loss":1520.0,"Core_Catalysts":["ARPU growth trajectory","5G monetization","Africa expansion"],"Risk_Profile":"Low","Expected_Return_Pct":20.0},
        {"Time_Horizon":"4 Months","Ticker":"CIPLA.NS","Company_Name":"Cipla Limited","Current_Price":1480.0,"Target_Price":1776.0,"Stop_Loss":1370.0,"Core_Catalysts":["US peptide launches","Respiratory portfolio growth","Margin tailwinds"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"4 Months","Ticker":"TITAN.NS","Company_Name":"Titan Company","Current_Price":3200.0,"Target_Price":3840.0,"Stop_Loss":2950.0,"Core_Catalysts":["Jewellery segment growth","Store expansion","Wedding season demand"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"5 Months","Ticker":"LT.NS","Company_Name":"Larsen & Toubro","Current_Price":3500.0,"Target_Price":4200.0,"Stop_Loss":3250.0,"Core_Catalysts":["Record order book","Infrastructure capex cycle","Margin improvement"],"Risk_Profile":"Low","Expected_Return_Pct":20.0},
        {"Time_Horizon":"5 Months","Ticker":"WIPRO.NS","Company_Name":"Wipro Limited","Current_Price":450.0,"Target_Price":540.0,"Stop_Loss":415.0,"Core_Catalysts":["Turnaround strategy bearing fruit","Large deal wins","AI-led efficiency gains"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"5 Months","Ticker":"KOTAKBANK.NS","Company_Name":"Kotak Mahindra Bank","Current_Price":1800.0,"Target_Price":2160.0,"Stop_Loss":1670.0,"Core_Catalysts":["Digital banking leadership","Deposit growth improving","Wealth management growth"],"Risk_Profile":"Low","Expected_Return_Pct":20.0},
        {"Time_Horizon":"6 Months","Ticker":"HDFCBANK.NS","Company_Name":"HDFC Bank","Current_Price":1600.0,"Target_Price":1950.0,"Stop_Loss":1450.0,"Core_Catalysts":["Merger synergies materializing","Credit growth accelerating","Valuation comfort"],"Risk_Profile":"Low","Expected_Return_Pct":21.9},
        {"Time_Horizon":"6 Months","Ticker":"M&M.NS","Company_Name":"Mahindra & Mahindra","Current_Price":2998.0,"Target_Price":3600.0,"Stop_Loss":2760.0,"Core_Catalysts":["SUV market dominance","Farm equipment recovery","EV tractor opportunity"],"Risk_Profile":"Medium","Expected_Return_Pct":20.1},
        {"Time_Horizon":"6 Months","Ticker":"ADANIPORTS.NS","Company_Name":"Adani Ports & SEZ","Current_Price":1350.0,"Target_Price":1620.0,"Stop_Loss":1240.0,"Core_Catalysts":["Cargo volume growth","Port acquisition synergies","Logistics integration"],"Risk_Profile":"Medium","Expected_Return_Pct":20.0},
        {"Time_Horizon":"12 Months","Ticker":"RELIANCE.NS","Company_Name":"Reliance Industries","Current_Price":2900.0,"Target_Price":3600.0,"Stop_Loss":2650.0,"Core_Catalysts":["Jio monetization","Retail expansion","New energy investments"],"Risk_Profile":"Medium","Expected_Return_Pct":24.1},
        {"Time_Horizon":"12 Months","Ticker":"TCS.NS","Company_Name":"Tata Consultancy Services","Current_Price":4000.0,"Target_Price":4900.0,"Stop_Loss":3700.0,"Core_Catalysts":["AI-driven deal wins","Margin resilience","Strong dividend yield"],"Risk_Profile":"Low","Expected_Return_Pct":22.5},
        {"Time_Horizon":"12 Months","Ticker":"INFY.NS","Company_Name":"Infosys Limited","Current_Price":1550.0,"Target_Price":1900.0,"Stop_Loss":1420.0,"Core_Catalysts":["Generative AI consulting boom","Large deal momentum","Margin expansion to 22%+"],"Risk_Profile":"Low","Expected_Return_Pct":22.6},
        {"Time_Horizon":"50% Return Picks","Ticker":"TATAPOWER.NS","Company_Name":"Tata Power","Current_Price":420.0,"Target_Price":630.0,"Stop_Loss":370.0,"Core_Catalysts":["Renewable capacity 3x in 3 yrs","EV charging network leader","Regulated returns improving"],"Risk_Profile":"High","Expected_Return_Pct":50.0},
        {"Time_Horizon":"50% Return Picks","Ticker":"VEDL.NS","Company_Name":"Vedanta Limited","Current_Price":440.0,"Target_Price":660.0,"Stop_Loss":380.0,"Core_Catalysts":["Commodity super-cycle beneficiary","Semiconductor fab plans","High dividend yield 7%+"],"Risk_Profile":"High","Expected_Return_Pct":50.0},
        {"Time_Horizon":"50% Return Picks","Ticker":"HINDALCO.NS","Company_Name":"Hindalco Industries","Current_Price":620.0,"Target_Price":930.0,"Stop_Loss":550.0,"Core_Catalysts":["Novelis IPO value unlock","Aluminium price recovery","Copper business growth"],"Risk_Profile":"High","Expected_Return_Pct":50.0},
        {"Time_Horizon":"50% Return Picks","Ticker":"JSWSTEEL.NS","Company_Name":"JSW Steel","Current_Price":850.0,"Target_Price":1275.0,"Stop_Loss":750.0,"Core_Catalysts":["Capacity expansion to 37 MTPA","Infrastructure-led steel demand","Cost optimization"],"Risk_Profile":"High","Expected_Return_Pct":50.0},
        {"Time_Horizon":"50% Return Picks","Ticker":"TATASTEEL.NS","Company_Name":"Tata Steel","Current_Price":145.0,"Target_Price":218.0,"Stop_Loss":125.0,"Core_Catalysts":["European restructuring savings","India volume growth","De-leveraging balance sheet"],"Risk_Profile":"High","Expected_Return_Pct":50.3},
        {"Time_Horizon":"Deep Value (Near All-Time Low)","Ticker":"COALINDIA.NS","Company_Name":"Coal India Limited","Current_Price":390.0,"Target_Price":520.0,"Stop_Loss":350.0,"Core_Catalysts":["Undervalued at 6x P/E","Highest Nifty dividend yield","Volume growth resuming"],"Risk_Profile":"Low","Expected_Return_Pct":33.3},
        {"Time_Horizon":"Deep Value (Near All-Time Low)","Ticker":"ONGC.NS","Company_Name":"Oil & Natural Gas Corp","Current_Price":250.0,"Target_Price":340.0,"Stop_Loss":225.0,"Core_Catalysts":["Trading at 7x P/E","Gas price reform benefits","Strong dividend support"],"Risk_Profile":"Medium","Expected_Return_Pct":36.0},
        {"Time_Horizon":"Deep Value (Near All-Time Low)","Ticker":"BPCL.NS","Company_Name":"Bharat Petroleum","Current_Price":310.0,"Target_Price":420.0,"Stop_Loss":280.0,"Core_Catalysts":["P/E below 5x","Disinvestment re-rating potential","Refining margins recovering"],"Risk_Profile":"Medium","Expected_Return_Pct":35.5},
        {"Time_Horizon":"Deep Value (Near All-Time Low)","Ticker":"IOC.NS","Company_Name":"Indian Oil Corporation","Current_Price":140.0,"Target_Price":190.0,"Stop_Loss":125.0,"Core_Catalysts":["Trading at 4x P/E","Dividend yield 8%+","Petrochemical expansion"],"Risk_Profile":"Medium","Expected_Return_Pct":35.7},
        {"Time_Horizon":"Deep Value (Near All-Time Low)","Ticker":"POWERGRID.NS","Company_Name":"Power Grid Corp of India","Current_Price":310.0,"Target_Price":400.0,"Stop_Loss":280.0,"Core_Catalysts":["Stable regulated returns","Green energy corridor capex","Consistent dividend payer"],"Risk_Profile":"Low","Expected_Return_Pct":29.0},
    ]
