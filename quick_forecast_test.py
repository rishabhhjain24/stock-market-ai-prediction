# quick_forecast_test.py - Test the new AI trading forecast system
# Run this to verify everything is working before using real money

import sys
sys.path.insert(0, r'c:\Users\Rishabh Jain\OneDrive\Documents\Stock Market Prediction\Stock Market Prediction')

from trading_forecast_engine import TradingForecastEngine
import yfinance as yf
from datetime import datetime
import pytz

print("="*80)
print("🎯 AI TRADING FORECAST SYSTEM - TEST")
print("="*80)

# Initialize engine
engine = TradingForecastEngine()
print("\n✅ Forecast engine initialized")

# Test with RELIANCE
symbol = "RELIANCE.NS"
print(f"\n📊 Testing forecast for {symbol}...")

try:
    # Fetch data
    df = yf.download(symbol, period="250d", interval="1d", progress=False)
    print(f"✅ Fetched {len(df)} candles of historical data")
    
    # Generate forecast
    forecast = engine.generate_forecast(symbol, df)
    
    if forecast:
        print("\n" + "="*80)
        print("📈 FORECAST RESULTS")
        print("="*80)
        
        print(f"\n🎯 Symbol: {forecast.symbol}")
        print(f"💰 Current Price: ₹{forecast.current_price:.2f}")
        print(f"📍 Recommendation: {forecast.recommendation}")
        print(f"💪 Signal Strength: {int(forecast.forecast_strength*100)}%")
        print(f"🧠 Overall Confidence: {int(forecast.forecast_confidence*100)}%")
        
        print(f"\n📊 PRICE TARGETS:")
        print(f"   1h Target:  ₹{forecast.target_price_1h:.2f}")
        print(f"   4h Target:  ₹{forecast.target_price_4h:.2f}")
        print(f"   1d Target:  ₹{forecast.target_price_1d:.2f}")
        print(f"   Stop Loss:  ₹{forecast.stop_loss:.2f}")
        
        print(f"\n💹 RISK/REWARD:")
        print(f"   Risk:Reward Ratio: {forecast.risk_reward_ratio:.2f}:1")
        print(f"   Portfolio Risk %: {forecast.portfolio_risk_percent:.1f}%")
        
        print(f"\n🧠 AI COMPONENT ANALYSIS:")
        print(f"   📰 News Sentiment:       {forecast.news_sentiment.score:+.2f} ({int(forecast.news_sentiment.confidence*100)}% conf)")
        print(f"   📊 Technical:            {forecast.technical_indicators.score:+.2f} ({int(forecast.technical_indicators.confidence*100)}% conf)")
        print(f"   📈 Chart Patterns:       {forecast.chart_patterns.score:+.2f} ({int(forecast.chart_patterns.confidence*100)}% conf)")
        print(f"   🌪️  Market Regime:        {forecast.market_regime.score:+.2f} ({int(forecast.market_regime.confidence*100)}% conf)")
        print(f"   📍 Price Action:         {forecast.price_action.score:+.2f} ({int(forecast.price_action.confidence*100)}% conf)")
        print(f"   📦 Volume Analysis:      {forecast.volume_analysis.score:+.2f} ({int(forecast.volume_analysis.confidence*100)}% conf)")
        print(f"   🌍 Global Sentiment:     {forecast.global_sentiment.score:+.2f} ({int(forecast.global_sentiment.confidence*100)}% conf)")
        
        print(f"\n⏱️  TRADING WINDOW:")
        print(f"   Market Hours Valid: {forecast.market_hours_valid}")
        print(f"   Best Entry Time: {forecast.best_entry_time}")
        print(f"   Hours Remaining: {forecast.trading_window_hours:.1f}h")
        
        if forecast.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in forecast.warnings:
                print(f"   • {warning}")
        
        if forecast.risk_factors:
            print(f"\n⚠️  RISK FACTORS:")
            for risk in forecast.risk_factors:
                print(f"   • {risk}")
        
        print("\n" + "="*80)
        print("✅ FORECAST GENERATION SUCCESSFUL!")
        print("="*80)
        
        print("\n📌 NEXT STEPS:")
        print("1. Run: streamlit run trading_dashboard.py")
        print("2. Enter stock symbol (e.g., RELIANCE.NS)")
        print("3. Click 'Generate Forecast'")
        print("4. Review: News + Technical + Patterns + Market Regime")
        print("5. Check: Entry/Exit prices, Risk/Reward, Warnings")
        print("6. Trade: ONLY during market hours with stop loss!")
        print("\n💰 REMEMBER: Paper trade first before using real money!")
        
    else:
        print("❌ Could not generate forecast")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
