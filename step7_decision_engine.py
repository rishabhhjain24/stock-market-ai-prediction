# step7_decision_engine.py
# FIXED: safe index alignment, BUY condition uses integer regime columns,
#        saves full context columns for downstream steps
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from config import DEFAULT_STOCK, DATA_DIR, TRAIN_RATIO, BUY_THRESHOLD

symbol_safe = DEFAULT_STOCK.replace(".", "_")

df_ml     = pd.read_csv(f"{DATA_DIR}/{symbol_safe}_ml_dataset.csv",    index_col=0, parse_dates=True)
df_regime = pd.read_csv(f"{DATA_DIR}/{symbol_safe}_with_regimes.csv",  index_col=0, parse_dates=True)

# ── Merge on shared dates ──────────────────────────────────────────────────────
regime_cols = ["Trend_Regime", "Volatility_Regime", "Volume_Regime"]
df = df_ml.join(df_regime[regime_cols], how="inner")
df.dropna(inplace=True)

# ── Features / target ─────────────────────────────────────────────────────────
DROP_COLS = ["Target", "Open", "High", "Low", "Close", "Volume"]
X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
y = df["Target"]

split   = int(len(df) * TRAIN_RATIO)
X_train = X.iloc[:split]; X_test = X.iloc[split:]
y_train = y.iloc[:split]; y_test = y.iloc[split:]

scaler    = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

model = LogisticRegression(max_iter=1000, C=0.1)
model.fit(X_train_s, y_train)
probs = model.predict_proba(X_test_s)[:, 1]

# ── Decision logic ─────────────────────────────────────────────────────────────
results                   = X_test.copy()
results["Actual"]         = y_test.values
results["UP_Probability"] = probs
results["Decision"]       = "NO_TRADE"

# BUY only when model is confident AND market regime is favourable
buy_mask = (
    (results["UP_Probability"]  >= BUY_THRESHOLD) &
    (results["Trend_Regime"]    == 1) &   # Bullish trend
    (results["Volatility_Regime"]== 1) &  # High volatility (breakout env)
    (results["Volume_Regime"]   == 1)     # Above-average volume
)
results.loc[buy_mask, "Decision"] = "BUY"

out_path = f"{DATA_DIR}/final_trade_decisions.csv"
results.to_csv(out_path)

buy_n = (results["Decision"] == "BUY").sum()
print(f"✅ STEP-7 SUCCESS: {len(results)} decisions → {out_path}")
print(f"   BUY: {buy_n}  |  NO_TRADE: {len(results)-buy_n}")
print(results[["UP_Probability", "Decision"]].tail(10).to_string())