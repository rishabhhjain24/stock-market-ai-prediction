# step6_market_regime.py
# FIXED: keeps both string labels (readable) and integer codes (ML-ready)
import pandas as pd
from config import DEFAULT_STOCK, DATA_DIR

symbol_safe = DEFAULT_STOCK.replace(".", "_")
df = pd.read_csv(f"{DATA_DIR}/{symbol_safe}_features.csv", index_col=0, parse_dates=True)

# ── Trend regime ───────────────────────────────────────────────────────────────
df["Trend_Regime_Label"] = "Sideways"
df.loc[df["EMA_20"] > df["EMA_50"], "Trend_Regime_Label"] = "Bullish"
df.loc[df["EMA_20"] < df["EMA_50"], "Trend_Regime_Label"] = "Bearish"
df["Trend_Regime"] = (df["Trend_Regime_Label"] == "Bullish").astype(int)

# ── Volatility regime ─────────────────────────────────────────────────────────
df["BB_Width_Avg"]          = df["BB_WIDTH"].rolling(20).mean()
df["Volatility_Regime_Label"] = "Low"
df.loc[df["BB_WIDTH"] > df["BB_Width_Avg"], "Volatility_Regime_Label"] = "High"
df["Volatility_Regime"] = (df["Volatility_Regime_Label"] == "High").astype(int)

# ── Volume regime ─────────────────────────────────────────────────────────────
df["Volume_Regime_Label"] = "Normal"
df.loc[df["VOLUME_RATIO"] > 1.2, "Volume_Regime_Label"] = "High"  # 20 % above avg
df["Volume_Regime"] = (df["Volume_Regime_Label"] == "High").astype(int)

df.dropna(inplace=True)

out_path = f"{DATA_DIR}/{symbol_safe}_with_regimes.csv"
df.to_csv(out_path)
print(f"✅ STEP-6 SUCCESS: regime data saved → {out_path}")
print(df[["Trend_Regime_Label","Volatility_Regime_Label","Volume_Regime_Label"]].tail(5).to_string())   