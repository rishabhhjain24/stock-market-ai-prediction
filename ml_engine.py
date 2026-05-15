# ml_engine.py
# FIXED: time-based split (no leakage), scaler fit on train only,
#        returns probability + decision + latest row + feature importances
import pickle, os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from config import TRAIN_RATIO, BUY_THRESHOLD, DATA_DIR

FEATURE_COLS = [
    "EMA_20", "EMA_50", "EMA_200", "RSI",
    "MACD", "MACD_SIGNAL", "MACD_HIST",
    "BB_HIGH", "BB_MID", "BB_LOW", "BB_WIDTH",
    "ATR", "STOCH_K", "STOCH_D",
    "VOLUME_RATIO", "Trend_Regime", "Volatility_Regime", "Volume_Regime",
]


def _get_X(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in FEATURE_COLS if c in df.columns]
    return df[cols].copy()


def predict_next_day(df: pd.DataFrame):
    """
    Train on historical data and predict for the LATEST row.
    Returns: (probability: float, decision: str, latest_row: DataFrame,
              feature_importances: dict)
    """
    df = df.copy()
    df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    df.dropna(subset=["Target"], inplace=True)

    X   = _get_X(df)
    y   = df["Target"]

    split     = int(len(df) * TRAIN_RATIO)
    X_train   = X.iloc[:split]
    y_train   = y.iloc[:split]

    scaler    = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        min_samples_leaf=10, random_state=42,
    )
    model.fit(X_train_s, y_train)

    # ── Predict on the very last row (today) ──────────────────────────────────
    latest    = X.iloc[-1:]
    latest_s  = scaler.transform(latest)
    prob      = float(model.predict_proba(latest_s)[0, 1])
    decision  = "BUY" if prob >= BUY_THRESHOLD else "NO TRADE"

    # Feature importances
    importances = dict(zip(X.columns, model.feature_importances_))

    return prob, decision, df.iloc[-1:], importances