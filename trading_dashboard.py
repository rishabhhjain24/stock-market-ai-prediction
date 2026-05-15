# trading_dashboard.py - PROFESSIONAL TRADING DASHBOARD v2.0
# Unified AI Forecast: News + Technical + Patterns + Regime + Risk Analysis
# FOR REAL MONEY TRADING - Full risk management & market validation

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time
import pytz

from trading_forecast_engine import TradingForecastEngine
from news_sentiment_unified import analyze_news_sentiment, get_latest_news

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
    return TradingForecastEngine()

def validate_market_hours():
    """Check if market is currently open"""
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    market_open = time(9, 15)
    market_close = time(15, 30)
    is_weekday = now.weekday() < 5
    return is_weekday and market_open <= now.time() < market_close, now

def get_global_market_sentiment():
    """Fetch global market context"""
    try:
        sp500 = yf.download("^GSPC", period="5d", interval="1d", progress=False)
        dow = yf.download("^DJI", period="5d", interval="1d", progress=False)
        nifty = yf.download("^NSEI", period="5d", interval="1d", progress=False)
        sensex = yf.download("^BSESN", period="5d", interval="1d", progress=False)
        
        if sp500 is None or sp500.empty or sp500.shape[0] < 2:
            return None
        
        return {
            'sp500_change': float((sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2] * 100),
            'dow_change': float((dow['Close'].iloc[-1] - dow['Close'].iloc[-2]) / dow['Close'].iloc[-2] * 100),
            'nifty_change': float((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2] * 100),
            'sensex_change': float((sensex['Close'].iloc[-1] - sensex['Close'].iloc[-2]) / sensex['Close'].iloc[-2] * 100),
        }
    except:
        return None

def get_multitimeframe_data(symbol: str) -> dict:
    """Fetch multi-timeframe data"""
    try:
        intraday_1h = yf.download(symbol, period="7d", interval="1h", progress=False)
        daily = yf.download(symbol, period="1y", interval="1d", progress=False)
        if intraday_1h is not None and daily is not None and not intraday_1h.empty and not daily.empty:
            return {"1h": intraday_1h, "daily": daily}
        return None
    except:
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

global_sentiment = get_global_market_sentiment()

if global_sentiment is not None:
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)
    
    with g_col1:
        sp_color = "🟢" if global_sentiment['sp500_change'] > 0 else "🔴"
        st.metric(f"{sp_color} S&P 500", f"{global_sentiment['sp500_change']:+.2f}%")
    
    with g_col2:
        dow_color = "🟢" if global_sentiment['dow_change'] > 0 else "🔴"
        st.metric(f"{dow_color} Dow Jones", f"{global_sentiment['dow_change']:+.2f}%")
    
    with g_col3:
        nifty_color = "🟢" if global_sentiment['nifty_change'] > 0 else "🔴"
        st.metric(f"{nifty_color} Nifty 50", f"{global_sentiment['nifty_change']:+.2f}%")
    
    with g_col4:
        sensex_color = "🟢" if global_sentiment['sensex_change'] > 0 else "🔴"
        st.metric(f"{sensex_color} Sensex 30", f"{global_sentiment['sensex_change']:+.2f}%")
    
    st.info(f"""
**Impact Analysis:** US {"Bullish 📈" if global_sentiment['sp500_change'] > 0 else "Bearish 📉"} → Nifty {"Strong ✅" if abs(global_sentiment['nifty_change']) > 1 else "Stable"} | Best for: {"LONGS 📈" if global_sentiment['nifty_change'] > 0 else "SHORTS 📉"}
    """)
else:
    st.warning("Global market data temporarily unavailable")

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
        forecast_engine = get_forecast_engine()
        
        try:
            mtf_data = get_multitimeframe_data(symbol)
            if mtf_data is None or '1h' not in mtf_data or 'daily' not in mtf_data:
                st.error(f"❌ Could not fetch data for {symbol}")
                st.stop()
            
            forecast = forecast_engine.generate_forecast(symbol, mtf_data['daily'])
            
            if forecast is None:
                st.error(f"❌ Could not generate forecast for {symbol}")
                st.stop()
            
            # Main Signal
            st.markdown(f"""
<div class='forecast-header'>
    <h2>📊 {symbol}</h2>
    <p>Current Price: <span style='color: #FFD700;'>₹{forecast.current_price:.2f}</span></p>
</div>
            """, unsafe_allow_html=True)
            
            rec_html = f"<p class='buy-signal'>✅ BUY</p>" if forecast.recommendation == "BUY" else \
                      f"<p class='sell-signal'>❌ SELL</p>" if forecast.recommendation == "SELL" else \
                      f"<p class='hold-signal'>⏸️ HOLD</p>"
            
            col_rec, col_conf, col_strength, col_rr = st.columns(4)
            
            with col_rec:
                st.markdown(rec_html, unsafe_allow_html=True)
                st.caption("Recommendation")
            
            with col_conf:
                conf_percent = int(forecast.forecast_confidence * 100)
                st.metric("Confidence", f"{conf_percent}%")
            
            with col_strength:
                strength_percent = int(forecast.forecast_strength * 100)
                st.metric("Signal Strength", f"{strength_percent}%")
            
            with col_rr:
                st.metric("Risk/Reward", f"{forecast.risk_reward_ratio:.2f}:1")
            
            st.divider()
            
            # Price Targets
            st.markdown("### 💰 Price Targets & Entry/Exit")
            
            targets_col1, targets_col2, targets_col3, targets_col4 = st.columns(4)
            
            with targets_col1:
                st.metric("📍 Entry", f"₹{forecast.current_price:.2f}")
            
            with targets_col2:
                t1_pct = ((forecast.target_price_1h - forecast.current_price) / forecast.current_price * 100)
                st.metric("🎯 1h Target", f"₹{forecast.target_price_1h:.2f}", f"{t1_pct:+.2f}%")
            
            with targets_col3:
                t2_pct = ((forecast.target_price_4h - forecast.current_price) / forecast.current_price * 100)
                st.metric("🎯 4h Target", f"₹{forecast.target_price_4h:.2f}", f"{t2_pct:+.2f}%")
            
            with targets_col4:
                t3_pct = ((forecast.target_price_1d - forecast.current_price) / forecast.current_price * 100)
                st.metric("🎯 1d Target", f"₹{forecast.target_price_1d:.2f}", f"{t3_pct:+.2f}%")
            
            # Risk Management
            st.markdown("### 🛑 Risk Management")
            
            risk_col1, risk_col2 = st.columns(2)
            
            with risk_col1:
                risk_amount = abs(forecast.current_price - forecast.stop_loss)
                st.metric("Stop Loss", f"₹{forecast.stop_loss:.2f}", f"Risk: ₹{risk_amount:.2f}")
            
            with risk_col2:
                st.metric("Portfolio Risk %", f"{forecast.portfolio_risk_percent:.1f}%")
            
            st.divider()
            
            # Component Breakdown
            st.markdown("### 🧠 AI Component Scores")
            
            components = [
                ("📰 News", forecast.news_sentiment),
                ("📊 Technical", forecast.technical_indicators),
                ("📈 Patterns", forecast.chart_patterns),
                ("🌪️ Regime", forecast.market_regime),
                ("📍 Price", forecast.price_action),
                ("📦 Volume", forecast.volume_analysis),
                ("🌍 Global", forecast.global_sentiment),
            ]
            
            comp_cols = st.columns(len(components))
            
            for idx, (comp_name, component) in enumerate(components):
                with comp_cols[idx]:
                    score_display = f"{component.score:+.2f}"
                    st.metric(comp_name, score_display, f"{int(component.confidence*100)}%")
            
            with st.expander("📋 Detailed Analysis", expanded=True):
                for comp_name, component in components:
                    st.write(f"**{comp_name}**")
                    st.write(f"Score: {component.score:+.2f} | Confidence: {int(component.confidence*100)}%")
                    st.write(f"{component.description}")
                    st.divider()
            
            st.divider()
            
            # News & Sentiment Analysis
            st.markdown("### 📰 News & Sentiment Analysis")
            
            try:
                news_result = analyze_news_sentiment(symbol)
                
                if news_result:
                    # Signal Metrics
                    sent_col1, sent_col2, sent_col3 = st.columns(3)
                    
                    with sent_col1:
                        signal_color = "🟢" if news_result['trading_signal'] == 'BUY' else \
                                      "🔴" if news_result['trading_signal'] == 'SELL' else "🟡"
                        st.metric("News Signal", f"{signal_color} {news_result['trading_signal'].upper()}")
                    
                    with sent_col2:
                        score = news_result['composite_score']
                        st.metric("Sentiment Score", f"{score:+.2f}", "(-1 to +1)")
                    
                    with sent_col3:
                        conf = news_result['confidence']
                        st.metric("Confidence", f"{conf:.0%}")
                    
                    # Component Breakdown
                    st.markdown("**Signal Breakdown (Company | Market | Economic):**")
                    
                    comp_col1, comp_col2, comp_col3 = st.columns(3)
                    
                    with comp_col1:
                        company_score = news_result['company_sentiment'].get('weighted_score', 0)
                        company_label = news_result['company_sentiment'].get('weighted_label', 'HOLD')
                        st.write(f"🏢 **Company:** {company_label}\n({company_score:+.2f})")
                    
                    with comp_col2:
                        market_score = news_result.get('market_sentiment', {}).get('weighted_score', 0)
                        market_label = news_result.get('market_sentiment', {}).get('weighted_label', 'HOLD')
                        st.write(f"📊 **Market:** {market_label}\n({market_score:+.2f})")
                    
                    with comp_col3:
                        econ_score = news_result.get('economic_sentiment', {}).get('weighted_score', 0)
                        econ_label = news_result.get('economic_sentiment', {}).get('weighted_label', 'HOLD')
                        st.write(f"🌍 **Economic:** {econ_label}\n({econ_score:+.2f})")
                    
                    st.divider()
            
            except Exception as e:
                st.warning(f"News sentiment analysis unavailable: {str(e)[:60]}")
            
            # Latest News Articles
            st.markdown("### 📋 Latest News & Articles")
            
            try:
                news_items = get_latest_news(symbol, max_articles=8)
                
                if news_items and len(news_items) > 0:
                    for i, article in enumerate(news_items[:5], 1):
                        title = article.get('title', 'No title')
                        desc = article.get('description', '')[:150]
                        url = article.get('url', '#')
                        
                        st.write(f"**{i}. {title}**")
                        st.caption(desc + "...")
                        if url != '#':
                            st.write(f"[Read more]({url})")
                        st.divider()
                else:
                    st.info("No recent news found")
            except Exception as e:
                st.warning(f"News unavailable: {str(e)[:50]}")
            
            st.divider()
            
            # Trading Timing
            st.markdown("### ⏱️ Trading Window")
            
            timing_col1, timing_col2 = st.columns(2)
            
            with timing_col1:
                st.info(f"""
**Best Entry:** {forecast.best_entry_time}

**Market Status:** {forecast.market_hours_valid and "🟢 OPEN" or "🔴 CLOSED"}

**Time Left:** {forecast.trading_window_hours:.1f} hours
                """)
            
            with timing_col2:
                if not forecast.market_hours_valid:
                    st.warning("⏰ Market Closed - Use for planning tomorrow's trades")
            
            st.divider()
            
            # Warnings
            if forecast.warnings or forecast.risk_factors:
                st.markdown("### ⚠️ Warnings & Risk Factors")
                
                if forecast.warnings:
                    for warning in forecast.warnings:
                        st.warning(warning)
                
                if forecast.risk_factors:
                    st.markdown("**Risk Factors:**")
                    for risk in forecast.risk_factors:
                        st.write(f"• {risk}")
            
            st.divider()
            
            # Rules
            st.markdown("""
### 💰 REAL MONEY TRADING RULES

**✅ RULES YOU **MUST** FOLLOW:**
1. **Entry:** Only enter at suggested price
2. **Stop Loss:** ALWAYS set before trade
3. **Risk:** Max 2% per trade
4. **Position Size:** (2% risk) / (Entry - SL)
5. **Hours:** 9:15 AM - 3:30 PM IST only

**❌ **NEVER** DO THESE:**
- Move stop loss after entry
- Average down on losers
- Trade without stop
- Over-trade (max 3/day)
- FOMO or revenge trading

**🎯 BEST PRACTICES:**
- Paper trade first
- Use limit orders (not market)
- Journal every trade
- Review daily/weekly

**⚠️ DISCLAIMER:** AI analysis only. Not financial advice. Trade at your own risk.
            """)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.write(traceback.format_exc())

else:
    st.info("👈 Select a stock symbol and click 'Generate Forecast' to begin")
