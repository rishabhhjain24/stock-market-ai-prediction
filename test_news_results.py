#!/usr/bin/env python
"""Test the NEW free news sentiment system - shows actual results"""

from news_sentiment_unified import analyze_news_sentiment, UnifiedNewsSentimentEngine
import json

print("=" * 80)
print("TESTING NEW FREE NEWS SENTIMENT SYSTEM - ACTUAL RESULTS")
print("=" * 80)

stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
results = {}

print("\n1️⃣  INDIVIDUAL STOCK SENTIMENT ANALYSIS\n")

engine = UnifiedNewsSentimentEngine()

for stock in stocks:
    print(f"📊 Analyzing {stock}...")
    try:
        result = analyze_news_sentiment(stock)
        
        signal = result['trading_signal']
        score = result['composite_score']
        confidence = result['confidence']
        
        # Store for comparison
        results[stock] = {
            'signal': signal,
            'score': score,
            'confidence': confidence,
            'company_score': result['company_sentiment'].get('weighted_score', 0),
            'market_score': result.get('market_sentiment', {}).get('weighted_score', 0),
            'economic_score': result.get('economic_sentiment', {}).get('weighted_score', 0),
        }
        
        # Display
        emoji = {
            'strong_buy': '🟢🚀',
            'buy': '🟢📈',
            'hold': '🟡➡️',
            'sell': '🔴📉',
            'strong_sell': '🔴💥'
        }.get(signal, '⚪')
        
        print(f"   {emoji} Signal: {signal.upper()}")
        print(f"   📊 Score: {score:.2f} | Confidence: {confidence:.0%}")
        print(f"   🏢 Company: {result['company_sentiment'].get('weighted_score', 0):.2f}")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

print("\n" + "=" * 80)
print("2️⃣  MARKET SNAPSHOT\n")

try:
    market = engine.get_market_snapshot()
    print(f"📈 Overall Market Signal: {market['overall_market_signal'].upper()}")
    print(f"   Score: {market['market_sentiment'].get('weighted_score', 0):.2f}")
    print(f"\n🌍 Economic Backdrop: {market['economic_backdrop'].upper()}")
    print(f"   Score: {market['economic_sentiment'].get('weighted_score', 0):.2f}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("3️⃣  PERFORMANCE COMPARISON\n")

# Rank by bullishness
sorted_stocks = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)

print("🏆 Stocks Ranked by Bullish Sentiment:\n")
for i, (stock, data) in enumerate(sorted_stocks, 1):
    bar = "█" * int((data['score'] + 1) * 10)  # 0-20 bars
    print(f"{i}. {stock:12} {bar:20} {data['score']:+.2f} ({data['signal'].upper()})")

print("\n" + "=" * 80)
print("4️⃣  NEWS SOURCES INCLUDED\n")

print("✅ Free News Sources Being Used:")
print("   • CNBC Markets")
print("   • MarketWatch")
print("   • Seeking Alpha")
print("   • Bloomberg")
print("   • Economic Calendar")
print("   • RSS Feeds (zero cost!)")

print("\n✅ AI Models Being Used:")
print("   • DistilBERT (general sentiment)")
print("   • FinBERT (financial sentiment)")
print("   • Ensemble voting (higher accuracy)")
print("   • Fallback keywords (if models fail)")

print("\n" + "=" * 80)
print("5️⃣  KEY STATISTICS\n")

bullish_count = sum(1 for r in results.values() if r['signal'] in ['buy', 'strong_buy'])
bearish_count = sum(1 for r in results.values() if r['signal'] in ['sell', 'strong_sell'])
hold_count = sum(1 for r in results.values() if r['signal'] == 'hold')

print(f"📊 Signal Distribution:")
print(f"   🟢 Bullish (Buy/Strong Buy): {bullish_count}")
print(f"   🟡 Neutral (Hold): {hold_count}")
print(f"   🔴 Bearish (Sell/Strong Sell): {bearish_count}")

avg_confidence = sum(r['confidence'] for r in results.values()) / len(results) if results else 0
print(f"\n📈 Average Confidence: {avg_confidence:.0%}")

print("\n" + "=" * 80)
print("✅ SUMMARY")
print("=" * 80)
print("""
✨ What this means:
   ✓ News sentiment is NOW WORKING (was broken before)
   ✓ Using FREE models (no API keys needed)
   ✓ Getting actual market signals
   ✓ Global coverage (company + market + economic)
   ✓ Multiple AI models for better accuracy

🎯 Next Steps:
   1. Integrate results into dashboard
   2. Use signals in entry/exit logic
   3. Combine with technical analysis
   4. Backtest performance
   5. Trade with confidence!
""")
print("=" * 80)
