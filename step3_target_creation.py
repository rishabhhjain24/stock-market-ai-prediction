# step3_target_creation.py
# FIXED: shift(-1) only on Close, drop Next_Close before saving so
#        the model never sees the future price directly.
import pandas as pd
from config import DEFAULT_STOCK, DATA_DIR

symbol_safe = DEFAULT_STOCK.replace(".", "_")
csv_path    = f"{DATA_DIR}/{symbol_safe}_features.csv"

df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

# ── Target: will tomorrow's close be higher than today's? ─────────────────────
df["Next_Close"] = df["Close"].shift(-1)
df["Target"]     = (df["Next_Close"] > df["Close"]).astype(int)

# Drop last row (no next-day close available) and the raw future price
df.dropna(subset=["Next_Close"], inplace=True)
df.drop(columns=["Next_Close"], inplace=True)

# ── Save ───────────────────────────────────────────────────────────────────────
out_path = f"{DATA_DIR}/{symbol_safe}_ml_dataset.csv"
df.to_csv(out_path)

up_days   = df["Target"].sum()
down_days = len(df) - up_days
print(f"✅ STEP-3 SUCCESS: {len(df)} rows → {out_path}")
print(f"   UP days: {up_days} ({up_days/len(df):.1%})  |  DOWN days: {down_days} ({down_days/len(df):.1%})")
print(df[["Close", "Target"]].tail(5))