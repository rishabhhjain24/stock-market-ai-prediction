# llm_engine.py
# FIXED: passes richer context to Gemini, handles missing key gracefully,
#        returns structured analysis instead of just a paragraph
import os
from openai import OpenAI
from config import GEMINI_API_KEY


def _get_client() -> OpenAI | None:
    key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not key or key == "your_gemini_api_key_here":
        return None
    return OpenAI(
        api_key=key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


def explain(stock: str, prob: float, latest, news: list, importances: dict = None) -> str:
    """
    Generate a concise AI explanation of the trade setup.
    `latest`      — last row of the DataFrame (pd.DataFrame, 1 row)
    `news`        — list of title strings
    `importances` — dict of feature → importance score (optional)
    """
    client = _get_client()
    if client is None:
        return _rule_based_explanation(stock, prob, latest)

    # ── Build context ──────────────────────────────────────────────────────────
    row = latest.iloc[0]

    def _fmt(col, decimals=2):
        v = row.get(col, None)
        return f"{v:.{decimals}f}" if v is not None else "N/A"

    trend      = "Bullish ↑" if row.get("Trend_Regime", 0) == 1 else "Bearish ↓"
    volatility = "High"      if row.get("Volatility_Regime", 0) == 1 else "Low"
    volume     = "Above avg" if row.get("Volume_Regime", 0) == 1 else "Below avg"

    top_features = ""
    if importances:
        top3 = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]
        top_features = "Top features driving the signal: " + ", ".join(f"{k} ({v:.3f})" for k, v in top3)

    news_text = "\n".join(f"• {t}" for t in (news or [])[:5]) or "No news available."

    prompt = f"""You are an expert Indian stock market analyst. Analyze the following setup and give a concise, actionable trade brief.

Stock: {stock}
ML model UP-probability: {prob:.2f} (threshold for BUY: 0.60)

INDICATORS (latest):
  Price     : {_fmt('Close')}
  EMA 20/50 : {_fmt('EMA_20')} / {_fmt('EMA_50')}  → Trend: {trend}
  RSI (14)  : {_fmt('RSI', 1)}
  MACD      : {_fmt('MACD')}  Signal: {_fmt('MACD_SIGNAL')}  Hist: {_fmt('MACD_HIST')}
  BB High   : {_fmt('BB_HIGH')}  Low: {_fmt('BB_LOW')}
  Stoch %K  : {_fmt('STOCH_K', 1)}  %D: {_fmt('STOCH_D', 1)}
  ATR (14)  : {_fmt('ATR')}
  Volatility: {volatility}
  Volume    : {volume}
{top_features}

RECENT NEWS:
{news_text}

Write a 5-sentence professional analysis:
1. Overall setup quality (Excellent / Good / Average / Poor) and why.
2. Key bullish or bearish signals from indicators.
3. What the news sentiment implies for near-term price action.
4. Suggested entry price zone, stop-loss level, and 1–2 targets.
5. One risk to watch out for.
Keep it concise, trader-style. No generic disclaimers."""

    try:
        resp = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[llm_engine] Gemini call failed: {e}")
        return _rule_based_explanation(stock, prob, latest)


def _rule_based_explanation(stock: str, prob: float, latest) -> str:
    """Fallback when Gemini key is missing or call fails."""
    row      = latest.iloc[0]
    rsi      = row.get("RSI", 50)
    trend    = "uptrend" if row.get("Trend_Regime", 0) == 1 else "downtrend"
    macd     = row.get("MACD", 0)
    macd_sig = row.get("MACD_SIGNAL", 0)
    decision = "BUY" if prob >= 0.60 else "NO TRADE"

    rsi_note = ("oversold — potential bounce" if rsi < 35
                else "overbought — exercise caution" if rsi > 70
                else "neutral momentum zone")
    macd_note = "MACD above signal (bullish)" if macd > macd_sig else "MACD below signal (bearish)"

    return (
        f"{stock} shows a {decision} signal with {prob:.0%} UP-probability. "
        f"The stock is in a {trend} (EMA 20/50 comparison). "
        f"RSI at {rsi:.1f} — {rsi_note}. "
        f"{macd_note}. "
        f"Add your Gemini API key to .env for a detailed AI analysis."
    )