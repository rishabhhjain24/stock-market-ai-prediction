# step2_indicators.py
# FIXED: robust CSV loading, added ATR + Stochastic + Volume MA,
#        MACD histogram, no silent NaN propagation
import os
import pandas as pd
import ta
import mplfinance as mpf
from config import DEFAULT_STOCK, DATA_DIR

# ── Load ───────────────────────────────────────────────────────────────────────
symbol_safe = DEFAULT_STOCK.replace(".", "_")
csv_path    = f"{DATA_DIR}/{symbol_safe}_data.csv"

df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
df.index.name = "Date"

# Force numeric (guards against stray header rows in old CSVs)
for col in ["Open", "High", "Low", "Close", "Volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df.dropna(inplace=True)

# ── Technical indicators ───────────────────────────────────────────────────────
close  = df["Close"]
high   = df["High"]
low    = df["Low"]
volume = df["Volume"]

# Trend
df["EMA_20"]      = ta.trend.ema_indicator(close, window=20)
df["EMA_50"]      = ta.trend.ema_indicator(close, window=50)
df["EMA_200"]     = ta.trend.ema_indicator(close, window=200)

# Momentum
df["RSI"]         = ta.momentum.rsi(close, window=14)
stoch             = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
df["STOCH_K"]     = stoch.stoch()
df["STOCH_D"]     = stoch.stoch_signal()

# MACD
macd_obj          = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)
df["MACD"]        = macd_obj.macd()
df["MACD_SIGNAL"] = macd_obj.macd_signal()
df["MACD_HIST"]   = macd_obj.macd_diff()

# Volatility
bb                = ta.volatility.BollingerBands(close, window=20, window_dev=2)
df["BB_HIGH"]     = bb.bollinger_hband()
df["BB_MID"]      = bb.bollinger_mavg()
df["BB_LOW"]      = bb.bollinger_lband()
df["BB_WIDTH"]    = (df["BB_HIGH"] - df["BB_LOW"]) / df["BB_MID"]  # normalised width
df["ATR"]         = ta.volatility.average_true_range(high, low, close, window=14)

# Volume
df["VOLUME_MA20"] = volume.rolling(20).mean()
df["VOLUME_RATIO"]= volume / df["VOLUME_MA20"]   # >1 = above-average volume

df.dropna(inplace=True)

# ── Save ───────────────────────────────────────────────────────────────────────
out_path = f"{DATA_DIR}/{symbol_safe}_features.csv"
df.to_csv(out_path)
print(f"✅ STEP-2 SUCCESS: {len(df)} rows, {len(df.columns)} features → {out_path}")
print(df[["Close", "EMA_20", "EMA_50", "RSI", "MACD", "ATR"]].tail(3))

# ── Chart ──────────────────────────────────────────────────────────────────────
try:
    apds = [
        mpf.make_addplot(df["EMA_20"].tail(120),  color="blue",   label="EMA20"),
        mpf.make_addplot(df["EMA_50"].tail(120),  color="orange", label="EMA50"),
        mpf.make_addplot(df["RSI"].tail(120),     panel=1, ylabel="RSI",  color="purple"),
        mpf.make_addplot(df["MACD"].tail(120),    panel=2, ylabel="MACD", color="green"),
        mpf.make_addplot(df["MACD_SIGNAL"].tail(120), panel=2, color="red"),
    ]
    mpf.plot(
        df.tail(120),
        type="candle",
        volume=True,
        addplot=apds,
        panel_ratios=(4, 1, 1),
        title=f"{DEFAULT_STOCK} — Indicators",
        style="yahoo",
    )
except Exception as e:
    print(f"Chart skipped: {e}")