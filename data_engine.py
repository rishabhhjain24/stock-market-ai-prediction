# data_engine.py
# FIXED: MultiIndex flattening, preserves DatetimeIndex, adds ATR + Stochastic + MACD histogram
import yfinance as yf
import pandas as pd
import ta
from config import EMA_SHORT, EMA_LONG, RSI_WINDOW


def get_features(stock: str, period: str = "2y") -> pd.DataFrame | None:
    """
    Download OHLCV data and compute all technical features.
    Returns a DataFrame with DatetimeIndex, or None on failure.
    """
    try:
        raw = yf.download(stock, period=period, interval="1d",
                          auto_adjust=True, progress=False)
    except Exception as e:
        print(f"[data_engine] yfinance error: {e}")
        return None

    if raw is None or raw.empty:
        return None

    # ── Flatten MultiIndex (yfinance ≥0.2.x) ──────────────────────────────────
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    # Keep standard columns only
    needed = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in needed if c not in raw.columns]
    if missing:
        print(f"[data_engine] Missing columns: {missing}")
        return None

    df = raw[needed].copy()
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"

    for col in needed:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(inplace=True)

    if len(df) < 60:
        print("[data_engine] Not enough data (< 60 rows).")
        return None

    # ── Indicators ─────────────────────────────────────────────────────────────
    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    df["EMA_20"]       = ta.trend.ema_indicator(close, window=EMA_SHORT)
    df["EMA_50"]       = ta.trend.ema_indicator(close, window=EMA_LONG)
    df["EMA_200"]      = ta.trend.ema_indicator(close, window=200)
    df["RSI"]          = ta.momentum.rsi(close, window=RSI_WINDOW)

    macd_obj           = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)
    df["MACD"]         = macd_obj.macd()
    df["MACD_SIGNAL"]  = macd_obj.macd_signal()
    df["MACD_HIST"]    = macd_obj.macd_diff()

    bb                 = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["BB_HIGH"]      = bb.bollinger_hband()
    df["BB_MID"]       = bb.bollinger_mavg()
    df["BB_LOW"]       = bb.bollinger_lband()
    df["BB_WIDTH"]     = (df["BB_HIGH"] - df["BB_LOW"]) / df["BB_MID"]

    df["ATR"]          = ta.volatility.average_true_range(high, low, close, window=14)

    stoch              = ta.momentum.StochasticOscillator(high, low, close,
                                                          window=14, smooth_window=3)
    df["STOCH_K"]      = stoch.stoch()
    df["STOCH_D"]      = stoch.stoch_signal()

    df["VOLUME_MA20"]  = volume.rolling(20).mean()
    df["VOLUME_RATIO"] = volume / df["VOLUME_MA20"]

    # ── Regime flags ───────────────────────────────────────────────────────────
    df["Trend_Regime"]      = (df["EMA_20"] > df["EMA_50"]).astype(int)
    df["Volatility_Regime"] = (df["BB_WIDTH"] > df["BB_WIDTH"].rolling(20).mean()).astype(int)
    df["Volume_Regime"]     = (df["VOLUME_RATIO"] > 1.2).astype(int)

    df.dropna(inplace=True)
    return df