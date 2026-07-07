"""Side-by-side stock comparison."""

from fastapi import APIRouter, Query

from config import get_gemini_api_key
from services import gemini_service
from services.analysis_service import run_analysis

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
def compare_stocks(
    a: str = Query(..., description="Symbol A e.g. TCS.NS"),
    b: str = Query(..., description="Symbol B e.g. INFY.NS"),
):
    sa = a.strip().upper()
    sb = b.strip().upper()
    ra = run_analysis(sa)
    rb = run_analysis(sb)
    if isinstance(ra, dict) and ra.get("error"):
        return {"error": ra["error"], "a": None, "b": rb if not (isinstance(rb, dict) and rb.get("error")) else None}
    if isinstance(rb, dict) and rb.get("error"):
        return {"error": rb["error"], "a": ra, "b": None}
    ai = None
    if get_gemini_api_key():
        try:
            prompt = f"""Compare two Indian equities for a research reader (not financial advice):
A {sa}: verdict={ra.get('strategy_type')}, signal_score={ra.get('signal_score')}, sentiment snippet={(ra.get('news_sentiment') or '')[:120]}
B {sb}: verdict={rb.get('strategy_type')}, signal_score={rb.get('signal_score')}, sentiment snippet={(rb.get('news_sentiment') or '')[:120]}
Give 4 bullets: relative valuation tone, technical posture, sentiment, key risk."""
            ai = gemini_service.generate_text(prompt, context="compare_stocks").strip()
        except Exception:
            ai = None
    return {"a": ra, "b": rb, "ai_comparison": ai}
