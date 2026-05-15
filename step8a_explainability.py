# step8a_explainability.py
# FIXED: dynamic reasons based on actual indicator values, not hardcoded strings
import pandas as pd
from config import DEFAULT_STOCK, DATA_DIR, BUY_THRESHOLD

symbol_safe = DEFAULT_STOCK.replace(".", "_")
df = pd.read_csv(f"{DATA_DIR}/final_trade_decisions.csv", index_col=0, parse_dates=True)


def generate_explanation(row: pd.Series) -> str:
    """Build a human-readable explanation from indicator values."""
    if row.get("Decision") != "BUY":
        return ""

    reasons = []

    prob = row.get("UP_Probability", 0)
    reasons.append(f"Model UP-probability {prob:.2f} ≥ threshold {BUY_THRESHOLD}")

    rsi = row.get("RSI", None)
    if rsi is not None:
        if rsi < 40:
            reasons.append(f"RSI={rsi:.1f} — oversold, potential bounce")
        elif rsi < 60:
            reasons.append(f"RSI={rsi:.1f} — neutral momentum")
        else:
            reasons.append(f"RSI={rsi:.1f} — strong momentum (watch for overbought)")

    macd      = row.get("MACD", None)
    macd_sig  = row.get("MACD_SIGNAL", None)
    if macd is not None and macd_sig is not None:
        cross = "bullish crossover" if macd > macd_sig else "bearish — use caution"
        reasons.append(f"MACD={macd:.2f} vs signal={macd_sig:.2f} → {cross}")

    if row.get("Trend_Regime", 0) == 1:
        reasons.append("EMA20 > EMA50 — uptrend confirmed")

    if row.get("Volatility_Regime", 0) == 1:
        reasons.append("High volatility (BB expanding) — breakout environment")

    if row.get("Volume_Regime", 0) == 1:
        reasons.append("Volume > 20-day avg — strong market participation")

    return " | ".join(reasons)


df["Explanation"] = df.apply(generate_explanation, axis=1)

out_path = f"{DATA_DIR}/final_trade_decisions_with_explanations.csv"
df.to_csv(out_path)

buy_rows = df[df["Decision"] == "BUY"]
print(f"✅ STEP-8A SUCCESS: explanations added for {len(buy_rows)} BUY signals → {out_path}")
if len(buy_rows) > 0:
    print(buy_rows[["UP_Probability", "Decision", "Explanation"]].tail(5).to_string())