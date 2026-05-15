# controller.py
# FIXED: passes importances to llm_engine, returns rich dict for Streamlit
from data_engine import get_features
from ml_engine   import predict_next_day
from news_engine import get_news_titles
from llm_engine  import explain


def run_pipeline(stock: str) -> dict | None:
    """
    Full pipeline: fetch → indicators → ML → news → AI explanation.
    Returns a rich dict consumed by app.py, or None on failure.
    """
    # 1. Data + features
    df = get_features(stock)
    if df is None or df.empty:
        return None

    # 2. ML prediction
    try:
        prob, decision, latest, importances = predict_next_day(df)
    except Exception as e:
        print(f"[controller] ML error: {e}")
        return None

    # 3. News
    news = get_news_titles(stock)

    # 4. AI explanation
    explanation = explain(stock, prob, latest, news, importances)

    # 5. Build rich context for UI
    row = latest.iloc[0]

    return {
        # Core signal
        "decision":     decision,
        "confidence":   round(prob, 4),
        "explanation":  explanation,

        # Latest indicators (for dashboard display)
        "price":        round(float(row.get("Close", 0)), 2),
        "rsi":          round(float(row.get("RSI", 0)), 2),
        "macd":         round(float(row.get("MACD", 0)), 4),
        "macd_signal":  round(float(row.get("MACD_SIGNAL", 0)), 4),
        "ema20":        round(float(row.get("EMA_20", 0)), 2),
        "ema50":        round(float(row.get("EMA_50", 0)), 2),
        "bb_high":      round(float(row.get("BB_HIGH", 0)), 2),
        "bb_low":       round(float(row.get("BB_LOW", 0)), 2),
        "atr":          round(float(row.get("ATR", 0)), 2),
        "stoch_k":      round(float(row.get("STOCH_K", 0)), 2),
        "stoch_d":      round(float(row.get("STOCH_D", 0)), 2),

        # Regime flags
        "trend_regime":      int(row.get("Trend_Regime", 0)),
        "volatility_regime": int(row.get("Volatility_Regime", 0)),
        "volume_regime":     int(row.get("Volume_Regime", 0)),

        # Feature importances
        "importances":  importances,

        # Raw news titles
        "news":         news,

        # Full DataFrame for charts
        "df":           df,
    }