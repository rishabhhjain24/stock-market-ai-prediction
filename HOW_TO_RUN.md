# HOW TO RUN THE NEWS SENTIMENT SYSTEM NOW

## 🚀 OPTION 1: TEST IT (2 MINUTES)

### Step 1: Open Terminal
Go to: Terminal → New Terminal (Ctrl + `)

### Step 2: Run the test
```bash
cd "c:\Users\Rishabh Jain\OneDrive\Documents\Stock Market Prediction\Stock Market Prediction"
python test_news_results.py
```

**Wait 1-2 minutes for results** (first time downloads AI models)

---

## 💻 OPTION 2: USE IT IN YOUR CODE (RIGHT NOW)

### Step 1: Open any Python file
Example: `entry_exit_engine.py` or `dashboard.py`

### Step 2: Add 2 lines at the top
```python
# At the very top of your file
from news_sentiment_unified import analyze_news_sentiment
```

### Step 3: Use it anywhere in your code
```python
# Anywhere in your functions:
result = analyze_news_sentiment("RELIANCE")

print(f"Signal: {result['trading_signal']}")      # "buy", "sell", "hold"
print(f"Score: {result['composite_score']}")      # -1 to +1
print(f"Confidence: {result['confidence']}")      # 0-1
```

---

## 🎯 EXAMPLE: ADD TO DASHBOARD

### In `dashboard.py` or `trading_dashboard.py`:

```python
import streamlit as st
from news_sentiment_unified import analyze_news_sentiment

# In your main function:
stock = st.selectbox("Select Stock", ["RELIANCE", "TCS", "INFY", "HDFC"])

# Get news sentiment
news_result = analyze_news_sentiment(stock)

# Display it
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "News Signal",
        news_result["trading_signal"].upper(),
        f"{news_result['composite_score']:.2f}"
    )

with col2:
    st.metric(
        "Confidence",
        f"{news_result['confidence']:.0%}"
    )

with col3:
    st.metric(
        "Company Sentiment",
        news_result["company_sentiment"]["weighted_label"]
    )
```

---

## 📊 EXAMPLE: USE IN TRADING LOGIC

### In `entry_exit_engine.py`:

```python
def should_trade(symbol, direction):
    from news_sentiment_unified import analyze_news_sentiment
    
    # Get news sentiment
    news = analyze_news_sentiment(symbol)
    
    # Only trade if news is bullish
    if direction == "up":
        if news["trading_signal"] in ["buy", "strong_buy"]:
            return True  # OK to trade
        else:
            return False  # Skip trade
    
    return True
```

---

## 🔄 EXAMPLE: SCAN WATCHLIST

### Quick scan of multiple stocks:

```python
from news_sentiment_unified import analyze_news_sentiment

stocks = ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK"]

print("📊 WATCHLIST SENTIMENT SCAN\n")

for stock in stocks:
    result = analyze_news_sentiment(stock)
    signal = result["trading_signal"]
    score = result["composite_score"]
    
    emoji = {
        "strong_buy": "🚀",
        "buy": "🟢",
        "hold": "🟡",
        "sell": "🔴",
        "strong_sell": "💥"
    }.get(signal, "⚪")
    
    print(f"{emoji} {stock:12} {signal:12} Score: {score:+.2f}")
```

---

## ⚡ FASTEST: ONE-LINE TEST

### Just copy-paste this in Python console:

```python
from news_sentiment_unified import analyze_news_sentiment; print(analyze_news_sentiment("RELIANCE")["trading_signal"])
```

Output: `sell` (or buy/hold/strong_buy/strong_sell)

---

## ⏱️ TIMING

| Task | Time |
|------|------|
| First run (downloads models) | 1-2 minutes |
| Subsequent runs | 5-10 seconds |
| News fetch per stock | 2-5 seconds |
| Sentiment analysis | 5-10 seconds |

---

## 🔧 TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'news_sentiment_unified'"
```bash
# Make sure you're in the right directory:
cd "c:\Users\Rishabh Jain\OneDrive\Documents\Stock Market Prediction\Stock Market Prediction"
```

### Error: "transformers not found"
```bash
pip install transformers torch feedparser
```

### Slow first run (1-2 minutes)
✅ Normal! Models are downloading and caching
✅ Only happens ONCE
✅ Subsequent runs are fast (5-10 seconds)

### No news found
✅ That's OK - uses fallback keyword analysis
✅ Still gives you a signal

---

## ✅ EXPECTED OUTPUT

### Running `python test_news_results.py`:

```
================================================================================
TESTING NEW FREE NEWS SENTIMENT SYSTEM - ACTUAL RESULTS
================================================================================

1️⃣  INDIVIDUAL STOCK SENTIMENT ANALYSIS

📊 Analyzing RELIANCE...
   🔴📉 Signal: SELL
   📊 Score: -0.32 | Confidence: 58%
   🏢 Company: 0.00

📊 Analyzing TCS...
   🟡➡️ Signal: HOLD
   📊 Score: -0.14 | Confidence: 58%
   🏢 Company: -0.14

[... more stocks ...]

2️⃣  MARKET SNAPSHOT
📈 Overall Market Signal: SELL
   Score: -0.44

3️⃣  PERFORMANCE COMPARISON
🏆 Stocks Ranked by Bullish Sentiment:
1. HDFC         -0.08 (HOLD)
2. TCS          -0.14 (HOLD)
3. RELIANCE     -0.32 (SELL)
4. INFY         -0.32 (SELL)
5. ICICIBANK    -0.32 (SELL)
```

---

## 🎯 NOW WHAT?

### Option 1: Test First
```bash
python test_news_results.py
```
✅ Takes 1-2 minutes
✅ Shows real signals
✅ Validates your setup

### Option 2: Integrate Now
```python
from news_sentiment_unified import analyze_news_sentiment
result = analyze_news_sentiment("RELIANCE")
```
✅ 3 lines of code
✅ Get instant signals
✅ Use in any project

### Option 3: Add to Dashboard
See example above - copy into `dashboard.py`
✅ Shows sentiment in Streamlit
✅ Real-time updates
✅ Beautiful display

---

## 🚀 START NOW!

### Pick one and run:

**1. Test it:**
```bash
python test_news_results.py
```

**2. Use in code:**
```python
from news_sentiment_unified import analyze_news_sentiment
print(analyze_news_sentiment("RELIANCE"))
```

**3. Add to dashboard:**
Copy the example above into your dashboard.py

---

## 📞 QUICK REFERENCE

**Import:** `from news_sentiment_unified import analyze_news_sentiment`

**Usage:** `result = analyze_news_sentiment("RELIANCE")`

**Get signal:** `result["trading_signal"]` → "buy" / "sell" / "hold"

**Get score:** `result["composite_score"]` → -1.0 to +1.0

**Get confidence:** `result["confidence"]` → 0.0 to 1.0

---

## ✨ YOU'RE READY!

Everything is set up and working. Just run it!

**Questions?**
- Check QUICK_ACTION.md for more examples
- Check NEWS_PERFORMANCE_RESULTS.md for understanding
- Check the code files for technical details

**GO TRADE!** 🚀
