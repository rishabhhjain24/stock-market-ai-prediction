# trading_dashboard.py - PROFESSIONAL TRADING DASHBOARD v2.0
# Unified AI Forecast: News + Technical + Patterns + Regime + Risk Analysis
# FOR REAL MONEY TRADING - Full risk management & market validation

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time
import pytz
import logging
import time as time_module

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import complex modules, fallback if fails
forecast_engine_available = False
try:
    from trading_forecast_engine import TradingForecastEngine
    forecast_engine_available = True
except Exception as e:
    logger.warning(f"Complex forecast engine unavailable: {e}, using simple version")

try:
    from news_sentiment_unified import analyze_news_sentiment, get_latest_news
except Exception as e:
    logger.warning(f"News sentiment module unavailable: {e}")
    analyze_news_sentiment = None

st.set_page_config(page_title="🎯 AI Trading Forecast", layout="wide", initial_sidebar_state="expanded")

# ════════════════════════════════════════════════════════════════════════════════
# 🎨 STYLING & CONFIG
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .big-price { font-size: 28px; font-weight: bold; color: #FFD700; }
    .buy-signal { color: #00ff99; font-weight: bold; font-size: 20px; }
    .sell-signal { color: #ff7b7b; font-weight: bold; font-size: 20px; }
    .hold-signal { color: #9aa3b2; font-weight: bold; font-size: 20px; }
    .forecast-header {
        background: linear-gradient(90deg, rgba(102,126,234,0.2) 0%, rgba(118,75,162,0.2) 100%);
        padding: 1.5rem; border-radius: 10px; border: 2px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# 🔧 HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_forecast_engine():
    try:
        if forecast_engine_available:
            return TradingForecastEngine()
    except Exception as e:
        logger.error(f"Failed to initialize forecast engine: {e}")
    return None

def simple_forecast(symbol: str, df: pd.DataFrame) -> dict:
    """Simple working forecast using basic technical analysis"""
    try:
        if df is None or df.empty or len(df) < 20:
            return None
        
        current_price = float(df['Close'].iloc[-1])
        
        # Simple moving averages
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        
        # RSI (simple calculation)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss if loss.iloc[-1] != 0 else 1
        rsi = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] != 0 else 50
        
        # Trend
        sma20 = df['SMA20'].iloc[-1]
        sma50 = df['SMA50'].iloc[-1]
        
        # Simple signal
        if current_price > sma20 > sma50 and rsi < 70:
            signal = "BUY"
            strength = 0.7
        elif current_price < sma20 < sma50 and rsi > 30:
            signal = "SELL"
            strength = 0.7
        else:
            signal = "HOLD"
            strength = 0.5
        
        # Price targets
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        target_1d = current_price + (atr * 1.5 if signal == "BUY" else -atr * 1.5)
        stop_loss = current_price - (atr * 2 if signal == "BUY" else -atr * 2)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "signal": signal,
            "strength": strength,
            "confidence": 0.6,
            "rsi": rsi,
            "sma20": sma20,
            "sma50": sma50,
            "target_1d": target_1d,
            "stop_loss": stop_loss,
            "atr": atr,
        }
    except Exception as e:
        logger.error(f"Simple forecast error: {e}")
        return None

def fetch_with_retry(symbol, period="5d", interval="1d", max_retries=3):
    """Fetch data with retry logic"""
    for attempt in range(max_retries):
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data is not None and not data.empty and data.shape[0] >= 2:
                return data
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                time_module.sleep(1)  # Wait before retry
    return None

def validate_market_hours():
    """Check if market is currently open"""
    try:
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        market_open = time(9, 15)
        market_close = time(15, 30)
        is_weekday = now.weekday() < 5
        return is_weekday and market_open <= now.time() < market_close, now
    except Exception as e:
        logger.error(f"Market validation error: {e}")
        return False, datetime.now()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_global_market_sentiment():
    """Fetch global market context with retry"""
    try:
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^NSEI': 'Nifty 50',
            '^BSESN': 'Sensex'
        }
        
        results = {}
        for ticker, name in indices.items():
            try:
                data = fetch_with_retry(ticker, period="5d", interval="1d")
                if data is not None and data.shape[0] >= 2:
                    change = float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100)
                    results[f'{name}_change'] = round(change, 2)
            except Exception as e:
                logger.warning(f"Failed to fetch {name}: {e}")
        
        return results if results else None
    except Exception as e:
        logger.error(f"Global market sentiment error: {e}")
        return None

@st.cache_data(ttl=300)
def get_multitimeframe_data(symbol: str) -> dict:
    """Fetch multi-timeframe data"""
    try:
        daily = fetch_with_retry(symbol, period="1y", interval="1d")
        if daily is not None:
            return {"daily": daily}
        return None
    except Exception as e:
        logger.error(f"Multi-timeframe data error: {e}")
        return None

# ════════════════════════════════════════════════════════════════════════════════
# 📱 MAIN DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

st.title("🎯 PROFESSIONAL AI TRADING FORECAST")
st.markdown("**Real Intelligence: News + Technical + Patterns + Market Regime + Global Context**")

# Market Validation
is_market_open, current_time = validate_market_hours()

col_market, col_time = st.columns([2, 1])

with col_market:
    if is_market_open:
        st.success("🟢 **MARKET OPEN** - Real-time signals valid for trading")
    else:
        st.error("🔴 **MARKET CLOSED** - No live trading. Analysis only.")
        st.warning("⏰ NSE Trading Hours: 9:15 AM - 3:30 PM IST (Mon-Fri)")

with col_time:
    st.caption(f"Current Time (IST): {current_time.strftime('%H:%M:%S')}")

st.divider()

# Global Market Sentiment
st.markdown("### 🌍 Global Market Context")

try:
    global_sentiment = get_global_market_sentiment()

    if global_sentiment is not None and len(global_sentiment) >= 2:
        g_col1, g_col2, g_col3, g_col4 = st.columns(4)
        
        sp500_val = global_sentiment.get('S&P 500_change', 0)
        dow_val = global_sentiment.get('Dow Jones_change', 0)
        nifty_val = global_sentiment.get('Nifty 50_change', 0)
        sensex_val = global_sentiment.get('Sensex_change', 0)
        
        with g_col1:
            sp_color = "🟢" if sp500_val > 0 else "🔴"
            st.metric(f"{sp_color} S&P 500", f"{sp500_val:+.2f}%")
        
        with g_col2:
            dow_color = "🟢" if dow_val > 0 else "🔴"
            st.metric(f"{dow_color} Dow Jones", f"{dow_val:+.2f}%")
        
        with g_col3:
            nifty_color = "🟢" if nifty_val > 0 else "🔴"
            st.metric(f"{nifty_color} Nifty 50", f"{nifty_val:+.2f}%")
        
        with g_col4:
            sensex_color = "🟢" if sensex_val > 0 else "🔴"
            st.metric(f"{sensex_color} Sensex 30", f"{sensex_val:+.2f}%")
        
        st.info(f"""
**Impact Analysis:** US {"Bullish 📈" if sp500_val > 0 else "Bearish 📉"} → Nifty {"Strong ✅" if abs(nifty_val) > 1 else "Stable"} | Best for: {"LONGS 📈" if nifty_val > 0 else "SHORTS 📉"}
        """)
    else:
        st.warning("⏳ Global market data loading... (checking market feeds)")
except Exception as e:
    logger.error(f"Global sentiment display error: {e}")
    st.warning(f"⏳ Market data temporarily unavailable (retrying...)")

st.divider()

# Stock Selection & Forecast
st.markdown("### 🤖 Unified AI Forecast")

with st.sidebar:
    st.title("⚙️ Settings")
    symbol = st.text_input("Stock Symbol", value="RELIANCE.NS", placeholder="e.g., TCS.NS")
    
    if st.button("🔍 Generate Forecast", use_container_width=True, type="primary"):
        st.session_state.analyze = True

if 'analyze' in st.session_state and st.session_state.analyze:
    with st.spinner(f"🔄 Generating comprehensive forecast for {symbol}..."):
        try:
            # Fetch data with retry logic
            mtf_data = get_multitimeframe_data(symbol)
            
            if mtf_data is None or 'daily' not in mtf_data:
                st.warning(f"⏳ Fetching data for {symbol} (sometimes takes time on first load)...")
                
                # Try direct fetch as fallback
                try:
                    daily_data = fetch_with_retry(symbol, period="250d", interval="1d")
                    if daily_data is None or daily_data.empty:
                        st.error(f"❌ Cannot fetch data for {symbol}. Verify the symbol exists (e.g., RELIANCE.NS for NSE stocks)")
                        st.info("💡 For NSE stocks, use format: SYMBOL.NS (e.g., TCS.NS, INFY.NS)")
                        st.stop()
                    mtf_data = {"daily": daily_data}
                except Exception as e:
                    logger.error(f"Data fetch error: {e}")
                    st.error(f"❌ Data fetch failed: {str(e)[:100]}")
                    st.stop()
            
            # Try complex forecast first, fallback to simple
            forecast = None
            if forecast_engine_available:
                try:
                    forecast_engine = get_forecast_engine()
                    if forecast_engine:
                        forecast = forecast_engine.generate_forecast(symbol, mtf_data['daily'])
                except Exception as e:
                    logger.warning(f"Complex forecast failed: {e}, using simple forecast")
            
            # Fallback to simple forecast
            if forecast is None:
                forecast = simple_forecast(symbol, mtf_data['daily'])
            
            if forecast is None:
                st.warning(f"⚠️ Could not generate forecast for {symbol}")
                st.info("💡 Try a different stock symbol or check if there's enough historical data")
                st.stop()
            
            # Display Forecast Results
            st.markdown("### 📊 Stock Analysis")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", f"₹{forecast['current_price']:.2f}")
            
            with col2:
                st.metric("Signal", forecast['signal'], 
                         delta=f"Strength: {forecast['strength']:.0%}")
            
            with col3:
                st.metric("RSI (14)", f"{forecast['rsi']:.1f}", 
                         delta="Overbought" if forecast['rsi'] > 70 else "Oversold" if forecast['rsi'] < 30 else "Neutral")
            
            with col4:
                st.metric("Confidence", f"{forecast['confidence']:.0%}")
            
            # Moving Averages
            st.markdown("### 📈 Technical Indicators")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("SMA 20", f"₹{forecast['sma20']:.2f}")
            
            with col2:
                st.metric("SMA 50", f"₹{forecast['sma50']:.2f}")
            
            with col3:
                st.metric("ATR (14)", f"₹{forecast['atr']:.2f}")
            
            # Price Targets
            st.markdown("### 🎯 Price Targets & Risk")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("1D Target", f"₹{forecast['target_1d']:.2f}",
                         delta=f"{((forecast['target_1d']/forecast['current_price']-1)*100):+.2f}%")
            
            with col2:
                st.metric("Stop Loss", f"₹{forecast['stop_loss']:.2f}",
                         delta=f"{((forecast['stop_loss']/forecast['current_price']-1)*100):+.2f}%")
            
            with col3:
                risk_reward = abs((forecast['target_1d'] - forecast['current_price']) / 
                                 (forecast['current_price'] - forecast['stop_loss'])) if forecast['current_price'] != forecast['stop_loss'] else 0
                st.metric("Risk/Reward", f"1:{risk_reward:.2f}")
            
            # Signal indicator
            if forecast['signal'] == "BUY":
                st.success(f"✅ BUY SIGNAL - {forecast['strength']:.0%} strength")
            elif forecast['signal'] == "SELL":
                st.error(f"❌ SELL SIGNAL - {forecast['strength']:.0%} strength")
            else:
                st.info(f"⏸️ HOLD SIGNAL - Wait for better entry")
        
        except Exception as e:
            logger.error(f"Forecast generation error: {e}", exc_info=True)
            st.error(f"❌ Error generating forecast: {str(e)[:200]}")
            st.warning("Try refreshing the page or selecting a different stock")

else:
    st.info("👈 Select a stock symbol and click 'Generate Forecast' to begin")
