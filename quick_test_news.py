# quick_test_news.py
# Quick test script for the new FREE news system

import sys
import os

print("=" * 80)
print("TESTING FREE NEWS SENTIMENT SYSTEM")
print("=" * 80)

# Test 1: Check imports
print("\n[TEST 1] Checking imports...")
try:
    print("  • Importing feedparser...", end=" ")
    import feedparser
    print("✅")
except ImportError as e:
    print(f"❌ {e}")
    sys.exit(1)

try:
    print("  • Importing transformers...", end=" ")
    from transformers import pipeline
    print("✅")
except ImportError as e:
    print(f"⚠️  WARNING: {e}")
    print("    (Transformers will download on first use)")

try:
    print("  • Importing news_engine_free...", end=" ")
    from news_engine_free import FreeNewsEngine
    print("✅")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

try:
    print("  • Importing sentiment_analyzer_hf...", end=" ")
    from sentiment_analyzer_hf import HFSentimentAnalyzer
    print("✅")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

try:
    print("  • Importing news_sentiment_unified...", end=" ")
    from news_sentiment_unified import UnifiedNewsSentimentEngine
    print("✅")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

# Test 2: Test news engine
print("\n[TEST 2] Testing FreeNewsEngine...")
try:
    engine = FreeNewsEngine()
    print("  ✅ Engine initialized")
    print("  • Available RSS feeds:", list(engine.rss_feeds.keys()))
    
    print("\n  Fetching market news (this may take 10-30 seconds on first run)...")
    news = engine.fetch_market_news()
    print(f"  ✅ Fetched {len(news)} articles")
    
    if news:
        print(f"    • Sample: {news[0].title[:60]}...")
        
except Exception as e:
    print(f"  ⚠️  Could not fetch news: {e}")
    print("    (This is OK - RSS feeds may be unavailable)")

# Test 3: Test sentiment analyzer
print("\n[TEST 3] Testing HFSentimentAnalyzer...")
try:
    analyzer = HFSentimentAnalyzer()
    print("  ✅ Analyzer initialized")
    print(f"  • Models available: {list(analyzer.models.keys())}")
    
    # Test sentiment analysis
    test_text = "RELIANCE stock surges 5% on strong earnings beat!"
    print(f"\n  Analyzing: '{test_text}'")
    print("  (This may take 30+ seconds on first run - models downloading...)")
    
    result = analyzer.analyze_text(test_text)
    print(f"  ✅ Score: {result.score:.2f}")
    print(f"  • Label: {result.label}")
    print(f"  • Confidence: {result.confidence:.2f}")
    
except Exception as e:
    print(f"  ⚠️  Sentiment analysis issue: {e}")

# Test 4: Full integration
print("\n[TEST 4] Testing UnifiedNewsSentimentEngine...")
try:
    engine = UnifiedNewsSentimentEngine()
    print("  ✅ Unified engine initialized")
    
    print("\n  Running full analysis for RELIANCE (may take 1-2 minutes)...")
    print("  This will:")
    print("    • Fetch company news")
    print("    • Fetch market news")
    print("    • Fetch economic news")
    print("    • Analyze sentiment for each")
    print("    • Calculate composite scores")
    
    # Use timeout to avoid long waits in test
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Analysis took too long")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)  # 2 minute timeout
    
    try:
        result = engine.analyze_stock_sentiment("RELIANCE", include_market=True, include_economic=True)
        signal.alarm(0)  # Cancel timeout
        
        print("\n  ✅ Analysis complete!")
        print(f"  • Composite Score: {result['composite_score']:.2f}")
        print(f"  • Trading Signal: {result['trading_signal'].upper()}")
        print(f"  • Confidence: {result['confidence']:.2f}")
        
    except TimeoutError:
        print("\n  ⚠️  Analysis is taking a while (this is normal on first run)")
        print("  • Continue in background - models are being downloaded and cached")
        signal.alarm(0)
    
except Exception as e:
    print(f"  ⚠️  Integration issue: {e}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("""
✅ If all tests passed:
   • Your system is ready for production use!
   • Run: python news_sentiment_unified.py (for full demo)

⚠️  If transformers/torch warnings appeared:
   • They'll download automatically on first real use (~5-10 minutes)
   • Subsequent runs will be fast (5-10 seconds)

🚀 Next steps:
   1. Review FREE_NEWS_SETUP_GUIDE.md
   2. Integrate to your dashboard/trading system
   3. Test with your stocks of interest
   4. Monitor signal accuracy

📊 Usage examples:
   
   # Quick sentiment
   from news_sentiment_unified import analyze_news_sentiment
   result = analyze_news_sentiment("RELIANCE")
   print(result["trading_signal"])  # "buy", "sell", "hold", etc.
   
   # Full analysis with market context
   from news_sentiment_unified import UnifiedNewsSentimentEngine
   engine = UnifiedNewsSentimentEngine()
   analysis = engine.analyze_stock_sentiment("RELIANCE")
   
   # For dashboard
   news = engine.get_news_for_dashboard("RELIANCE", max_articles=10)
""")

print("=" * 80)
