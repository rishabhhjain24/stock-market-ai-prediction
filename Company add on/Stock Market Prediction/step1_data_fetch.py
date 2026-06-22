# step1_data_fetch.py
# FIXED: proper MultiIndex column flattening, date preservation, error handling
import os
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from config import DEFAULT_STOCK, START_DATE, DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)

# ── 1. Choose stock ────────────────────────────────────────────────────────────
stock_symbol = DEFAULT_STOCK   # change here or pass via CLI

# ── 2. Download ────────────────────────────────────────────────────────────────
print(f"Downloading {stock_symbol} from {START_DATE} ...")
df_raw = yf.download(
    stock_symbol,
    start=START_DATE,
    interval="1d",
    auto_adjust=True,   # adjusts for splits & dividends
    progress=False,
)

if df_raw.empty:
    raise ValueError(f"No data returned for {stock_symbol}. Check the symbol.")

# ── 3. FIXED: flatten MultiIndex columns (yfinance ≥ 0.2.x returns MultiIndex)
if isinstance(df_raw.columns, pd.MultiIndex):
    df_raw.columns = df_raw.columns.get_level_values(0)

# ── 4. Keep Date as a proper DatetimeIndex ─────────────────────────────────────
df_raw.index.name = "Date"
df_raw.index = pd.to_datetime(df_raw.index)

# ── 5. Keep only OHLCV ─────────────────────────────────────────────────────────
df = df_raw[["Open", "High", "Low", "Close", "Volume"]].copy()
df.dropna(inplace=True)

# ── 6. Save ────────────────────────────────────────────────────────────────────
out_path = f"{DATA_DIR}/{stock_symbol.replace('.', '_')}_data.csv"
df.to_csv(out_path)

print(f"✅ STEP-1 SUCCESS: {len(df)} rows saved → {out_path}")
print(df.tail(3))

# ── 7. Candlestick chart ───────────────────────────────────────────────────────
try:
    mpf.plot(
        df.tail(120),
        type="candle",
        volume=True,
        title=f"{stock_symbol} — Last 120 days",
        style="yahoo",
    )
except Exception as e:
    print(f"Chart skipped (headless env): {e}")