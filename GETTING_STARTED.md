# GETTING_STARTED.md - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (1 minute)
```bash
cd "Stock Market Prediction"
pip install -r requirements.txt
```

### Step 2: Create/Update .env File (1 minute)
```
GEMINI_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_newsapi_key_here
DEFAULT_STOCK=RELIANCE.NS
```

**Get Free API Keys:**
- 🤖 [Gemini API](https://ai.google.dev/) (free tier available)
- 📰 [NewsAPI](https://newsapi.org/) (free tier available)

### Step 3: Verify Setup (1 minute)
```bash
python quick_test.py
```

Should show ✅ for all components. If any ❌, check the error message.

### Step 4: Launch Dashboard (1 minute)
```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501` - explore all 5 pages!

### Step 5: Run Your First Analysis (1 minute)
```python
from controller import run_pipeline

result = run_pipeline("RELIANCE.NS")
print(result)
```

---

## 📊 System Overview (2 Minutes Read)

Your system now has **8 powerful modules**:

### 1️⃣ **Data Engine** (`data_engine.py`)
Fetches market data + computes 18 indicators
```
Input: Stock symbol + timeframe
Output: DataFrame with price + 18+ indicators
```

### 2️⃣ **ML Prediction** (`ml_engine.py`)
Predicts if price will go UP or DOWN tomorrow
```
Input: 18 technical indicators
Output: 65% probability UP = BUY signal
```

### 3️⃣ **Sentiment Analysis** (`sentiment_engine.py`)
Analyzes recent news headlines for bias
```
Input: News articles
Output: Positive/Negative/Neutral score
```

### 4️⃣ **Chart Patterns** (`chart_patterns.py`)
Detects technical reversal patterns
```
Input: Price data
Output: Head & Shoulders, Double Top, Triangles
```

### 5️⃣ **Market Regime** (`market_regime.py`)
Classifies current market type
```
Input: Price data
Output: Uptrend, Downtrend, or Consolidation
```

### 6️⃣ **Risk Management** (`risk_management.py`)
Calculates safe position sizes
```
Input: Entry, Stop, Target prices
Output: How many shares to buy (by % of account)
```

### 7️⃣ **Paper Trading** (`paper_trading.py`)
Simulates trading without real money
```
Input: Trade parameters
Output: Simulated P&L, win rate, stats
```

### 8️⃣ **Watchlist Scanner** (`watchlist_scanner.py`)
Scans 50+ stocks for opportunities
```
Input: List of stocks
Output: Best buy/sell signals ranked by score
```

---

## 🎯 Common Use Cases

### Use Case 1: Find Trading Ideas
```bash
streamlit run dashboard.py
# Go to "📈 Watchlist Scanner" page
# Click "🔄 Scan All"
# See top BUY/SELL signals with confidence scores
```

### Use Case 2: Deep Analysis of One Stock
```bash
streamlit run dashboard.py
# Go to "🎯 Single Stock Analysis"
# Enter "RELIANCE.NS"
# See ML probability, sentiment, patterns, AI explanation
```

### Use Case 3: Test Strategy (Paper Trading)
```bash
streamlit run dashboard.py
# Go to "📝 Paper Trading"
# Enter trade details
# Track P&L without real money
```

### Use Case 4: Python Script for Automation
```python
from watchlist_scanner import WatchlistScanner

stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "WIPRO.NS"]
scanner = WatchlistScanner(stocks=stocks)
results = scanner.scan_watchlist()

# Get consensus signals only
consensus = scanner.get_consensus_signals(min_agreement=0.7)
for signal in consensus:
    print(f"{signal['stock']}: {signal['signal']} (consensus: {signal['consensus_pct']:.0%})")
```

### Use Case 5: Build Your Own Dashboard
```python
# Import any component
from data_engine import get_features
from ml_engine import predict_next_day
from sentiment_engine import sentiment_analysis_report
from chart_patterns import detect_all_patterns

# Combine them
df = get_features("RELIANCE.NS")
ml_prob, decision, _, _ = predict_next_day(df)
sentiment_data = sentiment_analysis_report("RELIANCE.NS", [])
patterns = detect_all_patterns(df)

# Build your own UI
print(f"Buy: {decision}, Confidence: {ml_prob:.1%}")
```

---

## 📋 Understanding the Signals

### Signal Interpretation

```
STRONG BUY 🟢🟢    All signals agree → High confidence
├── ML: 65%+ probability UP
├── Sentiment: Positive
├── Pattern: Bullish reversal detected
└── Technicals: RSI <50, MACD >0

BUY 🟢              Most signals positive → Medium confidence
├── ML: 55-65% probability
├── At least 2 other bullish indicators
└── No strong bearish signals

NEUTRAL ⚪          Signals mixed → Wait for clarity
├── ML probability near 50%
└── Technicals neutral

SELL 🔴             Most signals negative
├── ML: 35-45% probability UP
└── Bearish patterns or sentiment

STRONG SELL 🔴🔴   All signals negative → High bearish confidence
├── ML: <35% probability UP
├── Sentiment: Negative news
├── Pattern: Bearish reversal
└── Technicals: RSI >70, MACD <0
```

---

## ⚙️ Key Configuration Options

### Adjust Trading Aggressiveness
In `config.py`:
```python
# Conservative: fewer trades, higher accuracy
BUY_THRESHOLD = 0.70          # Require 70% confidence (high bar)
SELL_THRESHOLD = 0.30
ACTIVE_STRATEGY = "conservative"

# Aggressive: more trades, lower accuracy  
BUY_THRESHOLD = 0.55          # 55% is enough (frequent trades)
SELL_THRESHOLD = 0.45
ACTIVE_STRATEGY = "aggressive"
```

### Adjust Risk Per Trade
```python
RISK_PER_TRADE = 0.01         # 1% per trade (very conservative)
RISK_PER_TRADE = 0.02         # 2% per trade (standard)
RISK_PER_TRADE = 0.05         # 5% per trade (aggressive - risky!)
```

### Adjust Watchlist
```python
WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",       # Top 3
    "WIPRO.NS", "HDFC.NS", "ICICIBANK.NS",    # Add your picks
]
```

---

## 🐛 Common Issues & Fixes

### Issue 1: "No data found for RELIANCE"
**Problem**: Wrong symbol format
**Fix**: Use NSE format: `RELIANCE.NS` (not RIL or RELIANCE)

### Issue 2: Streamlit dashboard doesn't load
**Problem**: Missing dependencies
**Fix**: `pip install streamlit plotly -upgrade`

### Issue 3: Gemini API errors
**Problem**: Invalid or expired API key
**Fix**: Get new key from https://ai.google.dev/

### Issue 4: Very slow scanning
**Problem**: Too many stocks with slow internet
**Fix**: Reduce watchlist size or increase timeout

### Issue 5: Paper trading data doesn't persist
**Problem**: Database file deleted
**Fix**: Not a problem - will recreate automatically

---

## 📚 Learning Path

### Day 1: Understand the System
- [ ] Read README.md (comprehensive overview)
- [ ] Run quick_test.py (verify setup)
- [ ] Explore dashboard.py (see all features)

### Day 2: Deep Dive into Components
- [ ] Read IMPLEMENTATION_GUIDE.md
- [ ] Understand each module in isolation
- [ ] Try Python examples from module docs

### Day 3: Test & Customize
- [ ] Run paper trading simulator
- [ ] Modify configuration parameters
- [ ] Test on multiple stocks

### Day 4: Automation & Integration
- [ ] Create custom Python scripts
- [ ] Build simple trading bots
- [ ] Export data for analysis

---

## 🎯 Example: Complete Workflow

```python
# 1. Get market data
from data_engine import get_features
df = get_features("RELIANCE.NS", period="2y")
print(f"Loaded {len(df)} days of data")

# 2. Run ML prediction
from ml_engine import predict_next_day
prob, decision, latest, importances = predict_next_day(df)
print(f"ML Signal: {decision} ({prob:.1%})")

# 3. Check news sentiment
from news_engine import get_latest_news
from sentiment_engine import sentiment_analysis_report
news = get_latest_news("RELIANCE.NS")
report = sentiment_analysis_report("RELIANCE.NS", news)
print(f"News Sentiment: {report['sentiment_label']}")

# 4. Detect chart patterns
from chart_patterns import detect_all_patterns
patterns = detect_all_patterns(df)
if patterns:
    print(f"Pattern: {patterns[0].name}")

# 5. Calculate position size
from risk_management import PositionSizer
sizer = PositionSizer(account_balance=100000, risk_per_trade=0.02)
entry = latest.iloc[0]["Close"]
stop = entry - 2 * latest.iloc[0]["ATR"]
target = entry + 3 * latest.iloc[0]["ATR"]

metrics = sizer.calculate_position(entry, stop, target)
print(f"Position Size: {metrics.position_size:.1%}")

# 6. Paper trade it
from paper_trading import PaperTradingEngine
engine = PaperTradingEngine(initial_balance=100000)
trade = engine.enter_trade(
    stock="RELIANCE.NS",
    entry_price=entry,
    quantity=int(metrics.position_units),
    stop_loss=stop,
    target_price=target,
    reason="Full ML + Sentiment + Pattern setup"
)
print(f"Trade #{trade.id} entered")

# 7. Get stats
stats = engine.calculate_stats()
print(f"Account: ${stats['current_balance']:,.0f}")
print(f"Return: {stats['total_return_pct']:.1f}%")
```

---

## 🔗 Useful Links

- **Complete Docs**: README.md
- **Implementation Details**: IMPLEMENTATION_GUIDE.md
- **Module Deep Dives**: Each module has docstrings
- **Fast Testing**: quick_test.py

---

## 💡 Pro Tips

1. **Start Conservative**: Use `conservative` strategy first, then scale up
2. **Paper Trade First**: Test on paper before risking real money
3. **Monitor Consensus**: Look for signals where ML + Pattern + Sentiment agree
4. **Check Market Regime**: Uptrend favors buys, downtrend favors avoidance
5. **Review Regularly**: Run quick_test.py weekly to ensure setup is stable

---

## 🚀 You're Ready!

Start with:
```bash
streamlit run dashboard.py
```

Explore all pages, understand what each shows, then start using the system!

**Questions?** Check README.md or IMPLEMENTATION_GUIDE.md for detailed explanations.

**Happy Trading! 📈**
