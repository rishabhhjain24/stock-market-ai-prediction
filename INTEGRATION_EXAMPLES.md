# INTEGRATION EXAMPLES FOR YOUR EXISTING CODE
# Copy-paste ready code snippets to add news sentiment to your system

# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: Add News Sentiment to Dashboard (dashboard.py / trading_dashboard.py)
# ════════════════════════════════════════════════════════════════════════════════

"""
import streamlit as st
from news_sentiment_unified import UnifiedNewsSentimentEngine

def display_news_sentiment(symbol: str):
    '''Add this to your dashboard'''
    
    st.header(f"📰 News & Sentiment Analysis - {symbol}")
    
    with st.spinner("Analyzing news..."):
        engine = UnifiedNewsSentimentEngine()
        
        # Get analysis
        analysis = engine.analyze_stock_sentiment(
            symbol,
            include_market=True,
            include_economic=True
        )
        
        # Display composite signal
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Color code the signal
            signal = analysis["trading_signal"]
            colors = {
                "strong_buy": "🟢",
                "buy": "🟢",
                "hold": "🟡",
                "sell": "🔴",
                "strong_sell": "🔴"
            }
            st.metric(
                "News Signal",
                signal.upper(),
                delta=f"{analysis['composite_score']:.2f}"
            )
        
        with col2:
            st.metric(
                "Confidence",
                f"{analysis['confidence']:.0%}",
                delta=None
            )
        
        with col3:
            st.metric(
                "Articles Analyzed",
                analysis['detailed_analysis']['company']['news_count'] +
                analysis['detailed_analysis']['market']['news_count'] +
                analysis['detailed_analysis']['economic']['news_count']
            )
        
        # Display sentiment breakdown
        st.subheader("Sentiment Breakdown")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            comp = analysis.get("company_sentiment", {})
            st.write(f"**Company**: {comp.get('weighted_label', 'N/A')} ({comp.get('weighted_score', 0):.2f})")
        
        with col2:
            mkt = analysis.get("market_sentiment", {})
            st.write(f"**Market**: {mkt.get('weighted_label', 'N/A')} ({mkt.get('weighted_score', 0):.2f})")
        
        with col3:
            econ = analysis.get("economic_sentiment", {})
            st.write(f"**Economic**: {econ.get('weighted_label', 'N/A')} ({econ.get('weighted_score', 0):.2f})")
        
        # Display news articles
        st.subheader("Latest News")
        
        news_data = engine.get_news_for_dashboard(symbol, max_articles=10)
        
        for i, article in enumerate(news_data["articles"], 1):
            with st.expander(f"{article['emoji']} {article['title'][:60]}..."):
                st.write(f"**Source**: {article['source']}")
                st.write(f"**Sentiment**: {article['sentiment'].upper()} ({article['sentiment_score']:.2f})")
                st.write(article["description"])
                st.link_button("Read Full Article", article["url"])

# Usage in main dashboard:
display_news_sentiment("RELIANCE")
"""

# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: Add News Signal to Trading Logic (entry_exit_engine.py)
# ════════════════════════════════════════════════════════════════════════════════

"""
from news_sentiment_unified import analyze_news_sentiment

def get_enhanced_buy_signal(symbol: str, technical_signal: str):
    '''Combine technical signals with news sentiment'''
    
    if technical_signal != "BUY":
        return technical_signal, 0.0
    
    # Get news sentiment
    news_result = analyze_news_sentiment(symbol)
    news_signal = news_result["trading_signal"]
    news_confidence = news_result["confidence"]
    
    # Combine signals
    if news_signal in ["strong_buy", "buy"]:
        # Technical + News agree = STRONG signal
        combined_confidence = news_confidence * 0.9 + 0.1
        return "STRONG_BUY", combined_confidence
    
    elif news_signal == "hold":
        # Technical suggests buy but news is neutral = weak signal
        combined_confidence = news_confidence * 0.5
        return "BUY", combined_confidence
    
    elif news_signal == "sell":
        # Conflict between signals = don't trade
        return "HOLD", 0.0
    
    return technical_signal, news_confidence

# Usage:
signal, confidence = get_enhanced_buy_signal("RELIANCE", "BUY")
if signal == "STRONG_BUY" and confidence > 0.8:
    place_order(symbol, "BUY")
"""

# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: Risk Management with Market Context (risk_management.py)
# ════════════════════════════════════════════════════════════════════════════════

"""
from news_sentiment_unified import UnifiedNewsSentimentEngine

def calculate_position_size(symbol: str, base_size: int, account_risk: float = 0.02):
    '''Adjust position size based on market & economic conditions'''
    
    engine = UnifiedNewsSentimentEngine()
    
    # Get market snapshot
    market_snapshot = engine.get_market_snapshot()
    market_signal = market_snapshot["overall_market_signal"]
    econ_signal = market_snapshot["economic_backdrop"]
    
    # Get individual stock sentiment
    stock_analysis = engine.analyze_stock_sentiment(symbol)
    stock_signal = stock_analysis["trading_signal"]
    stock_confidence = stock_analysis["confidence"]
    
    # Calculate adjustments
    position_multiplier = 1.0
    
    # Market environment adjustment
    if market_signal == "strong_sell":
        position_multiplier *= 0.3  # Reduce by 70%
    elif market_signal == "sell":
        position_multiplier *= 0.6  # Reduce by 40%
    elif market_signal == "strong_buy":
        position_multiplier *= 1.2  # Increase by 20%
    
    # Economic backdrop adjustment
    if econ_signal == "bearish":
        position_multiplier *= 0.7
    elif econ_signal == "bullish":
        position_multiplier *= 1.1
    
    # Stock confidence adjustment
    if stock_confidence < 0.5:
        position_multiplier *= 0.5
    elif stock_confidence > 0.8:
        position_multiplier *= 1.2
    
    final_size = base_size * position_multiplier
    
    return {
        "base_size": base_size,
        "final_size": int(final_size),
        "multiplier": position_multiplier,
        "market_signal": market_signal,
        "econ_signal": econ_signal,
        "stock_confidence": stock_confidence
    }

# Usage:
sizing = calculate_position_size("RELIANCE", base_size=100)
print(f"Buy {sizing['final_size']} shares (adjusted from {sizing['base_size']})")
print(f"Multiplier: {sizing['multiplier']:.1%}")
"""

# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE 4: Watchlist Scanner with Sentiment (watchlist_scanner.py)
# ════════════════════════════════════════════════════════════════════════════════

"""
from news_sentiment_unified import UnifiedNewsSentimentEngine
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def scan_watchlist_with_sentiment(watchlist: list) -> pd.DataFrame:
    '''Scan multiple stocks for sentiment signals'''
    
    engine = UnifiedNewsSentimentEngine()
    results = []
    
    def analyze_stock(symbol):
        try:
            result = engine.analyze_stock_sentiment(symbol)
            return {
                "symbol": symbol,
                "signal": result["trading_signal"],
                "score": result["composite_score"],
                "confidence": result["confidence"],
                "company_articles": result['detailed_analysis']['company']['news_count'],
            }
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    # Analyze in parallel for speed
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(analyze_stock, sym) for sym in watchlist]
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    df = pd.DataFrame(results)
    df = df.sort_values("score", ascending=False)
    
    return df

# Usage:
watchlist = ["RELIANCE", "TCS", "INFY", "ICICIBANK", "HDFC"]
signals = scan_watchlist_with_sentiment(watchlist)

# Show strong buy signals
strong_buys = signals[signals["signal"] == "strong_buy"]
print(f"Strong Buy Signals: {len(strong_buys)}")
print(strong_buys)
"""

# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE 5: Historical Sentiment Tracking (for backtesting)
# ════════════════════════════════════════════════════════════════════════════════

"""
from news_sentiment_unified import UnifiedNewsSentimentEngine
import pandas as pd
from datetime import datetime, timedelta

def track_sentiment_history(symbol: str, days: int = 30):
    '''Track how sentiment changes over time'''
    
    engine = UnifiedNewsSentimentEngine()
    history = []
    
    for day_offset in range(days):
        date = datetime.now() - timedelta(days=day_offset)
        
        # Note: Current implementation fetches fresh news each time
        # For true history, you'd need to store sentiment scores
        
        result = engine.analyze_stock_sentiment(symbol)
        
        history.append({
            "date": date.date(),
            "sentiment_score": result["composite_score"],
            "signal": result["trading_signal"],
            "confidence": result["confidence"],
            "articles": result['detailed_analysis']['company']['news_count']
        })
    
    df = pd.DataFrame(history)
    df = df.sort_values("date")
    
    return df

# Usage:
sentiment_history = track_sentiment_history("RELIANCE", days=30)

# Plot sentiment trend
import matplotlib.pyplot as plt
plt.plot(sentiment_history["date"], sentiment_history["sentiment_score"])
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
plt.xlabel("Date")
plt.ylabel("Sentiment Score (-1 to +1)")
plt.title("RELIANCE Sentiment Trend (30 days)")
plt.show()
"""

# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE 6: Email Alert on Significant Sentiment Changes
# ════════════════════════════════════════════════════════════════════════════════

"""
from news_sentiment_unified import analyze_news_sentiment
import smtplib
from email.mime.text import MIMEText

def send_sentiment_alert(symbol: str, threshold: float = 0.7):
    '''Send alert when sentiment becomes extremely bullish/bearish'''
    
    result = analyze_news_sentiment(symbol)
    score = result["composite_score"]
    
    if abs(score) >= threshold:
        signal_type = "BULLISH" if score > 0 else "BEARISH"
        
        message = f"""
Sentiment Alert for {symbol}
================================
Signal: {signal_type}
Score: {score:.2f}
Confidence: {result['confidence']:.0%}
Signal Type: {result['trading_signal'].upper()}

Company News Sentiment: {result['company_sentiment']['weighted_label']}
Market Sentiment: {result['market_sentiment']['weighted_label']}
Economic Backdrop: {result['economic_sentiment']['weighted_label']}

Action: Review before trading
        """
        
        # Send email (configure with your email settings)
        # send_email(subject=f"{symbol} Sentiment Alert", body=message)

# Usage:
send_sentiment_alert("RELIANCE", threshold=0.7)
"""

print("""
════════════════════════════════════════════════════════════════════════════════
COPY-PASTE INTEGRATION EXAMPLES
════════════════════════════════════════════════════════════════════════════════

The examples above show how to integrate the new news sentiment system into:

1. Dashboard (display news + sentiment scores)
2. Entry/Exit Logic (combine with technical signals)
3. Risk Management (adjust position sizes based on market sentiment)
4. Watchlist Scanner (scan multiple stocks for sentiment signals)
5. Backtesting (track sentiment over time)
6. Alerts (notify on significant changes)

Each example is ready to copy-paste into your existing code.

Questions?
- Check FREE_NEWS_SETUP_GUIDE.md for full documentation
- Run python quick_test_news.py to test your setup
- Review the main files: news_engine_free.py, sentiment_analyzer_hf.py
════════════════════════════════════════════════════════════════════════════════
""")
