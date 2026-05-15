# enhanced_dashboard.py - Professional dashboard with multi-stock + scalping + entry/exit levels
# Focus: EXACT entry prices, entry/exit clarity, news sentiment, daily scalp opportunities

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta, time
import pytz
import logging

from ai_engine_integrator import AIEngineIntegrator, UnifiedSignal
from scalp_engine import ScalpEngine
from entry_exit_engine import EntryExitEngine, EntryExitLevels
from news_sentiment_ai import NewsSentimentAI
from config import WATCHLIST, DEFAULT_STOCK
from multi_timeframe_analyzer import MultiTimeframeAnalyzer

logger = logging.getLogger(__name__)

# Initialize news AI
news_ai = NewsSentimentAI()


def is_nse_open(now: datetime = None) -> bool:
    """Return True if NSE is open now (IST)."""
    tz = pytz.timezone("Asia/Kolkata")
    now = now or datetime.now(tz)
    # Weekday: 0=Mon .. 6=Sun
    if now.weekday() >= 5:
        return False
    open_time = time(9, 15)
    close_time = time(15, 30)
    return open_time <= now.time() <= close_time


def get_last_data_info(symbol: str, interval: str = "1h", period: str = "7d"):
    """Return (rows, last_timestamp) for a quick data check using yfinance."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df is None or len(df) == 0:
            return 0, None
        last_ts = df.index.max()
        return len(df), last_ts
    except Exception:
        return 0, None

# Page config
st.set_page_config(
    page_title="🤖 AI Trading System - Enhanced",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    /* Page background & dark card styles */
    .reportview-container .main {background-color: #0f1720; color: #e6eef8}
    .stApp { background-color: #0f1720; }
    .metric-card { background-color: #0b1220; padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.03); }
    .buy-signal { color: #00ff99; font-weight: 700; font-size: 1.3em; }
    .sell-signal { color: #ff7b7b; font-weight: 700; font-size: 1.3em; }
    .hold-signal { color: #9aa3b2; font-weight: 600; }
    .scalp-box { background: linear-gradient(135deg, rgba(102,126,234,0.9) 0%, rgba(118,75,162,0.9) 100%); padding: 1.5rem; border-radius: 0.6rem; color: white;  }
    .header-card { background: linear-gradient(90deg, rgba(8,145,178,0.08), rgba(134,65,244,0.06)); padding: 1rem; border-radius: 0.6rem; border: 1px solid rgba(255,255,255,0.02); }
    .small-muted { color: #9aa3b2; font-size: 0.9em; }
    /* Make dataframes dark */
    .stDataFrame table { background-color: #071022 }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

st.sidebar.title("⚙️ AI Trading System")

# Multi-stock selector
all_stocks = list(WATCHLIST) + [DEFAULT_STOCK]
selected_stock = st.sidebar.selectbox(
    "📊 Select Stock",
    all_stocks,
    index=0,
    help="Choose stock to analyze"
)

# Timeframe selector for scalping
scalp_tf = st.sidebar.radio(
    "⏱️ Scalping Timeframe",
    ["1m", "5m", "15m"],
    help="Intraday scalp detection timeframe"
)

# Run analysis
if st.sidebar.button("🔍 Analyze Now", use_container_width=True, type="primary"):
    st.session_state.run_analysis = True

# Initialize signal and data at module level
signal = None
df_1h = None
market_open = is_nse_open()
rows = 0
last_ts = None

# ═════════════════════════════════════════════════════════════════════════════
# MAIN: UNIFIED AI SIGNAL
# ═════════════════════════════════════════════════════════════════════════════

if "run_analysis" in st.session_state and st.session_state.run_analysis:
    
    with st.spinner(f"🔄 Analyzing {selected_stock}... (Fetching news + indicators)"):
        try:
            # Quick market status + last-data check
            rows, last_ts = get_last_data_info(selected_stock, interval="1h", period="7d")
            market_open = is_nse_open()

            # Show market status
            status_color = "#22c55e" if market_open else "#ff7b7b"
            last_ts_text = last_ts.strftime("%Y-%m-%d %H:%M:%S") if last_ts is not None else "No data"
            st.markdown(f"<div class='header-card'><b>Market (NSE):</b> <span style='color:{status_color}'>" + ("OPEN" if market_open else "CLOSED") + f"</span>  •  <b>Last 1h candle:</b> {last_ts_text}  •  <b>Rows (7d,1h):</b> {rows}</div>", unsafe_allow_html=True)

            # Choose analysis timeframe: prefer 1h when market open, otherwise use daily to avoid empty intraday frames
            tf_for_integrator = "1h" if market_open else "daily"
            signal = AIEngineIntegrator.generate_unified_signal(selected_stock, timeframe=tf_for_integrator)

            # Fetch data for entry/exit levels based on chosen timeframe
            try:
                if tf_for_integrator == "1h":
                    df_1h = yf.download(selected_stock, interval="1h", period="5d", progress=False)
                else:
                    # use daily candles when market closed
                    df_1h = yf.download(selected_stock, interval="1d", period="90d", progress=False)
            except Exception:
                df_1h = None
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            signal = None
            df_1h = None

# Display results (after spinner context exits)
if signal:
    # Header with recommendation
    st.title(f"📈 {selected_stock}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        recommendation_html = f"<p class='buy-signal'>BUY</p>" if signal.recommendation == "BUY" else \
                             f"<p class='sell-signal'>SELL</p>" if signal.recommendation == "SELL" else \
                             f"<p class='hold-signal'>HOLD</p>"
        st.markdown(recommendation_html, unsafe_allow_html=True)
        st.caption("Recommendation")
    
    with col2:
        st.metric("Current Price", f"₹{signal.current_price:.2f}", f"AI Score: {signal.confidence.signal_type}")
    
    with col3:
        st.metric("Target", f"₹{signal.target_price:.2f}", f"Risk/Reward: {signal.risk_reward:.1f}:1")
    
    with col4:
        st.metric("Stop Loss", f"₹{signal.stop_loss:.2f}", f"Confidence: {signal.confidence.overall_score:.0f}%")
    
    st.divider()
    
    # Entry/Exit Levels
    st.subheader("💰 TODAY'S ACTION LEVELS (For Scalping/Swing)")
    
    if df_1h is not None and len(df_1h) > 10:
        entry_levels = EntryExitEngine.generate_for_signal(
            df_1h,
            signal_direction="up" if signal.recommendation == "BUY" else "down"
        )
        
        if entry_levels:
            display_data = EntryExitEngine.format_for_display(entry_levels)
            
            # Main action instruction
            action_col = st.columns([2, 1, 1])[0]
            with action_col:
                st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 0.5rem; color: white;">
    <h2>{display_data['action']}</h2>
    <h3 style="color: #FFD700; margin-top: 0.5rem;">{display_data['entry_instruction']}</h3>
    <p style="font-size: 0.9rem; color: #aaa;">{display_data['entry_cancel']}</p>
</div>
                """, unsafe_allow_html=True)
            
            # Entry/Exit table
            action_data = {
                "Level": ["📍 Entry (Buy/Sell At)", "🎯 Target 1 (First Profit)", "🎯 Target 2 (Full Target)", "🛑 Stop Loss (Risk Limit)"],
                "Price": [
                    f"₹{entry_levels.buy_above if entry_levels.entry_action.startswith('BUY') else entry_levels.sell_below:.2f}",
                    f"₹{entry_levels.target1:.2f}",
                    f"₹{entry_levels.target2:.2f}",
                    f"₹{entry_levels.stoploss:.2f}"
                ],
                "Expected %": [
                    "—",
                    f"+{entry_levels.target1_pct:.2f}%" if entry_levels.entry_action.startswith('BUY') else f"-{entry_levels.target1_pct:.2f}%",
                    f"+{entry_levels.target2_pct:.2f}%" if entry_levels.entry_action.startswith('BUY') else f"-{entry_levels.target2_pct:.2f}%",
                    f"Risk"
                ],
                "R:R Ratio": ["—", f"1:{entry_levels.risk_reward_1:.2f}", f"1:{entry_levels.risk_reward_2:.2f}", "—"]
            }
            
            st.dataframe(pd.DataFrame(action_data), use_container_width=True, hide_index=True)
            setup_quality = "🟢 A+ SETUP" if entry_levels.strength > 0.8 else "🟡 GOOD SETUP" if entry_levels.strength > 0.6 else "⚪ MODERATE SETUP"
            st.info(f"**Setup Quality:** {setup_quality} | **ATR-based Risk:** ₹{entry_levels.risk_points:.2f}")
    
    st.divider()
    
    # Confidence breakdown
    st.subheader("🧠 AI Confidence Breakdown")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Price Action", f"{signal.confidence.price_action_score:.0f}%", delta=None)
    with col2:
        st.metric("Volume", f"{signal.confidence.volume_score:.0f}%", delta=None)
    with col3:
        st.metric("Technical", f"{signal.confidence.technical_score:.0f}%", delta=None)
    with col4:
        st.metric("Patterns", f"{signal.confidence.pattern_score:.0f}%", delta=None)
    with col5:
        st.metric("Sentiment", f"{signal.confidence.sentiment_score:.0f}%", delta=None)
    with col6:
        st.metric("Regime", f"{signal.confidence.regime_score:.0f}%", delta=None)
    
    st.success(f"✅ Analysis Complete - Generated at {signal.timestamp}")
        
else:
    # If integrator failed, still show last-known indicators and price so the user can see something useful
    st.markdown(f"<div class='metric-card'><h3 style='color:#ff7777;'>❌ Could not generate live AI signal for {selected_stock}.</h3><p class='small-muted'>Falling back to last-known indicators and price.</p></div>", unsafe_allow_html=True)

    # Try to display last-known indicators from df_1h (which may be daily candles when market closed)
    if df_1h is not None and len(df_1h) > 5:
        try:
            df_local = AIEngineIntegrator.enrich_dataframe(df_1h.copy())
            last_close = df_local['Close'].iloc[-1]
            ema20 = df_local['EMA_20'].iloc[-1]
            ema50 = df_local['EMA_50'].iloc[-1]
            rsi = df_local['RSI'].iloc[-1]
            atr = df_local['ATR'].iloc[-1]

            cola, colb, colc, cold = st.columns(4)
            with cola:
                st.metric('Last Price', f'₹{last_close:.2f}')
            with colb:
                st.metric('EMA20', f'₹{ema20:.2f}')
            with colc:
                st.metric('EMA50', f'₹{ema50:.2f}')
            with cold:
                st.metric('RSI', f'{rsi:.1f}')

            st.write(f"ATR: {atr:.3f} | Last update: {df_local.index.max()}")
        except Exception as _e:
            st.info('Unable to compute indicators from last-known data.')
    else:
        st.info('No sufficient historical data to compute indicators. Check symbol or internet connection.')

    with st.expander("Troubleshoot & Diagnostics"):
        st.write("Possible reasons:")
        st.markdown("- Wrong symbol format (use .NS for NSE stocks)\n- No internet or yfinance API limit\n- Intraday frames unavailable when market closed")
        try:
            sample = yf.download(selected_stock, period="30d", interval=("1h" if market_open else "1d"), progress=False)
            rows = 0 if sample is None else len(sample)
            st.write(f"Data check: rows fetched (30d,{ '1h' if market_open else '1d' }): **{rows}**")
            st.write(f"Last sample timestamp: {sample.index.max() if sample is not None and len(sample)>0 else 'N/A'}")
        except Exception:
            st.write("Data check: error fetching sample data (check internet)")

        if st.button("🔁 Retry Analysis"):
            st.session_state.run_analysis = True

# ═════════════════════════════════════════════════════════════════════════════
# QUICK MULTI-STOCK SCREENER
# ═════════════════════════════════════════════════════════════════════════════

st.divider()
st.subheader("📊 Quick Multi-Stock Screener")

if st.button("🔄 Scan All Stocks", use_container_width=True):
    progress_bar = st.progress(0)
    results = []
    
    for idx, stock in enumerate(WATCHLIST[:10]):  # Scan first 10 to save time
        signal = AIEngineIntegrator.generate_unified_signal(stock, timeframe="1h")
        
        if signal:
            results.append({
                "Stock": stock,
                "Price": f"₹{signal.current_price:.2f}",
                "Signal": signal.recommendation,
                "Confidence": f"{signal.confidence.overall_score:.0f}%",
                "Target": f"₹{signal.target_price:.2f}",
                "Stop": f"₹{signal.stop_loss:.2f}",
                "R:R": f"{signal.risk_reward:.1f}:1"
            })
        
        progress_bar.progress((idx + 1) / len(WATCHLIST[:10]))
    
    if results:
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
    else:
        st.warning("No results. Check your API connections.")

st.caption("🔒 Educational Trading System | Not Financial Advice | Risk Management Essential")
