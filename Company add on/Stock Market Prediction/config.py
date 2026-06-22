# config.py - Central configuration system for the complete trading platform
# This module centralizes all settings, making it easy to modify behavior across the app
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 ENVIRONMENT & PATHS
# ────────────────────────────────────────────────────────────────────────────────
ROOT_DIR       = Path(__file__).parent
DATA_DIR       = ROOT_DIR / "data"
MODELS_DIR     = ROOT_DIR / "models"
LOGS_DIR       = ROOT_DIR / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🏦 STOCK & MARKET SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
DEFAULT_STOCK  = os.getenv("DEFAULT_STOCK", "RELIANCE.NS")
DEFAULT_INDEX  = "^NSEI"  # NSE Nifty 50
START_DATE     = "2015-01-01"
HISTORICAL_DAYS = 730  # 2 years default

# Popular Indian stocks for watchlist
WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "WIPRO.NS", "HDFC.NS",
    "ICICIBANK.NS", "SBIN.NS", "MARUTI.NS", "JSWSTEEL.NS", "BAJAJFINSV.NS",
]

# ────────────────────────────────────────────────────────────────────────────────
# 🤖 ML MODEL SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
TRAIN_RATIO         = 0.80   # 80% train, 20% test (time-based split, prevents leakage)
BUY_THRESHOLD       = 0.60   # Minimum probability to trigger BUY signal
SELL_THRESHOLD      = 0.40   # Probability below which to trigger SELL signal
CONFIDENCE_LEVELS   = [0.50, 0.55, 0.60, 0.65, 0.70]

# Gradient Boosting Model Hyperparameters
# WHY: GB is faster than Random Forest and handles non-linear relationships well
GB_N_ESTIMATORS = 200      # Number of trees (more ≠ better after ~150)
GB_MAX_DEPTH    = 4        # Shallow trees prevent overfitting
GB_LEARNING_RATE= 0.05     # Smaller is more stable but slower
GB_MIN_SAMPLES  = 10       # Prevent leaf nodes that are too small/noisy
GB_RANDOM_STATE = 42       # For reproducibility

# ────────────────────────────────────────────────────────────────────────────────
# 📊 TECHNICAL INDICATOR WINDOWS
# ────────────────────────────────────────────────────────────────────────────────
# WHY these values:
#  - EMA 20: short-term trend (5 trading days * 4 weeks of data)
#  - EMA 50: medium-term trend
#  - EMA 200: long-term trend ("year" of data)
#  - RSI 14: standard, catches overbought/oversold
#  - Bollinger 20: default, 2 std dev captures ~95% of moves
#  - MACD 12/26/9: standard momentum parameters
#  - ATR 14: volatility measurement
#  - Stochastic 14/3: momentum oscillator with smoothing

EMA_SHORT      = 20        # Short-term trend
EMA_MEDIUM     = 50        # Medium-term trend
EMA_LONG       = 200       # Long-term trend
RSI_WINDOW     = 14        # Relative strength index
BB_WINDOW      = 20        # Bollinger Bands period
BB_STD_DEV     = 2         # 2 sigma = ~95% of price moves
ATR_WINDOW     = 14        # Average True Range for volatility
MACD_FAST      = 12        # MACD fast EMA
MACD_SLOW      = 26        # MACD slow EMA
MACD_SIGNAL    = 9         # MACD signal line
STOCH_WINDOW   = 14        # Stochastic oscillator
STOCH_SMOOTH   = 3         # Smoothing for K and D

# ────────────────────────────────────────────────────────────────────────────────
# 💰 RISK MANAGEMENT SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
# WHY these rules:
#  - Risk per trade: never risk >2% of account (professional standard)
#  - Max positions: prevents overconcentration
#  - Stop-loss: typically 2xATR below entry (gives room for noise)
#  - Take-profit: usually 2:1 or 3:1 reward/risk ratio

RISK_PER_TRADE         = 0.02        # Risk 2% of account per trade
MAX_POSITION_SIZE      = 0.10        # Max 10% of account in one trade
MIN_REWARD_RISK_RATIO  = 2.0         # Target 2:1 or better rewards
POSITION_SIZING_METHOD = "percent"   # Options: "percent", "fixed", "kelly"

# ────────────────────────────────────────────────────────────────────────────────
# 📈 TRADING STRATEGY SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
# Support for multiple trading styles

TRADING_STRATEGIES = {
    "aggressive": {      # Frequent trades, lower accuracy tolerance
        "buy_threshold": 0.55,
        "sell_threshold": 0.45,
        "max_positions": 5,
    },
    "balanced": {        # Default - medium risk/reward
        "buy_threshold": 0.60,
        "sell_threshold": 0.40,
        "max_positions": 3,
    },
    "conservative": {    # High confidence signals only
        "buy_threshold": 0.70,
        "sell_threshold": 0.30,
        "max_positions": 1,
    },
}

ACTIVE_STRATEGY = "balanced"

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 API & EXTERNAL SERVICES
# ────────────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
NEWS_API_KEY    = os.getenv("NEWS_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ────────────────────────────────────────────────────────────────────────────────
# 📊 SENTIMENT ANALYSIS SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
# WHY TextBlob: free, simple, good for financial news (no API key needed)
# Can be upgraded to FinBERT for better accuracy

USE_FINBERT_SENTIMENT = False  # Set True to use FinBERT (requires transformer install)
SENTIMENT_THRESHOLD_POSITIVE = 0.3   # Score > 0.3 = positive
SENTIMENT_THRESHOLD_NEGATIVE = -0.3  # Score < -0.3 = negative
NEWS_FETCH_COUNT = 10          # Number of articles to analyze

# ────────────────────────────────────────────────────────────────────────────────
# 📋 BACKTESTING & PERFORMANCE SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
BACKTEST_COMMISSION  = 0.0005   # 0.05% per trade (realistic brokerage)
BACKTEST_SLIPPAGE    = 0.0002   # 0.02% slippage on entries/exits
ANNUAL_RISK_FREE_RATE = 0.06    # Used for Sharpe ratio calculation
PROFIT_FACTOR_TARGET = 2.0      # Gross profit / gross loss should be > 2x

# ────────────────────────────────────────────────────────────────────────────────
# 🔔 NOTIFICATION SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
ENABLE_TELEGRAM = bool(TELEGRAM_BOT_TOKEN)
SEND_ALERTS_ON = {
    "buy_signal": True,
    "sell_signal": True,
    "portfolio_alert": True,
    "error": True,
}

# ────────────────────────────────────────────────────────────────────────────────
# 🎯 CHART PATTERN DETECTION SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
DETECT_PATTERNS = True
PATTERN_LOOKBACK = 50        # Bars to look back for patterns
PATTERN_CONFIDENCE_MIN = 0.7  # Min confidence to trigger pattern-based signal

# ────────────────────────────────────────────────────────────────────────────────
# 🔍 DEBUG & LOGGING
# ────────────────────────────────────────────────────────────────────────────────
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_FILE = LOGS_DIR / "trading_system.log"

# ────────────────────────────────────────────────────────────────────────────────
# 💾 DATABASE SETTINGS
# ────────────────────────────────────────────────────────────────────────────────
DATABASE_TYPE = "sqlite"  # Options: "sqlite", "postgresql"
DATABASE_PATH = DATA_DIR / "trading.db"
DATABASE_URL  = f"sqlite:///{DATABASE_PATH}"  # For SQLAlchemy