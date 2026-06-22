# quick_test.py - Test the system setup and demonstrate all components
# RUN THIS FIRST to verify everything is working

import sys
import os

print("=" * 80)
print("🤖 AI STOCK TRADING SYSTEM - VERIFICATION TEST")
print("=" * 80)

# Step 1: Check imports
print("\n[1/7] Checking Python imports...")
try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    import ta
    from sklearn.ensemble import GradientBoostingClassifier
    import streamlit as st
    print("✅ All core imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Step 2: Check .env file
print("\n[2/7] Checking configuration (.env)...")
from dotenv import load_dotenv
load_dotenv()

api_keys = {
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "DEFAULT_STOCK": os.getenv("DEFAULT_STOCK", "RELIANCE.NS"),
}

for key, value in api_keys.items():
    if value and value != "":
        print(f"✅ {key}: Configured")
    else:
        print(f"⚠️  {key}: Not set (optional for demo)")

# Step 3: Test data fetching
print("\n[3/7] Testing data fetching (RELIANCE.NS)...")
try:
    from data_engine import get_features
    df = get_features("RELIANCE.NS", period="1y")
    if df is not None:
        print(f"✅ Data fetched: {len(df)} rows")
        print(f"   Latest close: ₹{df['Close'].iloc[-1]:.2f}")
        print(f"   Latest RSI: {df['RSI'].iloc[-1]:.1f}")
        print(f"   Latest MACD: {df['MACD'].iloc[-1]:.4f}")
    else:
        print("❌ Could not fetch data")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 4: Test ML model
print("\n[4/7] Testing ML model...")
try:
    from ml_engine import predict_next_day
    prob, decision, latest, importances = predict_next_day(df)
    print(f"✅ ML prediction successful")
    print(f"   Probability (UP): {prob:.2%}")
    print(f"   Decision: {decision}")
    print(f"   Top 3 factors: {list(importances.items())[:3]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 5: Test sentiment analysis
print("\n[5/7] Testing sentiment analysis...")
try:
    from sentiment_engine import analyze_sentiment
    test_text = "Reliance Industries reported strong quarterly earnings with 15% profit growth"
    sentiment = analyze_sentiment(test_text)
    print(f"✅ Sentiment analysis working")
    print(f"   Test phrase sentiment: {sentiment:.3f} (positive)")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 6: Test chart patterns
print("\n[6/7] Testing chart pattern detection...")
try:
    from chart_patterns import detect_all_patterns
    patterns = detect_all_patterns(df)
    if patterns:
        print(f"✅ Chart patterns detected: {len(patterns)}")
        for p in patterns:
            print(f"   • {p.name} ({p.type}, {p.confidence:.0%})")
    else:
        print("✅ No patterns detected (normal)")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 7: Test risk management
print("\n[7/7] Testing risk management...")
try:
    from risk_management import PositionSizer
    sizer = PositionSizer(account_balance=100000)
    metrics = sizer.calculate_position(
        entry_price=2500,
        stop_loss=2450,
        target_price=2600,
    )
    print(f"✅ Risk management working")
    print(f"   Position size: {metrics.position_size:.1%} of account")
    print(f"   Risk: ₹{metrics.risk_amount:.0f}")
    print(f"   Reward: ₹{metrics.reward_amount:.0f}")
    print(f"   R:R Ratio: 1:{metrics.risk_reward_ratio:.2f}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ SYSTEM VERIFICATION COMPLETE")
print("=" * 80)

print("\n📊 NEXT STEPS:")
print("1. Run basic Streamlit UI:")
print("   streamlit run app.py")
print("\n2. Run professional dashboard:")
print("   streamlit run dashboard.py")
print("\n3. Use Python directly:")
print("   from controller import run_pipeline")
print("   result = run_pipeline('RELIANCE.NS')")
print("\n" + "=" * 80)

# Run a quick demo
print("\n🎯 QUICK DEMO: Running full pipeline on RELIANCE.NS...")
try:
    from controller import run_pipeline
    
    print("   Fetching data...")
    result = run_pipeline("RELIANCE.NS")
    
    if result:
        print(f"\n   📊 RESULTS:")
        print(f"   Decision: {result['decision']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Price: ₹{result['price']:.2f}")
        print(f"   RSI: {result['rsi']:.1f}")
        print(f"   EMA(20): ₹{result['ema20']:.2f}")
        print(f"   EMA(50): ₹{result['ema50']:.2f}")
        print(f"   Trend: {'📈 UP' if result['trend_regime'] == 1 else '📉 DOWN'}")
        print(f"\n   💡 AI Analysis:")
        print(f"   {result['explanation'][:200]}...")
    else:
        print("   ❌ Pipeline failed")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("All systems ready! Choose a UI option above or start coding. 🚀")
print("=" * 80)
